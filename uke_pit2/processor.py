# -*- coding: utf-8 -*-
"""
  processor.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 2.04.2024, 15:33:28
  
  Purpose: processor class.
"""

import time

from typing import Optional, List
from threading import Event, Thread
from inspect import currentframe
from queue import Queue, Empty

from sqlalchemy.orm import Session

from jsktoolbox.attribtool import ReadOnlyClass
from jsktoolbox.logstool.logs import LoggerClient, LoggerQueue
from jsktoolbox.libs.base_th import ThBaseObject
from jsktoolbox.netaddresstool.ipv4 import Address, Network
from jsktoolbox.raisetool import Raise
from jsktoolbox.devices.network.connectors import API
from jsktoolbox.devices.mikrotik.routerboard import RouterBoard
from jsktoolbox.datetool import Timestamp


from uke_pit2.base import BLogs
from uke_pit2.db_models.spider import (
    TConnection,
    TCustomer,
    TInterface,
    TInterfaceName,
    TRouter,
)
from uke_pit2.db_models.update import TLastUpdate
from uke_pit2.network import Pinger
from uke_pit2.rb import IRouterBoardCollector, RBData, RouterBoardVersion
from uke_pit2.db import DbConfig, Database


class _Keys(object, metaclass=ReadOnlyClass):
    """Internal Keys container class."""

    ACH: str = "__api_connector_handler__"
    DATA: str = "__router_data__"
    DATABASE: str = "__database__"
    DB_DATA: str = "__db_database__"
    DB_HOST: str = "__db_host__"
    DB_PASS: str = "__db_password__"
    DB_PORT: str = "__db_port__"
    DB_USER: str = "__db_username__"
    IP: str = "__host_ip__"
    PASS: str = "__passwords_list__"
    QUEUE: str = "__comms_queue__"
    RUNTIME: str = "__runtime__"


class DbProcessor(Thread, ThBaseObject, BLogs):
    """Database Processor class for router board object."""

    def __init__(
        self,
        logger_queue: LoggerQueue,
        comms_queue: Queue,
        debug: bool = False,
    ) -> None:
        """Processor constructor.

        ### Arguments:
        - logger_queue [LoggerQueue] - logger queue for communication.
        - comms_queue [Queue] - communication queue.
        - debug [bool] - debug flag.
        """
        # init thread
        Thread.__init__(self, name=f"{self._c_name}")
        self._stop_event = Event()
        self.sleep_period = 0.2
        # debug
        self._debug = debug
        # logger
        self.logs = LoggerClient(logger_queue, f"{self._c_name}")
        # communication queue
        self.__comms_queue = comms_queue
        # set runtime
        self._set_data(_Keys.RUNTIME, set_default_type=int, value=Timestamp.now)

    def run(self) -> None:
        """Start processor."""
        if not self._stop_event:
            return None
        if not self.__comms_queue:
            self.logs.message_critical = f"Communication queue was not set properly."
            return None

        if not self.__check_config():
            self.logs.message_critical = (
                "Unable to continue due to lack of configuration."
            )
            return None

        # configuring database connection
        if not self.logs or not self.logs.logs_queue or self._debug is None:
            return None
        conf = DbConfig()
        conf.host = self.db_host  # type: ignore
        conf.port = self.db_port  # type: ignore
        conf.database = self.db_database  # type: ignore
        conf.user = self.db_username  # type: ignore
        conf.password = self.db_password  # type: ignore
        # self.logs.message_debug = f"{conf}"
        self.database = Database(self.logs.logs_queue, conf, self._debug)
        # create connection
        if not self.database.create_connection():
            self.logs.message_critical = "connection to database error."
            return None

        # create session
        session: Optional[Session] = self.database.session
        if not session:
            self.logs.message_debug = "database session error"
            return None

        if self._debug:
            self.logs.message_debug = "starting..."

        # set runtime
        tlu = TLastUpdate()
        tlu.last_update = self._get_data(_Keys.RUNTIME, default_value=Timestamp.now)  # type: ignore
        session.add(tlu)
        session.commit()

        # stats counters
        stat_routers: int = 0
        stat_connections: int = 0
        stat_customers: int = 0

        while True:
            if self.__comms_queue.empty() and self._stop_event.is_set():
                break
            try:
                item: RBData = self.__comms_queue.get(block=False)
                self.logs.message_info = f"Update router information: {item.router_id}"
                self.logs.message_info = f" connections count: {len(item.routers)}"
                self.logs.message_info = f" customers count: {len(item.customers)}"

                # stats
                stat_routers += 1
                stat_connections += len(item.routers)
                stat_customers += len(item.customers)

                # update router information
                rid: int = self.__update_routers(session, item)
                if item.customers:
                    self.__update_router_customers(session, item, rid)
                if item.routers:
                    self.__update_router_connections(session, item, rid)

            except Empty:
                time.sleep(0.2)
                continue
            except Exception as ex:
                self.logs.message_critical = (
                    f"exception was thrown while processing the queue: {ex}"
                )
                continue

        session.close()

        # finished
        self.logs.message_notice = "########################"
        self.logs.message_notice = "Database update finished"
        self.logs.message_notice = f"* Routers: {stat_routers}"
        self.logs.message_notice = f"* Connections: {stat_connections}"
        self.logs.message_notice = f"* Customers: {stat_customers}"
        self.logs.message_notice = "########################"

        if self._debug:
            self.logs.message_debug = "stopped."

    def stop(self) -> None:
        """Sets stop event."""
        if self._stop_event:
            if self._debug:
                self.logs.message_debug = "stopping..."
            self._stop_event.set()

    def __update_router_connections(
        self, session: Session, data: RBData, router_record_id: int
    ) -> None:
        """Update information about inter-router connections."""
        runtime: Optional[int] = self._get_data(_Keys.RUNTIME)
        if runtime and session and data and data.routers:
            for item in data.routers:
                inf = inf_name_id = cid = network = vid = None  # type: ignore
                if "interface" in item:
                    inf: str = item["interface"]
                if "network" in item:
                    network: Network = item["network"]
                if "vlan-id" in item:
                    vid: int = item["vlan-id"]
                else:
                    vid = 1

                # check interface name
                row = (
                    session.query(TInterfaceName)
                    .filter(TInterfaceName.name == inf)
                    .first()
                )
                if not row:
                    row = TInterfaceName()
                    row.name = inf
                    session.add(row)
                    session.commit()
                inf_name_id: int = row.id

                # check connection
                row = (
                    session.query(TConnection)
                    .filter(
                        TConnection.rid == router_record_id,
                        TConnection.vlan_id == vid,
                        TConnection.network == int(network.network),
                    )
                    .first()
                )
                if row:
                    row.last_update = runtime
                else:
                    row = TConnection()
                    row.network = int(network.network)
                    row.rid = router_record_id
                    row.vlan_id = vid
                    row.last_update = runtime
                    session.add(row)
                session.commit()
                cid: int = row.id

                # check interface
                row = (
                    session.query(TInterface)
                    .filter(TInterface.cid == cid, TInterface.if_id == inf_name_id)
                    .first()
                )
                if row:
                    row.last_update = runtime
                else:
                    row = TInterface()
                    row.cid = cid
                    row.if_id = inf_name_id
                    row.last_update = runtime
                    session.add(row)
                session.commit()

    def __update_router_customers(
        self, session: Session, data: RBData, router_record_id: int
    ) -> None:
        """Update router customers information."""
        runtime: Optional[int] = self._get_data(_Keys.RUNTIME)
        if runtime and session and data and data.customers:
            for item in data.customers:
                if "name" in item and "address" in item:
                    row: Optional[TCustomer] = (
                        session.query(TCustomer)
                        .filter(TCustomer.name == item["name"])
                        .first()
                    )
                    if row:
                        if row.rid != router_record_id:
                            row.rid = router_record_id
                        if row.ip != int(Address(item["address"])):
                            row.ip = int(Address(item["address"]))
                        row.last_update = runtime
                    else:
                        customer = TCustomer()
                        customer.rid = router_record_id
                        customer.name = item["name"]
                        customer.ip = int(Address(item["address"]))
                        customer.last_update = runtime
                        session.add(customer)
                    session.commit()

    def __update_routers(self, session: Session, data: RBData) -> int:
        """Check and update routers information in database.

        ### Arguments:
        - session - database session,
        - data - router board collected data object,

        ### Returns:
        id [int] - database record ID.
        """
        runtime: Optional[int] = self._get_data(_Keys.RUNTIME)
        if runtime and session and data and data.router_id:
            row: Optional[TRouter] = (
                session.query(TRouter)
                .filter(TRouter.router_id == int(data.router_id))
                .first()
            )
            if row:
                row.last_update = runtime
            else:
                row = TRouter()
                row.router_id = int(data.router_id)
                row.last_update = runtime
                session.add(row)

            session.commit()
        return row.id

    def __check_config(self) -> bool:
        """Check if the connection variables are set."""
        if (
            self.db_database
            and self.db_host
            and self.db_password
            and self.db_port
            and self.db_username
        ):
            return True
        return False

    @property
    def __comms_queue(self) -> Optional[Queue]:
        """Returns communication queue if set."""
        return self._get_data(key=_Keys.QUEUE, set_default_type=Optional[Queue])

    @__comms_queue.setter
    def __comms_queue(self, comms_queue: Optional[Queue]) -> None:
        """Sets communication queue."""
        self._set_data(key=_Keys.QUEUE, value=comms_queue)

    @property
    def db_host(self) -> Optional[Address]:
        return self._get_data(key=_Keys.DB_HOST, set_default_type=Optional[Address])

    @db_host.setter
    def db_host(self, value: Optional[Address]) -> None:
        self._set_data(key=_Keys.DB_HOST, value=value)

    @property
    def db_port(self) -> Optional[int]:
        return self._get_data(
            key=_Keys.DB_PORT, set_default_type=int, default_value=3306
        )

    @db_port.setter
    def db_port(self, value: Optional[int]) -> None:
        self._set_data(key=_Keys.DB_PORT, value=value)

    @property
    def db_database(self) -> Optional[str]:
        return self._get_data(key=_Keys.DB_DATA, set_default_type=Optional[str])

    @db_database.setter
    def db_database(self, value: Optional[str]) -> None:
        self._set_data(key=_Keys.DB_DATA, value=value)

    @property
    def db_username(self) -> Optional[str]:
        return self._get_data(key=_Keys.DB_USER, set_default_type=Optional[str])

    @db_username.setter
    def db_username(self, value: Optional[str]) -> None:
        self._set_data(key=_Keys.DB_USER, value=value)

    @property
    def db_password(self) -> Optional[str]:
        return self._get_data(key=_Keys.DB_PASS, set_default_type=Optional[str])

    @db_password.setter
    def db_password(self, value: Optional[str]) -> None:
        self._set_data(key=_Keys.DB_PASS, value=value)

    @property
    def database(self) -> Database:
        """Returns Database object."""
        return self._get_data(key=_Keys.DATABASE)  # type: ignore

    @database.setter
    def database(self, database: Database) -> None:
        """Sets Database object."""
        self._set_data(key=_Keys.DATABASE, set_default_type=Database, value=database)


class Processor(Thread, ThBaseObject, BLogs):
    """Processor class for router board object."""

    def __init__(
        self,
        logger_queue: LoggerQueue,
        ip: Address,
        passwords: List[str],
        debug: bool = False,
    ) -> None:
        """Processor constructor.

        ### Arguments:
        - logger_queue [LoggerQueue] - logger queue for communication.
        - ip [Address] - router ip address.
        - passwords [List[str]] - list of router passwords
        - debug [bool] - debug flag.
        """
        # init thread
        Thread.__init__(self, name=f"{self._c_name} [{ip}]")
        self._stop_event = Event()
        self.sleep_period = 0.2
        # set ip
        self.ip = ip
        # set passwords
        self.__passwords = passwords
        # debug
        self._debug = debug
        # logger
        self.logs = LoggerClient(logger_queue, f"{self._c_name} {ip}")
        # data container
        self._data[_Keys.DATA] = None

    def run(self) -> None:
        """Start processor."""
        if self._debug:
            self.logs.message_debug = "starting..."

        # the main procedure
        if not self.has_stop_set:
            # check icmp to ip
            self.__check_icmp()

        if not self.has_stop_set:
            # connector handler
            conn = None
            for passwd in self.__passwords:
                if self._debug:
                    self.logs.message_debug = f"Try to connect..."
                conn = API(
                    ip_address=self.ip,
                    port=8728,
                    login="admin",
                    password=passwd,
                    debug=True if self._debug else False,
                )
                try:
                    if conn.connect() and conn.is_alive:
                        if self._debug:
                            self.logs.message_debug = f"connected"
                            # self.logs.message_debug = f"The password is: '{passwd}'"
                        self.api_handler = conn
                        break
                except Exception as e:
                    self.logs.message_debug = f"{e}"
            if not self.api_handler or not self.api_handler.is_alive:
                if self._debug:
                    self.logs.message_debug = f"cannot connect"
                self.stop()

        if not self.has_stop_set:
            # router board dialogs
            self.__router_board_dialogs()

        if self._debug:
            self.logs.message_debug = "stopped"

    def stop(self) -> None:
        """Sets stop event."""
        if self._stop_event:
            if self._debug:
                self.logs.message_debug = "stopping..."
            self._stop_event.set()

    def __del__(self) -> None:
        """Destructor for class."""
        if self.api_handler and self.api_handler.is_alive:
            if self._debug:
                self.logs.message_debug = "closing connection"
            self.api_handler.disconnect()

    def __check_icmp(self) -> None:
        """Check ipv4 responses."""
        test = Pinger()
        if not test.is_alive(self.ip):
            if self._debug:
                self.logs.message_debug = f"host not responding."
            self.stop()

    def __router_board_dialogs(self) -> None:
        """RB procedures."""
        if self.api_handler and self.logs.logs_queue:
            rb = RouterBoard(
                connector=self.api_handler,
                qlog=self.logs.logs_queue,
                debug=True if self._debug else False,
            )

            # check system version
            csv = RouterBoardVersion(
                logger_queue=self.logs.logs_queue,
                rb_handler=rb,
                debug=True if self._debug else False,
            )

            collector: Optional[IRouterBoardCollector] = csv.get_collector()

            if collector:
                # self.logs.message_debug = f"{collector}"
                collector.collect()
                # self.logs.message_debug = f"{collector.get_data()}"
                self._data[_Keys.DATA] = collector.get_data()
                # collector.dump()  # type: ignore

            # tests
            # rbq = RBQuery()
            # rbq.add_attrib("current-firmware")
            # out: Optional[Element] = rb.element("/system/routerboard/", auto_load=True)
            # if out:
            #     self.logs.message_debug = f"{out.search(rbq.query)}"
            #     self.logs.message_debug = f"{out.attrib}"

            # rbq = RBQuery()
            # rbq.add_attrib("interface", "routerid")
            # rbq.add_attrib("network", str(self.ip))
            # out: Optional[Element] = rb.element("/ip/address/", auto_load=True)
            # if out:
            #     self.logs.message_debug = f"{out.search(rbq.query)}"

    def router_data(self) -> Optional[RBData]:
        """Returns collected Router Board data."""
        return self._data[_Keys.DATA]

    @property
    def api_handler(self) -> Optional[API]:
        """Returns API object."""
        return self._get_data(key=_Keys.ACH, set_default_type=Optional[API])

    @api_handler.setter
    def api_handler(self, api: API) -> None:
        """Sets API object."""
        self._set_data(key=_Keys.ACH, value=api)

    @property
    def ip(self) -> Address:
        """Returns IPv4 router board address."""
        return self._get_data(
            key=_Keys.IP, set_default_type=Address, default_value=Address("127.0.0.1")
        )  # type: ignore

    @ip.setter
    def ip(self, value: Address) -> None:
        """Sets IPv4 router board address."""
        self._set_data(key=_Keys.IP, value=value)

    @property
    def __passwords(self) -> List[str]:
        """Returns list of the router passwords."""
        if _Keys.PASS not in self._data:
            self._data[_Keys.PASS] = []
        return self._data[_Keys.PASS]

    @__passwords.setter
    def __passwords(self, value: List[str]) -> None:
        """Sets list of the router passwords."""
        if not isinstance(value, list):
            raise Raise.error(
                f"Expected list[str] type, received: '{type(value)}'",
                TypeError,
                self._c_name,
                currentframe(),
            )
        self.__passwords.extend(value)

    @property
    def has_stop_set(self) -> bool:
        """Returns stop flag."""
        if self._stop_event:
            return self._stop_event.is_set()
        return False


# #[EOF]#######################################################################

# -*- coding: utf-8 -*-
"""
  processor.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 2.04.2024, 15:33:28
  
  Purpose: processor class.
"""


from typing import Optional, List
from threading import Event, Thread
from inspect import currentframe
from queue import Queue

from jsktoolbox.attribtool import ReadOnlyClass
from jsktoolbox.logstool.logs import LoggerClient, LoggerQueue
from jsktoolbox.libs.base_data import BData
from jsktoolbox.libs.base_th import ThBaseObject
from jsktoolbox.libs.base_logs import BLoggerQueue
from jsktoolbox.netaddresstool.ipv4 import Address
from jsktoolbox.raisetool import Raise
from jsktoolbox.devices.network.connectors import API
from jsktoolbox.devices.mikrotik.routerboard import RouterBoard
from jsktoolbox.devices.mikrotik.elements.libs.search import RBQuery
from jsktoolbox.devices.mikrotik.base import Element

from uke_pit2.base import BLogs
from uke_pit2.network import Pinger
from uke_pit2.rb import IRouterBoardCollector, RBData, RouterBoardVersion


class _Keys(object, metaclass=ReadOnlyClass):
    """Internal Keys container class."""

    ACH: str = "__api_connector_handler__"
    DATA: str = "__router_data__"
    DB_DATA: str = "__db_database__"
    DB_HOST: str = "__db_host__"
    DB_PASS: str = "__db_password__"
    DB_PORT: str = "__db_port__"
    DB_USER: str = "__db_username__"
    IP: str = "__host_ip__"
    PASS: str = "__passwords_list__"


class DbProcessor(Thread, ThBaseObject, BLogs):
    """Database Processor class for router board object."""

    def __init__(
        self,
        logger_queue: LoggerQueue,
        comms_queue: Queue,
        debug: bool = False,
    ) -> None:
        """Processor constructor.

        # Arguments:
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

    def run(self) -> None:
        """Start processor."""

    def stop(self) -> None:
        """Sets stop event."""
        if self._stop_event:
            if self._debug:
                self.logs.message_debug = "stopping..."
            self._stop_event.set()

    @property
    def db_host(self) -> Optional[Address]:
        if _Keys.DB_HOST not in self._data:
            self._data[_Keys.DB_HOST] = None
        return self._data[_Keys.DB_HOST]

    @db_host.setter
    def db_host(self, value: Optional[Address]) -> None:
        if value is not None and not isinstance(value, Address):
            raise Raise.error(
                f"Address type expected, received: '{type(value)}'.",
                TypeError,
                self._c_name,
                currentframe(),
            )
        self._data[_Keys.DB_HOST] = value

    @property
    def db_port(self) -> Optional[int]:
        if _Keys.DB_PORT not in self._data:
            self._data[_Keys.DB_PORT] = None
        return self._data[_Keys.DB_PORT]

    @db_port.setter
    def db_port(self, value: Optional[int]) -> None:
        if value is not None and not isinstance(value, int):
            raise Raise.error(
                f"int type expected, received: '{type(value)}'.",
                TypeError,
                self._c_name,
                currentframe(),
            )
        self._data[_Keys.DB_PORT] = value

    @property
    def db_database(self) -> Optional[str]:
        if _Keys.DB_DATA not in self._data:
            self._data[_Keys.DB_DATA] = None
        return self._data[_Keys.DB_DATA]

    @db_database.setter
    def db_database(self, value: Optional[str]) -> None:
        if value is not None and not isinstance(value, str):
            raise Raise.error(
                f"str type expected, received: '{type(value)}'.",
                TypeError,
                self._c_name,
                currentframe(),
            )
        self._data[_Keys.DB_DATA] = value

    @property
    def db_username(self) -> Optional[str]:
        if _Keys.DB_USER not in self._data:
            self._data[_Keys.DB_USER] = None
        return self._data[_Keys.DB_USER]

    @db_username.setter
    def db_username(self, value: Optional[str]) -> None:
        if value is not None and not isinstance(value, str):
            raise Raise.error(
                f"str type expected, received: '{type(value)}'.",
                TypeError,
                self._c_name,
                currentframe(),
            )
        self._data[_Keys.DB_USER] = value

    @property
    def db_password(self) -> Optional[str]:
        if _Keys.DB_PASS not in self._data:
            self._data[_Keys.DB_PASS] = None
        return self._data[_Keys.DB_PASS]

    @db_password.setter
    def db_password(self, value: Optional[str]) -> None:
        if value is not None and not isinstance(value, str):
            raise Raise.error(
                f"str type expected, received: '{type(value)}'.",
                TypeError,
                self._c_name,
                currentframe(),
            )
        self._data[_Keys.DB_PASS] = value


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

        # Arguments:
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
                            self.logs.message_debug = f"The password is: '{passwd}'"
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
                self.logs.message_debug = f"{collector}"
                collector.collect()
                self.logs.message_debug = f"{collector.get_data()}"
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
        if _Keys.ACH not in self._data:
            self._data[_Keys.ACH] = None
        return self._data[_Keys.ACH]

    @api_handler.setter
    def api_handler(self, api: API) -> None:
        """Sets API object."""
        if not isinstance(api, API):
            raise Raise.error(
                f"Expected API type, received: '{type(api)}'",
                TypeError,
                self._c_name,
                currentframe(),
            )
        self._data[_Keys.ACH] = api

    @property
    def ip(self) -> Address:
        """Returns IPv4 router board address."""
        if _Keys.IP not in self._data:
            self._data[_Keys.IP] = Address("127.0.0.1")
        return self._data[_Keys.IP]

    @ip.setter
    def ip(self, value: Address) -> None:
        """Sets IPv4 router board address."""
        if not isinstance(value, Address):
            raise Raise.error(
                f"Address type expected, type: '{type(value)}' received.",
                TypeError,
                self._c_name,
                currentframe(),
            )
        self._data[_Keys.IP] = value

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

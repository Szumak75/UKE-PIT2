# -*- coding: utf-8 -*-
"""
  db.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 15.04.2024, 13:22:36
  
  Purpose: Classes for lms database connection
"""
from typing import Dict, Any, Optional

from sqlalchemy import Subquery, create_engine, and_, or_, text, func
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine.base import Engine
from sqlalchemy.engine import URL, engine_from_config
from sqlalchemy.util import immutabledict

from jsktoolbox.attribtool import ReadOnlyClass
from jsktoolbox.netaddresstool.ipv4 import Address
from jsktoolbox.logstool.logs import LoggerQueue, LoggerClient, BData
from jsktoolbox.datetool import Timestamp

from uke_pit2.base import BDebug, BLogs, LmsBase
from uke_pit2.db_models import TLastUpdate


class DbConfigKeys(object, metaclass=ReadOnlyClass):
    """Keys container class for config dict."""

    DATABASE: str = "__db_database__"
    HOST: str = "__db_host__"
    PASS: str = "__db_password__"
    PORT: str = "__db_port__"
    USER: str = "__db_username__"


class _Keys(object, metaclass=ReadOnlyClass):
    """Internal Keys class."""

    CONF: str = "__config__"
    DB_POLL: str = "__pool__"


class DbConfig(BData):
    """Database configuration dict."""

    def __init__(self) -> None:
        """DbConfig constructor."""
        self.host = Address("127.0.0.1")
        self.database = ""
        self.port = 3306
        self.user = ""
        self.password = ""

    def __repr__(self) -> str:
        return f"{self._c_name}(host: {self.host}, port: {self.port}, database: {self.database}, user: {self.user})"

    @property
    def host(self) -> Address:
        """Returns database IP Address."""
        return self._get_data(DbConfigKeys.HOST, set_default_type=Address, default_value=Address("127.0.0.1"))  # type: ignore

    @host.setter
    def host(self, value: Address) -> None:
        self._set_data(DbConfigKeys.HOST, value=value)

    @property
    def port(self) -> int:
        """Returns database PORT."""
        return self._get_data(DbConfigKeys.PORT, set_default_type=int, default_value=3306)  # type: ignore

    @port.setter
    def port(self, port: int) -> None:
        self._set_data(DbConfigKeys.PORT, value=port)

    @property
    def database(self) -> str:
        """Returns DATABASE."""
        return self._get_data(DbConfigKeys.DATABASE, set_default_type=str, default_value="")  # type: ignore

    @database.setter
    def database(self, value: str) -> None:
        self._set_data(DbConfigKeys.DATABASE, value=value)

    @property
    def user(self) -> str:
        """Returns database USER."""
        return self._get_data(DbConfigKeys.USER, set_default_type=str, default_value="")  # type: ignore

    @user.setter
    def user(self, value: str) -> None:
        self._set_data(DbConfigKeys.USER, value=value)

    @property
    def password(self) -> str:
        """Returns database PASS."""
        return self._get_data(DbConfigKeys.PASS, set_default_type=str, default_value="")  # type: ignore

    @password.setter
    def password(self, value: str) -> None:
        self._set_data(DbConfigKeys.PASS, value=value)


class Database(BDebug, BLogs):
    """LMS Database class."""

    def __init__(
        self,
        logger_queue: LoggerQueue,
        config_obj: DbConfig,
        debug: bool = False,
    ) -> None:
        """Database constructor.

        ### Arguments:
        - logger_queue [LoggerQueue] - logger queue for logs subsystem communication.
        - config_obj [DbConfig] - config options for database communication.
        - debug [bool] - debugging flag, default: False.
        """
        self._set_data(_Keys.CONF, set_default_type=DbConfig, value=config_obj)
        self.logs = LoggerClient(logger_queue, self._c_name)
        self.debug = debug
        self._set_data(_Keys.DB_POLL, set_default_type=Optional[Engine], value=None)

        # self.logs.message_debug = f"from args: {config_obj}"
        # self.logs.message_debug = f"from data: {self._get_data(_Keys.CONF)}"

    def create_connection(self) -> bool:
        """Prepare database engine."""
        # Engine
        engine: Engine = create_engine(
            url=self.url,
            connect_args={},
            pool_recycle=3600,
            poolclass=QueuePool,
        )
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                if connection is not None:
                    LmsBase.metadata.create_all(engine)
                if self.debug:
                    self.logs.message_debug = f"add connection to server: {self._get_data(_Keys.CONF).host} with backend: pymysql"  # type: ignore
                    self._set_data(_Keys.DB_POLL, value=engine)
        except Exception as ex:
            self.logs.message_critical = f"connection to server: {self._get_data(_Keys.CONF).host} with backend: pymyslq error: {ex}"  # type: ignore
        if self._get_data(_Keys.DB_POLL) is not None:
            return True
        return False

    @property
    def url(self) -> URL:
        """Create URL object."""
        conf: DbConfig = self._get_data(_Keys.CONF)  # type: ignore
        return URL.create(
            "mysql+pymysql",
            username=conf.user,
            password=conf.password,
            host=str(conf.host),
            database=conf.database,
            port=conf.port,
            query=immutabledict({"charset": "utf8mb4"}),
        )

    @property
    def session(self) -> Optional[Session]:
        """Returns db session."""
        session = None
        try:
            session = Session(self._get_data(_Keys.DB_POLL))
            out = session.query(text("SELECT 1"))
            self.logs.message_info = f"check query: {out}"
        except:
            session = None

        return session


# #[EOF]#######################################################################

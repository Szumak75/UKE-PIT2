# -*- coding: utf-8 -*-
"""
  models.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 23.08.2024, 12:54:16
  
  Purpose: reports model classes.
"""

from typing import Optional, List, Tuple, Any
from threading import Event, Thread
from inspect import currentframe
from queue import Queue, Empty

from sqlalchemy import ForeignKey, Integer, Boolean, String, func, text, and_
from sqlalchemy.orm import Mapped, mapped_column, Query, relationship, aliased
from sqlalchemy.orm import Session
from sqlalchemy.dialects.mysql import (
    BIGINT,
    BINARY,
    BIT,
    BLOB,
    BOOLEAN,
    CHAR,
    DATE,
    DATETIME,
    DECIMAL,
    DOUBLE,
    ENUM,
    FLOAT,
    INTEGER,
    LONGBLOB,
    LONGTEXT,
    MEDIUMBLOB,
    MEDIUMINT,
    MEDIUMTEXT,
    NCHAR,
    NUMERIC,
    NVARCHAR,
    REAL,
    SET,
    SMALLINT,
    TEXT,
    TIME,
    TIMESTAMP,
    TINYBLOB,
    TINYINT,
    TINYTEXT,
    VARBINARY,
    VARCHAR,
    YEAR,
)

from jsktoolbox.attribtool import ReadOnlyClass
from jsktoolbox.logstool.logs import (
    LoggerClient,
    LoggerQueue,
)

from jsktoolbox.libs.base_th import ThBaseObject
from jsktoolbox.netaddresstool.ipv4 import Address, Network
from jsktoolbox.raisetool import Raise
from jsktoolbox.datetool import DateTime
from jsktoolbox.datetool import Timestamp
from jsktoolbox.stringtool.crypto import SimpleCrypto

from uke_pit2.base import BReportObject

from uke_pit2.db_models.spider import (
    TConnection,
    TCustomer,
    TInterface,
    TInterfaceName,
    TNodeAssignment,
    TRouter,
    TFlow,
    TDivisions,
    TForeign,
    TMedium,
)
from uke_pit2.db_models.update import TLastUpdate

# from web_service.models import LmsCustomer, LmsDivision, LmsNetNode, LmsUser


class RDivision(BReportObject):
    """Report object class."""

    class Keys(object, metaclass=ReadOnlyClass):
        """Internal keys class."""

        DIVISION: str = "__div__"

    def __init__(
        self,
        session: Session,
        logger_queue: LoggerQueue,
        division: TDivisions,
        verbose: bool,
        debug: bool,
    ) -> None:
        """Constructor."""

        self.logs = LoggerClient(logger_queue, self._c_name)
        self.debug = debug
        self.verbose = verbose
        self.session = session
        self._set_data(
            key=RDivision.Keys.DIVISION, value=division, set_default_type=TDivisions
        )

        self.logs.message_notice = f"Created Division: {self.division.ident}"

    def __repr__(self) -> str:
        """Returns string representation."""
        return f"{self._c_name}({self.division})"

    @property
    def division(self) -> TDivisions:
        return self._get_data(
            key=RDivision.Keys.DIVISION,
        )  # type: ignore


# #[EOF]#######################################################################

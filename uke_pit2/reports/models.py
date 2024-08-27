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

from sqlalchemy import ForeignKey, Integer, Boolean, String, func, text, and_, true
from sqlalchemy.orm import Mapped, mapped_column, Query, relationship, aliased
from sqlalchemy.orm import Session

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

from uke_pit2.db_models.reports import LmsDivision, Division


class RDivision(BReportObject):
    """Report object class."""

    class Keys(object, metaclass=ReadOnlyClass):
        """Internal keys class."""

        DIVISION: str = "__div__"
        IDENT: str = "__ident__"

    def __init__(
        self,
        session: Session,
        logger_queue: LoggerQueue,
        division: LmsDivision,
        verbose: bool,
        debug: bool,
    ) -> None:
        """Constructor."""

        self.logs = LoggerClient(logger_queue, self._c_name)
        self.debug = debug
        self.verbose = verbose
        self.session = session
        self._set_data(
            key=RDivision.Keys.DIVISION, value=division, set_default_type=LmsDivision
        )
        # update ident
        self.__update_ident()

        self.logs.message_notice = f"Created Division: {self.shortname}"

    def __repr__(self) -> str:
        """Returns string representation."""
        return f"{self._c_name}({self.division})"

    def __update_ident(self) -> None:
        """Update IDENT if self.main is False."""
        if not self.main:
            out = self.session.query(Division).filter(Division.main == True).first()
            if out:
                self._set_data(
                    key=RDivision.Keys.IDENT, value=out.ident, set_default_type=str
                )
            else:
                raise Raise.error(
                    "Could not find IDENT for main division, please check if database dataset configuration is correct.",
                    ValueError,
                    self._c_name,
                    currentframe(),
                )

    @property
    def foreign_ident(self) -> str:
        """Returns foreign ident string."""
        return self._get_data(
            key=RDivision.Keys.IDENT, set_default_type=str, default_value=""
        )  # type: ignore

    @property
    def division(self) -> LmsDivision:
        return self._get_data(
            key=RDivision.Keys.DIVISION,
        )  # type: ignore

    @property
    def main(self) -> bool:
        """Returns True if division is the main division."""
        if not self.division:
            return False
        return self.division.map.main

    @property
    def shortname(self) -> str:
        """Returns division name."""
        if not self.division:
            return "ERROR"
        return (
            self.division.shortname.upper()
            .replace(" ", "")
            .replace(".", "")
            .replace("SPZOO", "")
            .replace("AIR-NET", "AIR-NET-")
            .strip("-")
        )


# #[EOF]#######################################################################

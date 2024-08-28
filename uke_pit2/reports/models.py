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

from uke_pit2.db_models.reports import LmsDivision, Division, LmsNetNode, Foreign


class RNode(BReportObject):
    """Node report class."""

    class Keys(object, metaclass=ReadOnlyClass):
        """Internal keys class."""

        IDENT: str = "__ident__"
        MAIN: str = "__main__"
        NODE: str = "__node__"

    def __init__(
        self,
        session: Session,
        logger_queue: LoggerQueue,
        node: LmsNetNode,
        main: bool,
        foreign_ident: str,
        verbose: bool,
        debug: bool,
    ) -> None:
        """Constructor."""

        self.logs = LoggerClient(logger_queue, self._c_name)
        self.debug = debug
        self.verbose = verbose
        self.session = session

        # set node
        self._set_data(key=RNode.Keys.NODE, set_default_type=LmsNetNode, value=node)

        # set main
        self._set_data(key=RNode.Keys.MAIN, set_default_type=bool, value=main)

        # set ident
        self._set_data(key=RNode.Keys.IDENT, set_default_type=str, value=foreign_ident)

    @property
    def foreign_ident(self) -> str:
        """Returns foreign ident string."""
        return self._get_data(
            key=RNode.Keys.IDENT, set_default_type=str, default_value=""
        )  # type: ignore

    @property
    def main(self) -> bool:
        """Returns True if division is the main division."""
        return self._get_data(key=RNode.Keys.MAIN)  # type: ignore


class RDivision(BReportObject):
    """Report object class."""

    class Keys(object, metaclass=ReadOnlyClass):
        """Internal keys class."""

        DIVISION: str = "__div__"
        IDENT: str = "__ident__"
        NODES: str = "__nodes__"
        FOREIGN: str = "__foreign__"
        TEN: str = "__ten__"

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

        # update nodes list
        self.__get_nodes()

        # update foreign
        self.__update_foreign()

        self.logs.message_notice = (
            f"Created Division: {self.shortname}, FOREIGN: {self.foreign}"
        )


    def __repr__(self) -> str:
        """Returns string representation."""
        return f"{self._c_name}({self.division})"

    def generate_foreign(self) -> List[str]:
        """Foreign report generator."""
        head: str = "po01_id_podmiotu_obcego," "po02_nip_pl," "po03_nip_nie_pl"
        out: List[str] = []
        out.append(head)
        for item in self._get_data(key=RDivision.Keys.FOREIGN):  # type: ignore
            out.append(f"{item[0]},{item[1]},{item[2]}")
        return out

    def __update_foreign(self) -> None:
        """Update foreign list."""
        out: List[List[str]] = []
        if self.main:
            rows = self.session.query(Foreign).all()
            for item in rows:
                out.append([item.ident, item.tin.replace("-", ""), ""])
        else:
            out.append([self.foreign_ident, self.ten, ""])

        self._set_data(key=RDivision.Keys.FOREIGN, value=out, set_default_type=List)

    def __update_ident(self) -> None:
        """Update IDENT if self.main is False."""
        if not self.main:
            out = (
                self.session.query(Division, LmsDivision)
                .join(LmsDivision, Division.did == LmsDivision.id)
                .filter(Division.main == True)
                .first()
            )
            if out:
                self._set_data(
                    key=RDivision.Keys.IDENT, value=out[0].ident, set_default_type=str
                )
                self._set_data(
                    key=RDivision.Keys.TEN,
                    value=out[1].ten.replace("-", ""),
                    set_default_type=str,
                )
            else:
                raise Raise.error(
                    "Could not find IDENT for main division, please check if database dataset configuration is correct.",
                    ValueError,
                    self._c_name,
                    currentframe(),
                )

    def __get_nodes(self) -> None:
        """Get nodes records from lms."""
        out: List[RNode] = []

        if self.logs and self.logs.logs_queue:

            rows = self.session.query(LmsNetNode).all()
            for item in rows:
                out.append(
                    RNode(
                        self.session,
                        self.logs.logs_queue,
                        item,
                        self.main,
                        self.foreign_ident,
                        self.verbose,
                        self.debug,
                    )
                )
            self._set_data(key=RDivision.Keys.NODES, set_default_type=List, value=out)
        else:
            raise Raise.error(
                "Logs subsystem initialization error.",
                RuntimeError,
                self._c_name,
                currentframe(),
            )

    @property
    def foreign(self) -> List[List[str]]:
        """Returns foreign list."""
        return self._get_data(key=RDivision.Keys.FOREIGN)  # type: ignore

    @property
    def foreign_ident(self) -> str:
        """Returns foreign ident string."""
        return self._get_data(
            key=RDivision.Keys.IDENT, set_default_type=str, default_value=""
        )  # type: ignore

    @property
    def ten(self) -> str:
        """Returns ten number from lms."""
        return self._get_data(
            key=RDivision.Keys.TEN, set_default_type=str, default_value=""
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

    @property
    def nodes(self) -> List[RNode]:
        """Returns RNode list."""
        return self._get_data(key=RDivision.Keys.NODES, default_value=[])  # type: ignore


# #[EOF]#######################################################################

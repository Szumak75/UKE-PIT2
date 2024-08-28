# -*- coding: utf-8 -*-
"""
  generators.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 23.08.2024, 12:41:22
  
  Purpose: Report generators classes.
"""

import os

from typing import Optional, List, Tuple, Any
from threading import Event, Thread
from inspect import currentframe
from queue import Queue, Empty

from sqlalchemy.orm import Session

from jsktoolbox.attribtool import ReadOnlyClass
from jsktoolbox.logstool.logs import (
    LoggerClient,
    LoggerQueue,
)

from jsktoolbox.libs.base_th import ThBaseObject
from jsktoolbox.netaddresstool.ipv4 import Address, Network
from jsktoolbox.raisetool import Raise
from jsktoolbox.datetool import Timestamp
from jsktoolbox.stringtool.crypto import SimpleCrypto

from uke_pit2.base import BReportGenerator
from uke_pit2.conf import Config
from uke_pit2.db import DbConfig, Database

from uke_pit2.db_models.reports import LmsDivision
from uke_pit2.reports.models import RDivision


class ThReportGenerator(Thread, ThBaseObject, BReportGenerator):
    """Report Generator class."""

    class Keys(object, metaclass=ReadOnlyClass):
        """Internal keys class."""

        DIR: str = "__output_dir__"

    def __init__(
        self, logger_queue: LoggerQueue, config: Config, report_dir: str
    ) -> None:
        """Constructor."""
        # init thread
        Thread.__init__(self, name=f"{self._c_name}")
        self._stop_event = Event()
        self.sleep_period = 0.2
        # config
        self.conf = config
        # report dir
        self._set_data(
            key=ThReportGenerator.Keys.DIR, value=report_dir, set_default_type=str
        )
        # logger
        self.logs = LoggerClient(logger_queue, f"{self._c_name}")
        self.logs.message_debug = f"initializing complete"

    def run(self) -> None:
        """Start procedure."""
        self.logs.message_debug = "starting..."
        t_start = Timestamp.now
        # ---- #
        # create database connection
        self.debug = True
        self.verbose = True
        session = self.__db_connection()
        if session:
            # get data
            out_div_list = self.__create_dataset(session)
            # generate reports
            for div in out_div_list:
                # generate foreign entities
                file_path = os.path.join(self._get_data(key=ThReportGenerator.Keys.DIR), f"{div.shortname}-foreign.csv")  # type: ignore
                self.__writer(file_path=file_path, data=div.generate_foreign())
                # generate buildings and collocations -
                file_path = os.path.join(self._get_data(key=ThReportGenerator.Keys.DIR), f"{div.shortname}-collocations.csv")  # type: ignore
                # generate base stations -
                file_path = os.path.join(self._get_data(key=ThReportGenerator.Keys.DIR), f"{div.shortname}-base-stations.csv")  # type: ignore
                # generate nodes
                file_path = os.path.join(self._get_data(key=ThReportGenerator.Keys.DIR), f"{div.shortname}-nodes.csv")  # type: ignore
                # generate pe
                file_path = os.path.join(self._get_data(key=ThReportGenerator.Keys.DIR), f"{div.shortname}-points.csv")  # type: ignore
                # generate cable lines
                file_path = os.path.join(self._get_data(key=ThReportGenerator.Keys.DIR), f"{div.shortname}-cables.csv")  # type: ignore
                # generate wireless lines
                file_path = os.path.join(self._get_data(key=ThReportGenerator.Keys.DIR), f"{div.shortname}-wireless.csv")  # type: ignore
                # generate ranges -
                file_path = os.path.join(self._get_data(key=ThReportGenerator.Keys.DIR), f"{div.shortname}-ranges.csv")  # type: ignore
                # generate services
                file_path = os.path.join(self._get_data(key=ThReportGenerator.Keys.DIR), f"{div.shortname}-services.csv")  # type: ignore
                # generate sidusis
                file_path = os.path.join(self._get_data(key=ThReportGenerator.Keys.DIR), f"{div.shortname}-sidusis.csv")  # type: ignore

            self.logs.message_info = f"{out_div_list}"
            # end connection
            session.close()
        # ---- #
        t_end = Timestamp.now
        self.logs.message_debug = f"end after: {t_end-t_start} [s]."

    def __writer(self, file_path: str, data: List[str]) -> None:
        """Reports writer."""
        with open(file_path, "w") as writer:
            for line in data:
                writer.write(f"{line}\n")
            writer.flush()

    def __create_dataset(self, session: Session) -> List[RDivision]:
        """Create list of records."""
        out = []
        if self.logs and self.logs.logs_queue:
            rows = session.query(LmsDivision).all()
            for item in rows:
                out.append(
                    RDivision(
                        session=session,
                        logger_queue=self.logs.logs_queue,
                        division=item,
                        verbose=True,
                        debug=True,
                    )
                )
        return out

    def __db_connection(self) -> Optional[Session]:
        """Create db connection and return session object."""
        if self.__check_db_config():
            conf = DbConfig()
            conf.database = self.conf.module_conf.lms_database  # type: ignore
            conf.host = self.conf.module_conf.lms_host  # type: ignore
            conf.password = SimpleCrypto.multiple_decrypt(self.conf.module_conf.salt, self.conf.module_conf.lms_password)  # type: ignore
            conf.port = self.conf.module_conf.lms_port  # type: ignore
            conf.user = self.conf.module_conf.lms_user  # type: ignore
            # self.logs.message_debug = f"{conf}, pass: {conf.password}"
            database = Database(self.logs.logs_queue, conf, self.debug, self.verbose)  # type: ignore

            # create connection
            if not database.create_connection():
                self.logs.message_critical = "connection to database error."
                return None

            # create session
            session: Optional[Session] = database.session
            if not session:
                self.logs.message_debug = "database session error"
                return None
            return session
        else:
            return None

    def __check_db_config(self) -> bool:
        """Check if the connection variables are set."""
        if (
            self.conf
            and self.conf.module_conf
            and self.conf.module_conf.salt
            and self.conf.module_conf.lms_database
            and self.conf.module_conf.lms_host
            and self.conf.module_conf.lms_password
            and self.conf.module_conf.lms_database
            and self.conf.module_conf.lms_user
        ):
            return True
        return False


# #[EOF]#######################################################################

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  nodes-uips.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 27.09.2024, 13:27:24
  
  Purpose: 
"""

from queue import Queue
import os, sys, time, signal

from inspect import currentframe
from typing import Optional, List

from sqlalchemy.orm import Session
from uke_pit2.db import DbConfig, Database

from jsktoolbox.attribtool import ReadOnlyClass
from jsktoolbox.raisetool import Raise
from jsktoolbox.systemtool import CommandLineParser, PathChecker
from jsktoolbox.netaddresstool.ipv4 import Address
from jsktoolbox.logstool.logs import (
    LoggerEngine,
    LoggerClient,
    LoggerEngineStdout,
    LoggerEngineFile,
    LoggerQueue,
    LogsLevelKeys,
    ThLoggerProcessor,
)
from jsktoolbox.logstool.formatters import LogFormatterNull, LogFormatterDateTime
from jsktoolbox.systemtool import Env
from jsktoolbox.stringtool.crypto import SimpleCrypto

import uke_pit2
from uke_pit2.base import BVerbose, BaseApp, BModuleConfig, BDebug
from uke_pit2.conf import Config
from uke_pit2.processor import DbProcessor, Processor
from uke_pit2.rb import RBData

from uke_pit2.reports.generators import ThReportGenerator
from uke_pit2.db_models.reports import LmsNetNode


class _Keys(object, metaclass=ReadOnlyClass):
    """Internal _Keys container class."""

    CONF_DIR: str = "output_dir"
    OUTPUT_DIR: str = "__output_dir__"
    PASSWORDS: str = "router_passwords"
    SET_DB_PASS: str = "__set_db_pass__"
    SET_IP: str = "__set_ip__"
    SET_PASS: str = "__set_pass__"
    START_IP: str = "start_ip"
    TEST_RANGE: str = "__test_routers_range__"
    TEST_START_IP: str = "__test_start_ip__"
    VERBOSE: str = "__verbose__"


class _ModuleConf(BModuleConfig):
    """Module config private class."""

    @property
    def start_ip(self) -> Optional[Address]:
        """Returns starting IP address for procedure."""
        var: Optional[str] = self._get(_Keys.START_IP)
        if not var:
            return None
        return Address(var)

    @property
    def router_passwords(self) -> List[str]:
        """Returns list of the router passwords."""
        var: List[str] = self._get(_Keys.PASSWORDS)
        if not var or isinstance(var, List) and len(var) == 1 and len(f"{var[0]}") == 0:
            return []
        return var

    @property
    def output_dir(self) -> Optional[str]:
        """Returns output dir string for reports."""
        var: Optional[str] = self._get(_Keys.CONF_DIR)
        if not var:
            return None
        return var


class NodeApp(BaseApp, BVerbose, BDebug):
    """UKE PIT generator main class."""

    def __init__(self) -> None:
        """UKE generator constructor."""

        # set config section name
        self.section = self._c_name

        # logging subsystem
        log_engine = LoggerEngine()
        log_queue: Optional[LoggerQueue] = log_engine.logs_queue
        if not log_queue:
            log_queue = LoggerQueue()
            log_engine.logs_queue = log_queue

        # logger levels
        self.__init_log_levels(log_engine)

        # logger client
        self.logs = LoggerClient()

        # logger processor
        thl = ThLoggerProcessor()
        thl.sleep_period = 0.2
        thl.logger_engine = log_engine
        thl.logger_client = self.logs
        self.logs_processor = thl

        # add config handler
        if self.conf is None:
            self.conf = Config(logger_queue=log_queue, app_name="uke-pit2")

        # set configuration filename
        self.conf.config_file = os.path.join(
            Env().home, f".{self.conf.section}", "config"
        )

        # config file
        if not self.conf.load():
            self.logs.message_critical = "cannot load config file"
            # TODO: print logs
            sys.exit(1)

        # update debug
        self.logs_processor._debug = self.conf.debug

        # signal handling
        signal.signal(signal.SIGTERM, self.__sig_exit)
        signal.signal(signal.SIGINT, self.__sig_exit)

        # check command line
        self.__init_command_line()

        # init section config
        self.__check_config_section()

        # check single run options

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

    def __db_connection(self) -> Optional[Session]:
        """Create db connection and return session object."""
        if self.__check_db_config():
            conf = DbConfig()
            conf.database = self.conf.module_conf.lms_database  # type: ignore
            conf.host = self.conf.module_conf.lms_host  # type: ignore
            conf.password = SimpleCrypto.multiple_decrypt(self.conf.module_conf.salt, self.conf.module_conf.lms_password)  # type: ignore
            conf.port = self.conf.module_conf.lms_port  # type: ignore
            conf.user = self.conf.module_conf.lms_user  # type: ignore
            self.logs.message_debug = f"{conf}, pass: {conf.password}"
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

    def run(self) -> None:
        """Start application."""
        if not self.conf:
            return None

        # logger processor
        self.logs_processor.start()

        # data

        # TESTS
        if self.tests:
            pass

        # main procedure
        if (
            self.configured
            and self.logs.logs_queue
            and self.logs_processor
            and self.logs_processor.logger_engine
            and self.logs_processor.logger_engine.logs_queue
            and self.module_conf.output_dir
            and self.conf.module_conf
            and not self.stop
        ):
            # start
            self.logs.message_info = "starting procedure"

            if self.stop:
                # TERM or INT signal was set
                pass
            else:
                session: Optional[Session] = self.__db_connection()
                if session:
                    header: str = (
                        "name,"
                        "address,"
                        "note,"
                        "contactName,"
                        "phone,"
                        "email,"
                        "latitude,"
                        "longitude,"
                        "elevation,"
                        "height,"
                        "macAddresses,"
                        "ipAddresses"
                    )
                    template = (
                        "{name},"
                        ","
                        ","
                        ","
                        ","
                        ","
                        "{latitude},"
                        "{longitude},"
                        ","
                        "165,"
                        ","
                        ""
                    )
                    if self.module_conf.output_dir:
                        file_path: str = os.path.join(
                            self.module_conf.output_dir,
                            "import-uisp-nodes.csv",
                        )
                        data: List[str] = []
                        data.append(header)

                        rows: List[LmsNetNode] = (
                            session.query(LmsNetNode).order_by(LmsNetNode.id).all()
                        )

                        for item in rows:
                            self.logs.message_info = f"{item}"
                            data.append(
                                template.format(
                                    name=item.name,
                                    latitude=item.latitude,
                                    longitude=item.longitude,
                                )
                            )

                        with open(file_path, "w") as writer:
                            for line in data:
                                writer.write(f"{line}\n")
                            writer.flush()

                    self.logs.message_debug = f"dir: {self.module_conf.output_dir}"

            # end
            self.logs.message_info = "procedure is complete"

        # exit
        time.sleep(1)

        # logger processor
        self.logs_processor.stop()
        while not self.logs_processor.is_stopped:
            self.logs_processor.join()
            time.sleep(0.1)

        sys.exit(0)

    def __sig_exit(self, signum: int, frame) -> None:
        """Received TERM|INT signal."""
        if self.conf and self.conf.debug:
            self.logs.message_debug = "TERM or INT signal received."
        self.stop = True

    def __check_config_section(self) -> None:
        """Check config option for section."""
        if not self.conf or not self.conf.cfh or not self.section:
            raise Raise.error(
                "Configuration initialization error.",
                RuntimeError,
                self._c_name,
                currentframe(),
            )

        if self.conf.cfh.has_section(self.section):
            self.logs.message_debug = f"Found section: [{self.section}]"
        else:
            self.logs.message_debug = f"Section: [{self.section}] not found..."
            self.logs.message_debug = "...creating a default module configuration"
            # create section
            self.conf.cfh.set(self.section, desc="The generator configuration section")
            dir = os.path.join(
                Env().home,
                "Reports",
                f"{self.conf.app_name}/" if self.conf and self.conf.app_name else "",
            )
            if dir[-1] != "/":
                dir = f"{dir}/"
            self.conf.cfh.set(
                self.section,
                varname=_Keys.CONF_DIR,
                value=dir,
                desc="[str] output directory path for reports.",
            )
            if not self.conf.save():
                raise Raise.error(
                    "Configuration file writing error.",
                    OSError,
                    self._c_name,
                    currentframe(),
                )
            self.conf.reload()

        # check command line updates
        if self._get_data(key=_Keys.OUTPUT_DIR, default_value=None):
            self.conf.cfh.set(
                section=self.section,
                varname=_Keys.CONF_DIR,
                value=self._get_data(key=_Keys.OUTPUT_DIR),
            )
            if not self.conf.save():
                raise Raise.error(
                    "Configuration file writing error.",
                    OSError,
                    self._c_name,
                    currentframe(),
                )
            self.conf.reload()

        # set module conf
        self.module_conf = _ModuleConf(self.conf.cfh, self.section)

        # check configuration
        configured: bool = True
        if not self.module_conf.output_dir:
            self.logs.message_alert = f"'{_Keys.CONF_DIR}' is not set."
            configured = False
        else:
            dir = self.module_conf.output_dir
            if dir:
                if len(dir) < 3:
                    configured = False
                    self.logs.message_critical = f"'{_Keys.CONF_DIR}' is too short."
                elif dir[0] != "/":
                    configured = False
                    self.logs.message_critical = (
                        f"'{_Keys.CONF_DIR}' must be an absolute path."
                    )
                elif dir[-1] != "/":
                    dir = f"{dir}/"
                    self.conf.cfh.set(
                        self.section,
                        varname=_Keys.CONF_DIR,
                        value=dir,
                        desc="[str] output directory path for reports.",
                    )
                    if not self.conf.save():
                        raise Raise.error(
                            "Configuration file writing error.",
                            OSError,
                            self._c_name,
                            currentframe(),
                        )
                    self.conf.reload()
        if configured:
            if self.module_conf.output_dir:
                # check directory
                pc = PathChecker(self.module_conf.output_dir)
                # self.logs.message_info = f"{pc}"
                if not pc.exists:
                    if not pc.create():
                        configured = False
                        self.logs.message_critical = f"Cannot create '{_Keys.CONF_DIR}': '{self.module_conf.output_dir}'"
                elif pc.is_file:
                    configured = False
                    self.logs.message_critical = f"'{_Keys.CONF_DIR}' is a file."
            else:
                configured = False

        self.configured = configured

        if not configured:
            self.logs.message_critical = (
                f"module [{self.section}] is not configured properly."
            )
            self.logs.message_critical = "use command line options"

    def __init_command_line(self) -> None:
        """Initialize command line."""
        parser = CommandLineParser()

        # configuration for arguments
        parser.configure_argument("h", "help", "this information.")
        parser.configure_argument(
            "o",
            "output_dir",
            "modify output dir for reports.",
            has_value=True,
            example_value="/tmp/Reports",
        )
        parser.configure_argument("T", "test", "for developer tests.")
        parser.configure_argument("v", "verbose", "verbose flag for debugging.")

        # command line parsing
        parser.parse_arguments()

        # check
        if parser.get_option("help") is not None:
            self._help(parser.dump())
        if parser.get_option("verbose") is not None:
            # set verbose flag
            self.verbose = True
        if parser.get_option("test") is not None:
            # set test flag
            self.tests = True
        if parser.get_option("output_dir") is not None:
            # set new output dir for reports
            out: Optional[str] = parser.get_option("output_dir")
            if out:
                if len(out) < 3:
                    self.logs.message_critical = f"'output_dir': '{out}' is too short."
                    self.stop = True
                elif out[0] != "/":
                    self.logs.message_critical = (
                        f"'output_dir' must be an absolute path."
                    )
                    self.stop = True
                else:
                    if out[-1] != "/":
                        out = f"{out}/"
                    dir = PathChecker(out)
                    # self.logs.message_notice = f"{dir}"
                    if dir.exists and dir.is_file:
                        self.logs.message_critical = (
                            f"'output_dir' exists and is a file."
                        )
                        self.stop = True
                    elif not dir.exists or dir.is_dir:
                        if dir.dirname and self.conf and self.conf.app_name:
                            self._set_data(
                                key=_Keys.OUTPUT_DIR,
                                value=os.path.join(
                                    dir.dirname, f"{self.conf.app_name}/"
                                ),
                                set_default_type=str,
                            )
                            self.logs.message_debug = f"'output_dir' is set to: {self._get_data(key=_Keys.OUTPUT_DIR)}"

            else:
                self.logs.message_critical = f"'output_dir' is required."
                self.stop = True

    def __init_log_levels(self, engine: LoggerEngine) -> None:
        """Set logging levels configuration for LoggerEngine."""
        # ALERT
        engine.add_engine(
            LogsLevelKeys.ALERT,
            LoggerEngineStdout(
                name=f"{self._c_name}->ALERT",
                # formatter=LogFormatterDateTime(),
                formatter=LogFormatterNull(),
            ),
        )
        # DEBUG
        engine.add_engine(
            LogsLevelKeys.DEBUG,
            LoggerEngineStdout(
                name=f"{self._c_name}->DEBUG",
                # formatter=LogFormatterDateTime(),
                formatter=LogFormatterNull(),
            ),
        )
        # ERROR
        engine.add_engine(
            LogsLevelKeys.ERROR,
            LoggerEngineStdout(
                name=f"{self._c_name}->ERROR",
                # formatter=LogFormatterDateTime(),
                formatter=LogFormatterNull(),
            ),
        )
        # NOTICE
        engine.add_engine(
            LogsLevelKeys.NOTICE,
            LoggerEngineStdout(
                name=f"{self._c_name}->NOTICE",
                # formatter=LogFormatterDateTime(),
                formatter=LogFormatterNull(),
            ),
        )
        # CRITICAL
        engine.add_engine(
            LogsLevelKeys.CRITICAL,
            LoggerEngineStdout(
                name=f"{self._c_name}->CRITICAL",
                # formatter=LogFormatterDateTime(),
                formatter=LogFormatterNull(),
            ),
        )
        # EMERGENCY
        engine.add_engine(
            LogsLevelKeys.EMERGENCY,
            LoggerEngineStdout(
                name=f"{self._c_name}->EMERGENCY",
                # formatter=LogFormatterDateTime(),
                formatter=LogFormatterNull(),
            ),
        )
        # INFO
        engine.add_engine(
            LogsLevelKeys.INFO,
            LoggerEngineStdout(
                name=self._c_name,
                # formatter=LogFormatterDateTime(),
                formatter=LogFormatterNull(),
            ),
        )
        # WARNING
        engine.add_engine(
            LogsLevelKeys.WARNING,
            LoggerEngineStdout(
                name=f"{self._c_name}->WARNING",
                # formatter=LogFormatterDateTime(),
                formatter=LogFormatterNull(),
            ),
        )

    @property
    def module_conf(self) -> _ModuleConf:
        """Return module conf object."""
        return self._get_data(key=_ModuleConf.Keys.MODCONF, set_default_type=_ModuleConf)  # type: ignore

    @module_conf.setter
    def module_conf(self, value: _ModuleConf) -> None:
        """Sets ModuleConf object."""
        self._set_data(key=_ModuleConf.Keys.MODCONF, value=value)


# #[EOF]#######################################################################

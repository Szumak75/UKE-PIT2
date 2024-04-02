# -*- coding: utf-8 -*-
"""
  main.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 27.03.2024, 13:08:55
  
  Purpose: Project main classes.
"""

import os, sys, time

from inspect import currentframe
from typing import Optional, List

from jsktoolbox.attribtool import ReadOnlyClass
from jsktoolbox.raisetool import Raise
from jsktoolbox.libs.system import CommandLineParser
from jsktoolbox.netaddresstool.ipv4 import Address
from jsktoolbox.logstool.logs import (
    LoggerEngine,
    LoggerClient,
    LoggerEngineStdout,
    LoggerQueue,
    LogsLevelKeys,
    ThLoggerProcessor,
)
from jsktoolbox.logstool.formatters import LogFormatterNull
from jsktoolbox.libs.system import Env, PathChecker
from jsktoolbox.stringtool.crypto import SimpleCrypto

from uke_pit2.base import BaseApp, BModuleConfig
from uke_pit2.conf import Config


class _Keys(object, metaclass=ReadOnlyClass):
    """Internal _Keys container class."""

    CONFIGURED: str = "__conf_ok__"
    PASSWORDS: str = "router_passwords"
    SET_DB_PASS: str = "__set_db_pass__"
    SET_IP: str = "__set_ip__"
    SET_PASS: str = "__set_pass__"
    START_IP: str = "start_ip"


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


class SpiderApp(BaseApp):
    """Spider main class."""

    def __init__(self) -> None:
        """SpiderAdd constructor."""

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

        # check command line
        self.__init_command_line()

        # add config handler
        if self.conf is None:
            self.conf = Config(logger_queue=log_queue, app_name="uke-pit2")

        # set configuration filename
        self.conf.config_file = os.path.join(
            Env.home, f".{self.conf.section}", "config"
        )

        # config file
        if not self.conf.load():
            self.logs.message_critical = "cannot load config file"
            # TODO: print logs
            sys.exit(1)

        # update debug
        self.logs_processor._debug = self.conf.debug

        # init section config
        self.__check_config_section()

        # check single run options

        self.run()

    def run(self) -> None:
        """Start application."""
        if not self.conf:
            return None

        # logger processor
        self.logs_processor.start()

        # main procedure
        if self.configured:
            time.sleep(5)

        # exit
        time.sleep(1)

        # logger processor
        self.logs_processor.stop()
        while not self.logs_processor.is_stopped:
            self.logs_processor.join()
            time.sleep(0.1)

        sys.exit(0)

    def __init_command_line(self) -> None:
        """Initialize command line."""
        parser = CommandLineParser()

        # configuration for arguments
        parser.configure_argument("h", "help", "this information.")
        parser.configure_argument(
            "i",
            "ip",
            "add/modify starting router ip4.",
            has_value=True,
            example_value="192.168.1.1",
        )
        parser.configure_argument(
            "R", "rbpassword", "add router password to connection list."
        )
        parser.configure_argument(
            "p", "dbpassword", "set user password for lms database connection."
        )

        # command line parsing
        parser.parse_arguments()

        # check
        if parser.get_option("help") is not None:
            self._help(parser.dump())
        if parser.get_option("ip") is not None:
            try:
                ip_str = parser.get_option("ip")
                if ip_str:
                    tmp = Address(ip_str)
                    self._data[_Keys.SET_IP] = tmp
            except Exception as ex:
                self.logs.message_critical = (
                    f"[command line] IPv4 address expected, received: '{ip_str}'"
                )
        if parser.get_option("rbpassword") is not None:
            # get password string from console
            while True:
                password: str = input("Enter router password: ")
                if password == "":
                    print('Type: "Exit" to break.')
                elif password == "EXIT":
                    break
                else:
                    self._data[_Keys.SET_PASS] = password
                    break
        if parser.get_option("dbpassword") is not None:
            # get password string from console
            while True:
                password: str = input("Enter database password: ")
                if password == "":
                    print('Type: "Exit" to break.')
                elif password == "EXIT":
                    break
                else:
                    self._data[_Keys.SET_DB_PASS] = password
                    break

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
            self.conf.cfh.set(self.section, desc="The spider configuration section")
            self.conf.cfh.set(
                self.section,
                varname=_Keys.START_IP,
                value="",
                desc="[str] IP address of the originating router.",
            )
            self.conf.cfh.set(
                self.section,
                varname=_Keys.PASSWORDS,
                value=[],
                desc="[List] list of passwords for routers",
            )
            if not self.conf.save():
                raise Raise.error(
                    "Configuration file writing error.",
                    OSError,
                    self._c_name,
                    currentframe(),
                )

        # check command line updates
        if _Keys.SET_IP in self._data:
            self.conf.cfh.set(
                section=self.section,
                varname=_Keys.START_IP,
                value=str(self._data[_Keys.SET_IP]),
            )
            if not self.conf.save():
                raise Raise.error(
                    "Configuration file writing error.",
                    OSError,
                    self._c_name,
                    currentframe(),
                )
            self.conf.reload()
        if _Keys.SET_DB_PASS in self._data:
            password: str = self._data[_Keys.SET_DB_PASS]
            mod: bool = False
            if self.conf.module_conf:
                salt: int = self.conf.module_conf.salt
                password = SimpleCrypto.multiple_encrypt(salt, password)
                if (
                    not self.conf.module_conf.lms_password
                    or self.conf.module_conf.lms_password
                    and self.conf.module_conf.lms_password != password
                ):
                    self.conf.set_lms_password(password)

        if _Keys.SET_PASS in self._data:
            password: str = self._data[_Keys.SET_PASS]
            mod: bool = False
            if self.conf.module_conf:
                salt: int = self.conf.module_conf.salt
                password = SimpleCrypto.multiple_encrypt(salt, password)
                pass_list: List[str] = self.conf.cfh.get(
                    section=self.section, varname=_Keys.PASSWORDS
                )
                if pass_list is None or isinstance(pass_list, str):
                    pass_list = [""]

                if len(pass_list) == 1:
                    if pass_list[0] == "":
                        pass_list[0] = password
                        self.conf.cfh.set(
                            section=self.section,
                            varname=_Keys.PASSWORDS,
                            value=pass_list,
                        )
                        mod = True

                test = False
                for item in pass_list:
                    if item == password:
                        test = True
                        break
                if not test:
                    pass_list.insert(0, password)
                    self.conf.cfh.set(
                        section=self.section,
                        varname=_Keys.PASSWORDS,
                        value=pass_list,
                    )
                    mod = True
            if mod:
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
        if not self.module_conf.start_ip:
            self.logs.message_alert = f"'{_Keys.START_IP}' is not set."
            configured = False
        if not self.module_conf.router_passwords:
            self.logs.message_alert = f"'{_Keys.PASSWORDS}' is not set."
            configured = False

        self.configured = configured

        if not configured:
            self.logs.message_critical = (
                f"module [{self.section}] is not configured properly."
            )
            self.logs.message_critical = "use command line options"

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
        if _ModuleConf.Keys.MODCONF not in self._data:
            return None  # type: ignore
        return self._data[_ModuleConf.Keys.MODCONF]

    @module_conf.setter
    def module_conf(self, value: _ModuleConf) -> None:
        """Sets ModuleConf object."""
        if not isinstance(value, _ModuleConf):
            raise Raise.error(
                f"_ModuleConf type expected, '{type(value)} received.'",
                TypeError,
                self._c_name,
                currentframe(),
            )
        self._data[_ModuleConf.Keys.MODCONF] = value

    @property
    def configured(self) -> bool:
        """Returns configured flag."""
        if _Keys.CONFIGURED not in self._data:
            self._data[_Keys.CONFIGURED] = False
        return self._data[_Keys.CONFIGURED]

    @configured.setter
    def configured(self, flag: bool) -> None:
        """Sets configured flag."""
        self._data[_Keys.CONFIGURED] = flag


class UkeApp(BaseApp):
    """UKE PIT generator main class."""

    def __init__(self) -> None:
        """UKE generator constructor."""

        # check command line
        self.__init_command_line()

    def __init_command_line(self) -> None:
        """Initialize command line."""
        parser = CommandLineParser()

        # configuration for arguments
        parser.configure_argument("h", "help", "this information")

        # command line parsing
        parser.parse_arguments()

        # check
        if parser.get_option("help") is not None:
            self._help(parser.dump())

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


# #[EOF]#######################################################################

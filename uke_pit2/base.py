# -*- coding: utf-8 -*-
"""
  base.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 27.03.2024, 13:17:19
  
  Purpose: Project base classes.
"""

import sys

from typing import List, Dict, Optional, Any
from inspect import currentframe

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Session

import uke_pit2

from jsktoolbox.libs.base_data import BData
from jsktoolbox.attribtool import ReadOnlyClass
from jsktoolbox.configtool.main import Config as ConfigTool
from jsktoolbox.logstool.logs import LoggerClient, ThLoggerProcessor
from jsktoolbox.devices.mikrotik.routerboard import RouterBoard
from jsktoolbox.raisetool import Raise


class _Keys(object, metaclass=ReadOnlyClass):
    """Internal _Keys container class."""

    COMMAND_LINE_OPTS: str = "__clo__"
    CONF: str = "__config__"
    CONFIGURED: str = "__conf_ok__"
    CONFIG_FILE: str = "__config_file__"
    CONFIG_HANDLER: str = "__cfh__"
    DEBUG: str = "__debug__"
    LOGGER_CLIENT: str = "__logger_client__"
    PROC_LOGS: str = "__logger_processor__"
    RB: str = "__rbh__"
    SECTION: str = "__config_section__"
    SET_STOP: str = "__set_stop__"
    SET_TEST: str = "__set_test__"
    VERBOSE: str = "__verbose__"


class BConfigSection(BData):
    """Base class for Config Section."""

    @property
    def section(self) -> Optional[str]:
        """Return section name."""
        return self._get_data(key=_Keys.SECTION, set_default_type=Optional[str])

    @section.setter
    def section(self, section_name: Optional[str]) -> None:
        """Set section name."""
        self._set_data(key=_Keys.SECTION, value=str(section_name).lower())


class BConfigHandler(BData):
    """Base class for Config handler."""

    @property
    def cfh(self) -> Optional[ConfigTool]:
        """Returns config handler object."""
        return self._get_data(
            key=_Keys.CONFIG_HANDLER, set_default_type=Optional[ConfigTool]
        )

    @cfh.setter
    def cfh(self, config_handler: Optional[ConfigTool]) -> None:
        """Sets config handler."""
        self._set_data(key=_Keys.CONFIG_HANDLER, value=config_handler)

    @property
    def config_file(self) -> Optional[str]:
        """Return config_file path string."""
        return self._get_data(key=_Keys.CONFIG_FILE, set_default_type=Optional[str])

    @config_file.setter
    def config_file(self, value: str) -> None:
        """Set config_file path string."""
        self._set_data(key=_Keys.CONFIG_FILE, value=value)


class BModuleConfig(BConfigHandler, BConfigSection):
    """Base class for module config classes."""

    class Keys(object, metaclass=ReadOnlyClass):
        """Keys definition container class."""

        MODCONF: str = "__modconf__"

    def __init__(self, cfh: ConfigTool, section: Optional[str]) -> None:
        """Constructor."""
        self.cfh = cfh
        self.section = section

    def _get(self, varname: str) -> Any:
        """Get variable from config."""
        if self.cfh and self.section:
            return self.cfh.get(self.section, varname)
        return None


class BDebug(BData):
    """Base class for debugging property."""

    @property
    def debug(self) -> bool:
        """Returns debug flag."""
        return self._get_data(
            key=_Keys.DEBUG, set_default_type=bool, default_value=False
        )  # type: ignore

    @debug.setter
    def debug(self, flag: bool) -> None:
        """Sets debug flag."""
        self._set_data(key=_Keys.DEBUG, value=flag)


class BVerbose(BData):
    """Base class for verbose debugging property."""

    @property
    def verbose(self) -> bool:
        """Returns debug flag."""
        return self._get_data(
            key=_Keys.VERBOSE, set_default_type=bool, default_value=False
        )  # type: ignore

    @verbose.setter
    def verbose(self, flag: bool) -> None:
        """Sets debug flag."""
        self._set_data(key=_Keys.VERBOSE, set_default_type=bool, value=flag)


class BLogs(BData):
    """Base class for LoggerClient property."""

    @property
    def logs(self) -> LoggerClient:
        """Returns LoggerClient object."""
        return self._get_data(
            key=_Keys.LOGGER_CLIENT,
            set_default_type=LoggerClient,
            default_value=LoggerClient(),
        )  # type: ignore

    @logs.setter
    def logs(self, logger_client: LoggerClient) -> None:
        """Sets LoggerClient."""
        self._set_data(key=_Keys.LOGGER_CLIENT, value=logger_client)


class BRouterBoard(BData):
    """Base class for router board property."""

    @property
    def rb(self) -> Optional[RouterBoard]:
        """Returns RouterBoard handler."""
        return self._get_data(key=_Keys.RB, set_default_type=Optional[RouterBoard])

    @rb.setter
    def rb(self, value: RouterBoard) -> None:
        """Sets Router Board handler."""
        self._set_data(key=_Keys.RB, value=value)


class BStop(BData):
    """Base class for stop method."""

    @property
    def stop(self) -> bool:
        """Returns STOP flag."""
        return self._get_data(
            key=_Keys.SET_STOP, set_default_type=bool, default_value=False
        )  # type: ignore

    @stop.setter
    def stop(self, flag: bool) -> None:
        """Sets STOP flag."""
        self._set_data(key=_Keys.SET_STOP, value=flag)


class BTest(BData):
    """Base class for test method."""

    @property
    def tests(self) -> bool:
        """Returns tests flag."""
        return self._get_data(
            key=_Keys.SET_TEST, set_default_type=bool, default_value=False
        )  # type: ignore

    @tests.setter
    def tests(self, flag: bool) -> None:
        """Sets tests flag."""
        self._set_data(key=_Keys.SET_TEST, set_default_type=bool, value=flag)


class BConfig(BData):
    """Base class for Config."""

    from uke_pit2.conf import Config

    @property
    def conf(self) -> Optional[Config]:
        """Return Config class object."""
        from uke_pit2.conf import Config

        return self._get_data(key=_Keys.CONF, set_default_type=Optional[Config])

    @conf.setter
    def conf(self, conf_obj: Config) -> None:
        """Set Config class object."""

        from uke_pit2.conf import Config

        self._set_data(key=_Keys.CONF, value=conf_obj)


class BReportGenerator(BLogs, BConfig, BStop, BTest, BVerbose, BDebug):
    """Base class for reports generator class."""


class BReportObject(BLogs, BVerbose, BDebug):
    """Base class for Report object."""

    class Keys(object, metaclass=ReadOnlyClass):
        """Internal keys class."""

        SESSION: str = "__session__"

    @property
    def session(self) -> Session:
        """Returns db session."""
        return self._get_data(
            key=BReportObject.Keys.SESSION, set_default_type=Session
        )  # type: ignore

    @session.setter
    def session(self, session: Session) -> None:
        if not session:
            raise Raise.error(
                "Session type expected, NoneType received.",
                TypeError,
                self._c_name,
                currentframe(),
            )
        self._set_data(
            key=BReportObject.Keys.SESSION, value=session, set_default_type=Session
        )


class BaseApp(BLogs, BConfig, BConfigSection, BStop, BTest):
    """Main app base class."""

    @property
    def configured(self) -> bool:
        """Returns configured flag."""
        return self._get_data(key=_Keys.CONFIGURED, set_default_type=bool, default_value=False)  # type: ignore

    @configured.setter
    def configured(self, flag: bool) -> None:
        """Sets configured flag."""
        self._set_data(key=_Keys.CONFIGURED, value=flag)

    @property
    def version(self) -> str:
        """Returns version information string."""
        return uke_pit2.VERSION

    @property
    def command_opts(self) -> bool:
        """Returns commands line flag"""
        return self._get_data(
            key=_Keys.COMMAND_LINE_OPTS, set_default_type=bool, default_value=False
        )  # type: ignore

    @command_opts.setter
    def command_opts(self, flag: bool) -> None:
        """Sets commands line flag."""
        self._set_data(key=_Keys.COMMAND_LINE_OPTS, value=flag)

    @property
    def logs_processor(self) -> ThLoggerProcessor:
        """Return logs_processor."""
        return self._get_data(
            key=_Keys.PROC_LOGS, set_default_type=ThLoggerProcessor
        )  # type: ignore

    @logs_processor.setter
    def logs_processor(self, value: ThLoggerProcessor) -> None:
        """Set logs_processor."""
        self._set_data(key=_Keys.PROC_LOGS, value=value)

    def _help(self, command_conf: Dict) -> None:
        """Show help information and shutdown."""
        command_opts: str = ""
        desc_opts: List = []
        max_len: int = 0
        opt_value: List = []
        opt_no_value: List = []
        # stage 1
        for item in command_conf.keys():
            if max_len < len(item):
                max_len = len(item)
            if command_conf[item]["has_value"]:
                opt_value.append(item)
            else:
                opt_no_value.append(item)
        max_len += 7
        # stage 2
        for item in sorted(opt_no_value):
            tmp: str = ""
            if command_conf[item]["short"]:
                tmp = f"-{command_conf[item]['short']}|--{item} "
            else:
                tmp = f"--{item}    "
            desc_opts.append(f" {tmp:<{max_len}}- {command_conf[item]['description']}")
            command_opts += tmp
        # stage 3
        for item in sorted(opt_value):
            tmp: str = ""
            if command_conf[item]["short"]:
                tmp = f"-{command_conf[item]['short']}|--{item}"
            else:
                tmp = f"--{item}   "
            desc_opts.append(f" {tmp:<{max_len}}- {command_conf[item]['description']}")
            command_opts += tmp
            if command_conf[item]["example"]:
                command_opts += f"{command_conf[item]['example']}"
            command_opts += " "
        print("###[HELP]###")
        print(f"{sys.argv[0]} {command_opts}")
        print(f"")
        print("# Arguments:")
        for item in desc_opts:
            print(item)
        sys.exit(2)


class LmsBase(DeclarativeBase):
    """Declarative Base class."""


# #[EOF]#######################################################################

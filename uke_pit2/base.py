# -*- coding: utf-8 -*-
"""
  base.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 27.03.2024, 13:17:19
  
  Purpose: Project base classes.
"""

import sys

from inspect import currentframe
from typing import List, Dict, Optional, Any

import uke_pit2

from jsktoolbox.libs.base_data import BData
from jsktoolbox.attribtool import ReadOnlyClass
from jsktoolbox.raisetool import Raise
from jsktoolbox.configtool.main import Config as ConfigTool
from jsktoolbox.logstool.logs import LoggerClient, ThLoggerProcessor


class _Keys(object, metaclass=ReadOnlyClass):
    """Internal _Keys container class."""

    COMMAND_LINE_OPTS: str = "__clo__"
    CONF: str = "__config__"
    CONFIG_FILE: str = "__config_file__"
    CONFIG_HANDLER: str = "__cfh__"
    LOGGER_CLIENT: str = "__logger_client__"
    PROC_LOGS: str = "__logger_processor__"
    SECTION: str = "__config_section__"


class BConfigSection(BData):
    """Base class for Config Section."""

    @property
    def section(self) -> Optional[str]:
        """Return section name."""
        if _Keys.SECTION not in self._data:
            self._data[_Keys.SECTION] = None
        return self._data[_Keys.SECTION]

    @section.setter
    def section(self, section_name: Optional[str]) -> None:
        """Set section name."""
        if section_name is None:
            self._data[_Keys.SECTION] = None
        self._data[_Keys.SECTION] = str(section_name).lower()


class BConfigHandler(BData):
    """Base class for Config handler."""

    @property
    def cfh(self) -> Optional[ConfigTool]:
        """Returns config handler object."""
        if _Keys.CONFIG_HANDLER not in self._data:
            self._data[_Keys.CONFIG_HANDLER] = None
        return self._data[_Keys.CONFIG_HANDLER]

    @cfh.setter
    def cfh(self, config_handler: Optional[ConfigTool]) -> None:
        """Sets config handler."""
        if config_handler is not None and not isinstance(config_handler, ConfigTool):
            raise Raise.error(
                f"Expected ConfigTool type, received'{type(config_handler)}'.",
                TypeError,
                self._c_name,
                currentframe(),
            )
        self._data[_Keys.CONFIG_HANDLER] = config_handler

    @property
    def config_file(self) -> Optional[str]:
        """Return config_file path string."""
        if _Keys.CONFIG_FILE not in self._data:
            self._data[_Keys.CONFIG_FILE] = None
        return self._data[_Keys.CONFIG_FILE]

    @config_file.setter
    def config_file(self, value: str) -> None:
        """Set config_file path string."""
        if not isinstance(value, str):
            raise Raise.error(
                f"Expected String type, received: '{type(value)}'.",
                TypeError,
                self._c_name,
                currentframe(),
            )
        self._data[_Keys.CONFIG_FILE] = value


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


class BLogs(BData):
    """Base class for LoggerClient property."""

    @property
    def logs(self) -> LoggerClient:
        """Returns LoggerClient object or None."""
        if _Keys.LOGGER_CLIENT not in self._data:
            self._data[_Keys.LOGGER_CLIENT] = LoggerClient()
        return self._data[_Keys.LOGGER_CLIENT]

    @logs.setter
    def logs(self, logger_client: LoggerClient) -> None:
        """Sets LoggerClient."""
        if not isinstance(logger_client, LoggerClient):
            raise Raise.error(
                f"Expected LoggerClient type, received: '{type(logger_client)}'.",
                TypeError,
                self._c_name,
                currentframe(),
            )
        self._data[_Keys.LOGGER_CLIENT] = logger_client


class BaseApp(BLogs, BConfigSection):
    """Main app base class."""

    from uke_pit2.conf import Config

    @property
    def conf(self) -> Optional[Config]:
        """Return Config class object."""
        if _Keys.CONF not in self._data:
            self._data[_Keys.CONF] = None
        return self._data[_Keys.CONF]

    @conf.setter
    def conf(self, conf_obj: Config) -> None:
        """Set Config class object."""

        from uke_pit2.conf import Config

        if not isinstance(conf_obj, Config):
            raise Raise.error(
                f"Expected Config class type, received: '{type(conf_obj)}'.",
                TypeError,
                self._c_name,
                currentframe(),
            )
        self._data[_Keys.CONF] = conf_obj

    @property
    def version(self) -> str:
        """Returns version information string."""
        return uke_pit2.VERSION

    @property
    def command_opts(self) -> bool:
        """Returns commands line flag"""
        if _Keys.COMMAND_LINE_OPTS not in self._data:
            self._data[_Keys.COMMAND_LINE_OPTS] = False
        return self._data[_Keys.COMMAND_LINE_OPTS]

    @command_opts.setter
    def command_opts(self, flag: bool) -> None:
        """Sets commands line flag."""
        if not isinstance(flag, bool):
            raise Raise.error(
                "Boolean flag expected.", TypeError, self._c_name, currentframe()
            )
        self._data[_Keys.COMMAND_LINE_OPTS] = flag

    @property
    def logs_processor(self) -> ThLoggerProcessor:
        """Return logs_processor."""
        if _Keys.PROC_LOGS not in self._data:
            self._data[_Keys.PROC_LOGS] = None
        return self._data[_Keys.PROC_LOGS]

    @logs_processor.setter
    def logs_processor(self, value: ThLoggerProcessor) -> None:
        """Set logs_processor."""
        if not isinstance(value, ThLoggerProcessor):
            raise Raise.error(
                f"Expected ThLoggerProcessor type, received: '{type(value)}'.",
                TypeError,
                self._c_name,
                currentframe(),
            )
        self._data[_Keys.PROC_LOGS] = value

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


# #[EOF]#######################################################################

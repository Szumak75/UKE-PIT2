# -*- coding: utf-8 -*-
"""
  conf.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 27.03.2024, 14:50:23
  
  Purpose: Config class.
"""

from inspect import currentframe
from typing import Optional, Dict

from jsktoolbox.attribtool import ReadOnlyClass
from jsktoolbox.raisetool import Raise
from jsktoolbox.configtool.main import Config as ConfigTool
from jsktoolbox.logstool.logs import LoggerQueue, LoggerClient
from jsktoolbox.stringtool.crypto import SimpleCrypto

from uke_pit2.base import BLogs, BConfigHandler, BModuleConfig, BConfigSection


class _Keys(object, metaclass=ReadOnlyClass):
    """Private _Keys container class."""

    APP_NAME: str = "__application_name__"
    CF: str = "__config_file_handler__"
    MAIN: str = "__main__"
    MODCONF: str = "__modconf__"
    DEBUG: str = "__debug__"


class _ModuleConf(BModuleConfig):
    """Module config private class."""

    class Keys(object, metaclass=ReadOnlyClass):
        """Internal Keys class for naming variables in the config file."""

        SALT: str = "salt"
        DEBUG: str = "debug"

    @property
    def salt(self) -> int:
        """Return salt var."""
        return self._get(_ModuleConf.Keys.SALT)


class Config(BLogs, BConfigHandler, BConfigSection):
    """Configuration container class."""

    def __init__(self, logger_queue: LoggerQueue, app_name: str) -> None:
        """Config constructor

        Arguments:
        - logger_queue [LoggerQueue] - queue for logger communication module
        - app_name [str] - application name string for logs
        """
        # class logger client
        self.logs = LoggerClient(queue=logger_queue, name=self._c_name)

        self.logs.message_info = "Config initialization..."
        self._data[_Keys.MAIN] = dict()
        self._data[_Keys.MODCONF] = None
        self.app_name = app_name
        self._data[_Keys.CF] = None
        self.logs.message_info = "... complete"

    def load(self) -> bool:
        """Try to load config file."""
        if self.config_file is None or self.section is None:
            self.logs.message_critical = (
                f"UNRECOVERABLE ERROR: {self._c_name}.{self._f_name}"
            )
            self.logs.message_error = (
                f"config file: {self.config_file}, section:{self.section}"
            )
            return False
        if self.cfh is None:
            config = ConfigTool(self.config_file, self.section)
            self.cfh = config
            self._data[_Keys.MODCONF] = _ModuleConf(config, self.section)
            if not config.file_exists:
                self.logs.message_warning = (
                    f"config file '{self.config_file}' does not exist"
                )
                self.logs.message_warning = "try to create default one"
                if not self.__create_config_file():
                    return False
        out: bool = False
        try:
            if self.debug:
                self.logs.message_debug = (
                    f"try to load config file: '{self.config_file}'..."
                )
            out = self.cfh.load()
            # TODO: process config file
            if out:
                if self.debug:
                    self.logs.message_debug = "config file loaded successful"
        except Exception as ex:
            self.logs.message_critical = (
                f"cannot load config file: '{self.config_file}'"
            )
            if self.debug:
                self.logs.message_debug = f"{ex}"
        return out

    def save(self) -> bool:
        """Try to save config file."""
        return False

    def reload(self) -> bool:
        """Try to reload config file."""
        return False

    def __create_config_file(self) -> bool:
        """Try to create the config file."""
        if self.cfh is None or self.section is None:
            return False
        # main section
        self.cfh.set(self.section, desc=f"{self.section} configuration file")
        # add debug
        self.cfh.set(self.section, varname=_ModuleConf.Keys.DEBUG, value=False)
        # add salt
        self.cfh.set(
            self.section,
            varname=_ModuleConf.Keys.SALT,
            value=SimpleCrypto.salt_generator(4),
            desc="[int] salt for passwords encode/decode",
        )
        # add mysql lms configuration

        # add spider section

        # add pit section

        # try to save the config file
        out: bool = False
        try:
            out = self.save()
        except Exception as ex:
            self.logs.message_critical = (
                f"cannot create config file: '{self.config_file}'"
            )
            if self.debug:
                self.logs.message_debug = f"{ex}"
        return out

    @property
    def app_name(self) -> Optional[str]:
        """Returns app name."""
        if _Keys.APP_NAME not in self.__main:
            self.__main[_Keys.APP_NAME] = None
        return self.__main[_Keys.APP_NAME]

    @app_name.setter
    def app_name(self, value: str) -> None:
        """Sets app name string."""
        if not isinstance(value, str):
            raise Raise.error(
                f"Expected string type",
                TypeError,
                self._c_name,
                currentframe(),
            )
        self.__main[_Keys.APP_NAME] = value
        self.section = value

    @property
    def __main(self) -> Dict:
        """Return MAIN dict."""
        return self._data[_Keys.MAIN]

    @property
    def debug(self) -> bool:
        """Return debug flag."""
        if _Keys.DEBUG not in self.__main:
            self.__main[_Keys.DEBUG] = False
        if self.cfh and self.section:
            if self.cfh.get(self.section, _ModuleConf.Keys.DEBUG):
                return True
        return self.__main[_Keys.DEBUG]

    @debug.setter
    def debug(self, value: bool) -> None:
        """Set debug flag."""
        if not isinstance(value, bool):
            raise Raise.error(
                f"Expected Boolean type, received: '{type(value)}'.",
                TypeError,
                self._c_name,
                currentframe(),
            )
        self.__main[_Keys.DEBUG] = value

    @property
    def module_conf(self) -> Optional[_ModuleConf]:
        """Return module conf object."""
        return self._data[_Keys.MODCONF]


# #[EOF]#######################################################################

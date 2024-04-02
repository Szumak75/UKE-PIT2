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
from jsktoolbox.netaddresstool.ipv4 import Address

from uke_pit2.base import BLogs, BConfigHandler, BModuleConfig, BConfigSection


class _Keys(object, metaclass=ReadOnlyClass):
    """Private _Keys container class."""

    APP_NAME: str = "__application_name__"
    CF: str = "__config_file_handler__"
    MAIN: str = "__main__"

    DEBUG: str = "debug"
    LMS_DB: str = "db_database"
    LMS_HOST: str = "db_host"
    LMS_PASS: str = "db_password"
    LMS_PORT: str = "db_port"
    LMS_USER: str = "db_user"
    SALT: str = "salt"


class _ModuleConf(BModuleConfig):
    """Module config private class."""

    @property
    def salt(self) -> int:
        """Return salt var."""
        return self._get(_Keys.SALT)

    @property
    def debug(self) -> bool:
        """Return debug var."""
        var: Optional[bool] = self._get(_Keys.DEBUG)
        if var is None:
            return False
        return var

    @property
    def lms_host(self) -> Optional[Address]:
        """Returns lms_host ip address as optional Address."""
        var: Optional[str] = self._get(_Keys.LMS_HOST)
        if not var:
            return None
        address = None
        try:
            address = Address(var)
        except Exception as e:
            pass
        return address

    @property
    def lms_port(self) -> Optional[int]:
        """Returns lms_port optional int."""
        var: Optional[int] = self._get(_Keys.LMS_PORT)
        if not var:
            return None
        return var

    @property
    def lms_database(self) -> Optional[str]:
        """Returns lms_database name."""
        var: Optional[str] = self._get(_Keys.LMS_DB)
        if not var:
            return None
        return var

    @property
    def lms_user(self) -> Optional[str]:
        """Returns lms_user name."""
        var: Optional[str] = self._get(_Keys.LMS_USER)
        if not var:
            return None
        return var

    @property
    def lms_password(self) -> Optional[str]:
        """Returns lms_password name."""
        var: Optional[str] = self._get(_Keys.LMS_PASS)
        if not var:
            return None
        return var


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
        self._data[_ModuleConf.Keys.MODCONF] = None
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
            self._data[_ModuleConf.Keys.MODCONF] = _ModuleConf(config, self.section)
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
                # check variables
                if self.module_conf:
                    # salt
                    if self.module_conf.salt is None or not isinstance(
                        self.module_conf.salt, int
                    ):
                        self.logs.message_critical = (
                            f"'{_Keys.SALT}' is not set properly."
                        )
                    # lms_host
                    if not self.module_conf.lms_host:
                        self.logs.message_critical = (
                            f"'{_Keys.LMS_HOST}' is not set properly."
                        )
                    # lms_port
                    if not self.module_conf.lms_port or not isinstance(
                        self.module_conf.lms_port, int
                    ):
                        self.logs.message_critical = (
                            f"'{_Keys.LMS_PORT}' is not set properly."
                        )
                    # lms_database
                    if not self.module_conf.lms_database:
                        self.logs.message_critical = (
                            f"'{_Keys.LMS_DB}' is not set properly."
                        )
                    # lms_user
                    if not self.module_conf.lms_user:
                        self.logs.message_critical = (
                            f"'{_Keys.LMS_USER}' is not set properly."
                        )
                    # lms_pass
                    if not self.module_conf.lms_password:
                        self.logs.message_critical = (
                            f"'{_Keys.LMS_PASS}' is not set properly."
                        )

        except Exception as ex:
            self.logs.message_critical = (
                f"cannot load config file: '{self.config_file}'"
            )
            if self.debug:
                self.logs.message_debug = f"{ex}"
        return out

    def save(self) -> bool:
        """Try to save config file."""
        if self.cfh:
            if self.cfh.save():
                if self.debug:
                    self.logs.message_debug = "config file saved successful"
                return True
            else:
                self.logs.message_warning = (
                    f"cannot save config file: '{self.config_file}'"
                )
        return False

    def reload(self) -> bool:
        """Try to reload config file."""
        self.cfh = None
        return self.load()

    def __create_config_file(self) -> bool:
        """Try to create the config file."""
        if self.cfh is None or self.section is None:
            return False
        # main section
        self.cfh.set(self.section, desc=f"{self.section} configuration file")
        # add debug
        self.cfh.set(self.section, varname=_Keys.DEBUG, value=True)
        # add salt
        self.cfh.set(
            self.section,
            varname=_Keys.SALT,
            value=SimpleCrypto.salt_generator(4),
            desc="[int] salt for passwords encode/decode",
        )
        # add mysql lms configuration
        self.cfh.set(
            self.section,
            varname=_Keys.LMS_HOST,
            desc="[str] lms mysql server IP",
        )
        self.cfh.set(
            self.section,
            varname=_Keys.LMS_PORT,
            value=3306,
            desc="[int] lms mysql server Port",
        )
        self.cfh.set(
            self.section,
            varname=_Keys.LMS_DB,
            desc="[str] lms database name",
        )
        self.cfh.set(
            self.section,
            varname=_Keys.LMS_USER,
            desc="[str] lms user name",
        )
        self.cfh.set(
            self.section,
            varname=_Keys.LMS_PASS,
            desc="[str] lms user password",
        )

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

    def set_lms_password(self, password: str) -> None:
        """Sets lms password."""
        if self.cfh is None or self.section is None:
            self.logs.message_critical = f"Config isn't initialized properly."
            return None

        self.cfh.set(section=self.section, varname=_Keys.LMS_PASS, value=password)
        if not self.save():
            self.logs.message_critical = f"Cannot update lms password."
        else:
            self.reload()

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
        """Returns MAIN dict."""
        return self._data[_Keys.MAIN]

    @property
    def debug(self) -> bool:
        """Returns debug flag."""
        if _Keys.DEBUG not in self.__main:
            self.__main[_Keys.DEBUG] = False
        if self.cfh and self.section:
            if self.cfh.get(self.section, _Keys.DEBUG):
                return True
        return self.__main[_Keys.DEBUG]

    @debug.setter
    def debug(self, value: bool) -> None:
        """Sets debug flag."""
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
        """Returns module conf object."""
        return self._data[_ModuleConf.Keys.MODCONF]


# #[EOF]#######################################################################

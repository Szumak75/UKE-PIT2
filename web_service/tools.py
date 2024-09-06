# -*- coding: utf-8 -*-
"""
  tools.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 23.04.2024, 12:42:13
  
  Purpose: tools for project.
"""

from inspect import currentframe
from typing import Optional, Any

from jsktoolbox.attribtool import NoDynamicAttributes, ReadOnlyClass
from jsktoolbox.configtool.main import Config as ConfigTool
from jsktoolbox.raisetool import Raise
from jsktoolbox.systemtool import PathChecker
from jsktoolbox.basetool.data import BData
from jsktoolbox.stringtool.crypto import SimpleCrypto
from jsktoolbox.netaddresstool.ipv4 import Address


class _Keys(object, metaclass=ReadOnlyClass):
    """Keys definition container class."""

    DB_DATABASE: str = "db_database"
    DB_HOST: str = "db_host"
    DB_LOGIN: str = "db_user"
    DB_PASSWORD: str = "db_password"
    DB_PORT: str = "db_port"
    DEBUG: str = "debug"
    SALT: str = "salt"


class _ModuleConfig(BData):
    """Base class for module config classes."""

    class Keys(object, metaclass=ReadOnlyClass):
        """Keys definition container class."""

        SECTION: str = "__section_name__"
        CFH: str = "__config_handler__"

    def __init__(self, cfh: ConfigTool, section: Optional[str]) -> None:
        """Constructor."""
        self.__cf__ = cfh
        self._section = section

    def _get(self, varname: str) -> Any:
        """Get variable from config."""
        if self.__cf__ and self._section:
            return self.__cf__.get(self._section, varname)
        return None

    @property
    def _section(self) -> Optional[str]:
        """Return section name."""
        return self._get_data(self.Keys.SECTION, set_default_type=Optional[str])

    @_section.setter
    def _section(self, section_name: Optional[str]) -> None:
        """Set section name."""
        self._set_data(
            self.Keys.SECTION,
            set_default_type=Optional[str],
            value=str(section_name).lower(),
        )

    @property
    def __cf__(self) -> Optional[ConfigTool]:
        """Return config handler object."""
        return self._get_data(self.Keys.CFH, set_default_type=Optional[ConfigTool])

    @__cf__.setter
    def __cf__(self, config_handler: Optional[ConfigTool]) -> None:
        """Set config handler."""
        self._set_data(
            self.Keys.CFH, set_default_type=Optional[ConfigTool], value=config_handler
        )


class WebConfig(NoDynamicAttributes):
    """docstring for WebConfig."""

    __main_section__: str = "uke-pit2"
    __file_name__: str = "/etc/uke-pit2.conf"
    __cf__: Optional[ConfigTool] = None
    __m_conf__: Optional[_ModuleConfig] = None
    __errors: bool = False

    def __init__(self) -> None:
        """Constructor."""
        # init config
        if not self.__init_config_file():
            print("configuration error")

        # check errors
        self.__check_config()

    def __init_config_file(self) -> bool:
        self.__cf__ = ConfigTool(self.__file_name__, self.__main_section__)
        self.__m_conf__ = _ModuleConfig(self.__cf__, self.__main_section__)
        if not self.__cf__.file_exists:
            if not self.__create_config_file():
                self.__errors = True
                return False
        else:
            return self.__cf__.load()
        return True

    def __check_config(self) -> None:
        test = True

        if self.salt is None or not isinstance(self.salt, int):
            test = False

        if self.db_host is None or not isinstance(self.db_host, Address):
            test = False

        if self.db_port is None or not isinstance(self.db_port, int):
            test = False

        if (
            self.db_database is None
            or not self.db_database
            or not isinstance(self.db_database, str)
        ):
            test = False

        if (
            self.db_login is None
            or not self.db_login
            or not isinstance(self.db_login, str)
        ):
            test = False
        if (
            self.db_password is None
            or not self.db_password
            or not isinstance(self.db_password, str)
        ):
            test = False

        # if any test failed, set errors
        self.__errors = not test

    def __create_config_file(self) -> bool:
        """Try to create config file."""
        if self.__cf__ is None:
            return False
        # set header file
        self.__cf__.set(
            self.__main_section__, desc=f"{self.__main_section__} configuration file"
        )
        # add salt variable
        self.__cf__.set(
            self.__main_section__,
            varname=_Keys.SALT,
            value=SimpleCrypto.salt_generator(6),
            desc="[int] salt for passwords encode/decode",
        )
        # add debug variable
        self.__cf__.set(
            self.__main_section__,
            varname=_Keys.DEBUG,
            value=False,
            desc="[boolean] debug logging level.",
        )
        # add db_host variable
        self.__cf__.set(
            self.__main_section__,
            varname=_Keys.DB_HOST,
            desc="[str] IPv4 address for mysql database.",
        )
        # add db_port variable
        self.__cf__.set(
            self.__main_section__,
            varname=_Keys.DB_PORT,
            value=3306,
            desc="[int] port number for mysql database.",
        )
        # add db_database variable
        self.__cf__.set(
            self.__main_section__,
            varname=_Keys.DB_DATABASE,
            value="",
            desc="[str] LMS database name.",
        )
        # add db_login variable
        self.__cf__.set(
            self.__main_section__,
            varname=_Keys.DB_LOGIN,
            value="",
            desc="[str] LMS database login name.",
        )
        # add db_password variable
        self.__cf__.set(
            self.__main_section__,
            varname=_Keys.DB_PASSWORD,
            value="",
            desc="[str] LMS database encrypted password.",
        )

        test: bool = False
        try:
            test = self.save()
        except Exception as ex:
            # self.logs.message_critical = (
            #     f"cannot create config file: '{self.config_file}'"
            # )
            # if self.debug:
            #     self.logs.message_debug = f"{ex}"
            print(f"{ex}")

        return test

    def load(self) -> bool:
        """Try to load config file."""
        out: bool = False
        if self.__cf__ is None:
            return out
        try:
            out = self.__cf__.load()
        except Exception as ex:
            self.__errors = True
            print(f"{ex}")
        return out

    def save(self) -> bool:
        """Try to save config file."""
        if self.__cf__:
            if self.__cf__.save():
                # if self.debug:
                #     self.logs.message_debug = "config file saved successful"
                return True
            else:
                # self.logs.message_warning = (
                #     f"cannot save config file: '{self.config_file}'"
                # )
                print(f"cannot save config file: '{self.__file_name__}'")
        return False

    @property
    def debug(self) -> bool:
        if self.__m_conf__ is None:
            return True
        tmp = self.__m_conf__._get(_Keys.DEBUG)
        if tmp is not None and isinstance(tmp, bool):
            return tmp
        return False

    @property
    def salt(self) -> Optional[int]:
        if self.__m_conf__ is None:
            return None
        salt = self.__m_conf__._get(_Keys.SALT)
        if salt is not None and isinstance(salt, int):
            return salt
        return None

    @property
    def db_host(self) -> Optional[Address]:
        if self.__m_conf__ is None:
            return None
        host = self.__m_conf__._get(_Keys.DB_HOST)
        if host is not None and isinstance(host, str):
            return Address(host)
        return None

    @property
    def db_port(self) -> Optional[int]:
        if self.__m_conf__ is None:
            return None
        port = self.__m_conf__._get(_Keys.DB_PORT)
        if port is not None and isinstance(port, int):
            return port
        return None

    @property
    def db_database(self) -> Optional[str]:
        if self.__m_conf__ is None:
            return None
        tmp = self.__m_conf__._get(_Keys.DB_DATABASE)
        if tmp is not None and isinstance(tmp, str):
            return tmp
        return None

    @property
    def db_login(self) -> Optional[str]:
        if self.__m_conf__ is None:
            return None
        tmp = self.__m_conf__._get(_Keys.DB_LOGIN)
        if tmp is not None and isinstance(tmp, str):
            return tmp
        return None

    @property
    def db_password(self) -> Optional[str]:
        if self.__m_conf__ is None:
            return None
        tmp = self.__m_conf__._get(_Keys.DB_PASSWORD)
        if tmp is not None and isinstance(tmp, str):
            return tmp
        return None

    @db_password.setter
    def db_password(self, passwd: str) -> None:
        if passwd and isinstance(passwd, str) and self.__cf__:
            self.__cf__.set(
                self.__main_section__, varname=_Keys.DB_PASSWORD, value=passwd
            )
            test: bool = False
            try:
                test = self.save()
            except Exception as ex:
                print(f"{ex}")
            if not test:
                print("Configuration update error.")

    @property
    def errors(self) -> bool:
        return self.__errors


# #[EOF]#######################################################################

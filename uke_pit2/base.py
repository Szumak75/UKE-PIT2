# -*- coding: utf-8 -*-
"""
  base.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 27.03.2024, 13:17:19
  
  Purpose: Project base classes.
"""

import sys

from inspect import currentframe
from typing import List, Dict

import uke_pit2

from jsktoolbox.libs.base_data import BData
from jsktoolbox.attribtool import ReadOnlyClass
from jsktoolbox.raisetool import Raise


class _Keys(object, metaclass=ReadOnlyClass):
    """Internal _Keys container class."""

    COMMAND_LINE_OPTS: str = "__clo__"


class BaseApp(BData):
    """Main app base class."""

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
        """Set commands line flag."""
        if not isinstance(flag, bool):
            raise Raise.error(
                "Boolean flag expected.", TypeError, self._c_name, currentframe()
            )
        self._data[_Keys.COMMAND_LINE_OPTS] = flag

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

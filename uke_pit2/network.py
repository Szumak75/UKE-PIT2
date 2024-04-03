# -*- coding: utf-8 -*-
"""
  network.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 2.04.2024, 15:32:12
  
  Purpose: tests for network device
"""


import os
import subprocess

from inspect import currentframe
from distutils.spawn import find_executable
from typing import Optional, Dict, List

from jsktoolbox.attribtool import ReadOnlyClass
from jsktoolbox.raisetool import Raise
from jsktoolbox.netaddresstool.ipv4 import Address
from jsktoolbox.libs.base_data import BData


class _Keys(object, metaclass=ReadOnlyClass):
    """Private Keys definition class.

    For internal purpose only.
    """

    CMD: str = "cmd"
    COMMAND: str = "__command_found__"
    COMMANDS: str = "__commands__"
    MULTIPLIER: str = "__multiplier__"
    OPTS: str = "opts"
    TIMEOUT: str = "__timeout__"


class Pinger(BData):
    """Pinger class for testing ICMP echo."""

    def __init__(self, timeout: int = 1) -> None:
        """Constructor.

        Arguments:
        - timeout [int] - timeout in seconds
        """
        if not isinstance(timeout, int):
            raise Raise.error(
                f"Expected Integer type, received: '{type(timeout)}'.",
                TypeError,
                self._c_name,
                currentframe(),
            )
        self._data[_Keys.TIMEOUT] = timeout
        self._data[_Keys.COMMANDS] = []
        self._data[_Keys.MULTIPLIER] = 1
        self._data[_Keys.COMMANDS].append(
            {
                _Keys.CMD: "fping",
                _Keys.MULTIPLIER: 1000,
                _Keys.OPTS: "-AaqR -B1 -r2 -t{} {} >/dev/null 2>&1",
            }
        )
        self._data[_Keys.COMMANDS].append(
            {
                # FreeBSD ping
                _Keys.CMD: "ping",
                _Keys.MULTIPLIER: 1000,
                _Keys.OPTS: "-Qqo -c3 -W{} {} >/dev/null 2>&1",
            }
        )
        self._data[_Keys.COMMANDS].append(
            {
                # Linux ping
                _Keys.CMD: "ping",
                _Keys.MULTIPLIER: 1,
                _Keys.OPTS: "-q -c3 -W{} {} >/dev/null 2>&1",
            }
        )
        tmp: Optional[tuple] = self.__is_tool
        if tmp:
            (
                self._data[_Keys.COMMAND],
                self._data[_Keys.MULTIPLIER],
            ) = tmp

    def is_alive(self, ip: Address) -> bool:
        """Check ICMP echo response."""
        if not isinstance(ip, Address):
            raise Raise.error(
                f"Address type expected, '{type(ip)}' received.",
                TypeError,
                self._c_name,
                currentframe(),
            )
        if self._data[_Keys.COMMAND] is None:
            raise Raise.error(
                "Command for testing ICMP echo not found.",
                ChildProcessError,
                self._c_name,
                currentframe(),
            )
        if (
            os.system(
                self._data[_Keys.COMMAND].format(
                    int(self._data[_Keys.TIMEOUT] * self._data[_Keys.MULTIPLIER]),
                    str(ip),
                )
            )
        ) == 0:
            return True
        return False

    @property
    def __is_tool(self) -> Optional[tuple]:
        """Check system command."""
        for cmd in self._data[_Keys.COMMANDS]:
            if find_executable(cmd[_Keys.CMD]) is not None:
                test_cmd: str = f"{cmd[_Keys.CMD]} {cmd[_Keys.OPTS]}"
                multi: int = cmd[_Keys.MULTIPLIER]
                if (
                    os.system(
                        test_cmd.format(
                            int(self._data[_Keys.TIMEOUT] * multi),
                            "127.0.0.1",
                        )
                    )
                    == 0
                ):
                    return test_cmd, multi
        return None


# #[EOF]#######################################################################

# -*- coding: utf-8 -*-
"""
  main.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 27.03.2024, 13:08:55
  
  Purpose: Project main classes.
"""

from typing import Optional

from jsktoolbox.attribtool import ReadOnlyClass
from jsktoolbox.libs.system import CommandLineParser

from uke_pit2.base import BaseApp


class _Keys(object, metaclass=ReadOnlyClass):
    """Internal _Keys container class."""


class SpiderApp(BaseApp):
    """Spider main class."""

    def __init__(self) -> None:
        """SpiderAdd constructor."""

        # check command line
        self.__init_command_line()

        print("stop")

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


# #[EOF]#######################################################################

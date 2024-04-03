# -*- coding: utf-8 -*-
"""
  rb.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 2.04.2024, 15:32:49
  
  Purpose: mikrotik router board class.
"""

from abc import ABC
from inspect import currentframe
from typing import Optional, List, Dict, Any

from jsktoolbox.attribtool import ReadOnlyClass
from jsktoolbox.logstool.logs import LoggerClient, LoggerQueue
from jsktoolbox.libs.base_data import BData
from jsktoolbox.libs.base_th import ThBaseObject
from jsktoolbox.libs.base_logs import BLoggerQueue
from jsktoolbox.netaddresstool.ipv4 import Address
from jsktoolbox.raisetool import Raise
from jsktoolbox.devices.network.connectors import API
from jsktoolbox.devices.mikrotik.routerboard import RouterBoard
from jsktoolbox.devices.mikrotik.elements.libs.search import RBQuery
from jsktoolbox.devices.mikrotik.base import Element

from uke_pit2.base import BLogs, BDebug


class _Keys(object, metaclass=ReadOnlyClass):
    """Internal keys container class."""


class IRouterBoardCollector(ABC):
    """Collector interface class."""


class RouterBoardVersion:
    """ROS Version checker class."""


class __Collector(BLogs, BDebug):
    """Private Collector main class."""

    def __init__(self, logger_queue: LoggerQueue, debug: bool = False) -> None:
        """Collector constructor."""

        self.logs = LoggerClient(logger_queue, "RouterBoardCollector")
        self.debug = debug


class RouterBoardCollector6(IRouterBoardCollector, __Collector):
    """Collector class for ROS 6."""


class RouterBoardCollector7(IRouterBoardCollector, __Collector):
    """Collector class for ROS 7."""


# #[EOF]#######################################################################

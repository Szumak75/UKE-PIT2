# -*- coding: utf-8 -*-
"""
  generators.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 23.08.2024, 12:41:22
  
  Purpose: Report generators classes.
"""

from typing import Optional, List, Tuple
from threading import Event, Thread
from inspect import currentframe
from queue import Queue, Empty

from jsktoolbox.attribtool import ReadOnlyClass
from jsktoolbox.logstool.logs import (
    LoggerClient,
    LoggerQueue,
)

from jsktoolbox.libs.base_th import ThBaseObject
from jsktoolbox.netaddresstool.ipv4 import Address, Network
from jsktoolbox.raisetool import Raise
from jsktoolbox.datetool import Timestamp

from uke_pit2.base import BReportGenerator
from uke_pit2.conf import Config


class ThReportGenerator(Thread, ThBaseObject, BReportGenerator):
    """Report Generator class."""

    def __init__(
        self,
        logger_queue: LoggerQueue,
        config: Config,
    ) -> None:
        """Constructor."""
        # init thread
        Thread.__init__(self, name=f"{self._c_name}")
        self._stop_event = Event()
        self.sleep_period = 0.2
        # config
        self.conf = config
        # logger
        self.logs = LoggerClient(logger_queue, f"{self._c_name}")
        self.logs.message_debug = f"initializing complete"

    def run(self) -> None:
        """Start procedure."""
        self.logs.message_notice = f"stop is set: {self.stop}"


# #[EOF]#######################################################################

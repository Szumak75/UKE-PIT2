# -*- coding: utf-8 -*-
"""
  processor.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 2.04.2024, 15:33:28
  
  Purpose: processor class.
"""


from typing import Optional, List
from threading import Event, Thread
from inspect import currentframe

from jsktoolbox.attribtool import ReadOnlyClass
from jsktoolbox.logstool.logs import LoggerClient, LoggerQueue
from jsktoolbox.libs.base_data import BData
from jsktoolbox.libs.base_th import ThBaseObject
from jsktoolbox.libs.base_logs import BLoggerQueue
from jsktoolbox.netaddresstool.ipv4 import Address
from jsktoolbox.raisetool import Raise

from uke_pit2.base import BLogs
from uke_pit2.network import Pinger


class _Keys(object, metaclass=ReadOnlyClass):
    """Internal Keys container class."""

    IP: str = "__host_ip__"


class Processor(Thread, ThBaseObject, BLogs):
    """Processor class for router board object."""

    def __init__(
        self,
        logger_queue: LoggerQueue,
        ip: Address,
        passwords: List[str],
        debug: bool = False,
    ) -> None:
        """Processor constructor.

        # Arguments:
        - logger_queue [LoggerQueue] - logger queue for communication.
        - ip [Address] - router ip address.
        - passwords [List[str]] - list of router passwords
        - debug [bool] - debug flag.
        """
        # init thread
        Thread.__init__(self, name=f"{self._c_name} [{ip}]")
        self._stop_event = Event()
        self.sleep_period = 0.2
        # set ip
        self.ip = ip
        # debug
        self._debug = debug
        # logger
        self.logs = LoggerClient(logger_queue, f"{self._c_name} {ip}")

    def run(self) -> None:
        """Start processor."""
        if self._debug:
            self.logs.message_debug = "starting..."

        # the main procedure
        if not self.has_stop_set:
            # check icmp to ip
            self.__check_icmp()

        if self._debug:
            self.logs.message_debug = "stopped"

    def stop(self) -> None:
        """Sets stop event."""
        if self._stop_event:
            if self._debug:
                self.logs.message_debug = "stopping..."
            self._stop_event.set()

    def __check_icmp(self) -> None:
        """Check ipv4 responses."""
        test = Pinger()
        if not test.is_alive(f"{self.ip}"):
            if self._debug:
                self.logs.message_debug = f"host {self.ip} not responding."
            self.stop()

    @property
    def ip(self) -> Address:
        """Returns IPv4 router board address."""
        if _Keys.IP not in self._data:
            self._data[_Keys.IP] = Address("127.0.0.1")
        return self._data[_Keys.IP]

    @ip.setter
    def ip(self, value: Address) -> None:
        """Sets IPv4 router board address."""
        if not isinstance(value, Address):
            raise Raise.error(
                f"Address type expected, type: '{type(value)}' received.",
                TypeError,
                self._c_name,
                currentframe(),
            )
        self._data[_Keys.IP] = value

    @property
    def has_stop_set(self) -> bool:
        """Returns stop flag."""
        if self._stop_event:
            return self._stop_event.is_set()
        return False


# #[EOF]#######################################################################

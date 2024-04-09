# -*- coding: utf-8 -*-
"""
  rb.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 2.04.2024, 15:32:49
  
  Purpose: mikrotik router board class.
"""

import re

from abc import ABC, abstractmethod
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

from uke_pit2.base import BLogs, BDebug, BRouterBoard


class IRouterBoardCollector(ABC):
    """Collector interface class."""

    @abstractmethod
    def collect(self) -> None:
        """Fire up collector procedures."""


class RouterBoardVersion(BLogs, BDebug, BRouterBoard):
    """ROS Version checker class."""

    def __init__(
        self, logger_queue: LoggerQueue, rb_handler: RouterBoard, debug: bool = False
    ) -> None:
        """Collector constructor."""

        self.logs = LoggerClient(logger_queue, self._c_name)
        self.rb = rb_handler
        self.debug = debug

    def get_collector(self) -> Optional[IRouterBoardCollector]:
        """Returns collector proper for rb version."""

        if self.rb:
            out: Optional[Element] = self.rb.element(
                "/system/routerboard/", auto_load=True
            )
            if out:
                rbq = RBQuery()
                rbq.add_attrib("current-firmware")
                self.logs.message_debug = f"{out.search(rbq.query)}"
                squery = out.search(rbq.query)
                if squery and isinstance(squery, dict) and "current-firmware" in squery:
                    ver = squery["current-firmware"]
                    self.logs.message_debug = f"The version is: {ver}"

                    if re.match(r"^6\.", ver):
                        if self.logs.logs_queue:
                            return RouterBoardCollector6(
                                logger_queue=self.logs.logs_queue,
                                rb_handler=self.rb,
                                debug=self.debug,
                            )
                    elif re.match(r"^7\.", ver):
                        if self.logs.logs_queue:
                            return RouterBoardCollector7(
                                logger_queue=self.logs.logs_queue,
                                rb_handler=self.rb,
                                debug=self.debug,
                            )

        return None


class __Collector(BLogs, BDebug, BRouterBoard):
    """Private Collector main class."""

    def __init__(
        self, logger_queue: LoggerQueue, rb_handler: RouterBoard, debug: bool = False
    ) -> None:
        """Collector constructor."""

        self.logs = LoggerClient(logger_queue, "RouterBoardCollector")
        self.rb = rb_handler
        self.debug = debug

        # init tables
        self._data[_Keys.ETHER] = []
        self._data[_Keys.VLAN] = []
        self._data[_Keys.ADDRESS] = []
        self._data[_Keys.NEIGHBOR] = []

    @property
    def addresses(self) -> List[Dict[str, Any]]:
        return self._data[_Keys.ADDRESS]

    @property
    def ethers(self) -> List[Dict[str, Any]]:
        return self._data[_Keys.ETHER]

    @property
    def neighbors(self) -> List[Dict[str, Any]]:
        return self._data[_Keys.NEIGHBOR]

    @property
    def vlans(self) -> List[Dict[str, Any]]:
        return self._data[_Keys.VLAN]

    def dump(self) -> None:
        self.logs.message_debug = f"{self.ethers}"
        self.logs.message_debug = f"{self.vlans}"
        self.logs.message_debug = f"{self.neighbors}"
        self.logs.message_debug = f"{self.addresses}"


class _Keys(object, metaclass=ReadOnlyClass):
    """Internal keys container class."""

    ADDRESS: str = "__addr__"
    ETHER: str = "__eth__"
    NEIGHBOR: str = "__nb__"
    VLAN: str = "__vlan__"


class RouterBoardCollector6(IRouterBoardCollector, __Collector):
    """Collector class for ROS 6."""

    def collect(self) -> None:
        """Fire up collector procedures."""

        if not self.rb:
            return None


class RouterBoardCollector7(IRouterBoardCollector, __Collector):
    """Collector class for ROS 7."""

    def collect(self) -> None:
        """Fire up collector procedures."""

        if not self.rb:
            return None

        # interfaces
        inf: Optional[Element] = self.rb.element("/interface/ethernet/", auto_load=True)
        if inf:
            query = RBQuery()
            query.add_attrib("type", "ether")
            query.add_attrib("disabled", "false")
            query.add_attrib("running", "true")
            out = inf.search(query.query)
            if out:
                for item in out:
                    self.ethers.append(
                        {
                            ".id": item[".id"],
                            "name": item["name"],
                            "default-name": item["default-name"],
                            "mtu": item["mtu"],
                            "l2mtu": item["l2mtu"],
                            "mac-address": item["mac-address"],
                        }
                    )

        # vlans
        vlan: Optional[Element] = self.rb.element("/interface/vlan/", auto_load=True)
        if vlan:
            query = RBQuery()
            query.add_attrib("disabled", "false")
            query.add_attrib("running", "true")
            out = vlan.search(query.query)
            if out:
                for item in out:
                    self.vlans.append(
                        {
                            ".id": item[".id"],
                            "name": item["name"],
                            "mtu": item["mtu"],
                            "l2mtu": item["l2mtu"],
                            "mac-address": item["mac-address"],
                            "interface": item["interface"],
                            "vlan-id": item["vlan-id"],
                        }
                    )

        # ospf-neighbors
        neighbor: Optional[Element] = self.rb.element(
            "/routing/ospf/neighbor/", auto_load=True
        )
        if neighbor:
            query = RBQuery()
            query.add_attrib("state", "Full")
            out = neighbor.search(query.query)
            if out:
                for item in out:
                    self.neighbors.append(
                        {"router-id": item["router-id"], "address": item["address"]}
                    )

        # address
        address: Optional[Element] = self.rb.element("/ip/address/", auto_load=True)
        if address:
            query = RBQuery()
            query.add_attrib("disabled", "false")
            query.add_attrib("dynamic", "false")
            out = address.search(query.query)
            if out:
                for item in out:
                    self.addresses.append(item)


# #[EOF]#######################################################################

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
from typing import Optional, Union, List, Dict, Any

from jsktoolbox.attribtool import ReadOnlyClass
from jsktoolbox.logstool.logs import LoggerClient, LoggerQueue
from jsktoolbox.libs.base_data import BData
from jsktoolbox.libs.base_th import ThBaseObject
from jsktoolbox.libs.base_logs import BLoggerQueue
from jsktoolbox.netaddresstool.ipv4 import Address, Network
from jsktoolbox.raisetool import Raise
from jsktoolbox.devices.network.connectors import API
from jsktoolbox.devices.mikrotik.routerboard import RouterBoard
from jsktoolbox.devices.mikrotik.elements.libs.search import RBQuery
from jsktoolbox.devices.mikrotik.base import Element

from uke_pit2.base import BLogs, BDebug, BRouterBoard


class _Keys(object, metaclass=ReadOnlyClass):
    """Internal keys container class."""

    ADDRESS: str = "__addr__"
    ETHER: str = "__eth__"
    NEIGHBOR: str = "__nb__"
    PPP: str = "__ppp__"
    VLAN: str = "__vlan__"

    # RBData keys
    ROUTERS: str = "__rb_data_routers__"


class RBData(BData):
    """Router board data container class."""

    def __init__(self) -> None:
        """RBData constructor."""
        self._data[_Keys.ROUTERS] = []

    @property
    def routers(self) -> List[Dict[str, str]]:
        """Returns list of dict for neighbor routers."""
        return self._data[_Keys.ROUTERS]

    def __repr__(self) -> str:
        return f"{self._c_name}(routers: {self.routers})"


class IRouterBoardCollector(ABC):
    """Collector interface class."""

    @abstractmethod
    def collect(self) -> None:
        """Fire up collector procedures."""

    @abstractmethod
    def get_data(self) -> RBData:
        """Returns collected data."""


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
                search_query = out.search(rbq.query)
                if (
                    search_query
                    and isinstance(search_query, dict)
                    and "current-firmware" in search_query
                ):
                    ver = search_query["current-firmware"]
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
        self._data[_Keys.ETHER] = None
        self._data[_Keys.VLAN] = None
        self._data[_Keys.ADDRESS] = None
        self._data[_Keys.NEIGHBOR] = None
        self._data[_Keys.PPP] = None

    def __get_vlan_interface(
        self, interface: str
    ) -> tuple[Optional[str], Optional[int]]:
        """Returns vlan interface if found."""
        vlans = RBQuery()
        vlans.add_attrib("name", interface)

        real_interface: Optional[str] = None
        vlan_id: Optional[int] = None

        if self.vlans:
            search: Optional[Union[List[Any], Dict[Any, Any]]] = self.vlans.search(
                vlans.query
            )
            if search and isinstance(search, List):
                for item in search:
                    real_interface = item["interface"]
                    vlan_id = item["vlan-id"]

        return real_interface, vlan_id

    def __get_neighbor_interface(
        self, address: Address
    ) -> tuple[str, Optional[int], Optional[Network]]:
        """Returns real interface name and optional vlan-id."""
        # neighbor = RBQuery()
        # neighbor.add_attrib("address", str(address))

        # if self.neighbors:
        #     neighbor_search: Optional[Union[List[Any], Dict[Any, Any]]] = (
        #         self.neighbors.search(neighbor.query)
        #     )
        #     if neighbor_search and isinstance(neighbor_search, List):
        #         self.logs.message_debug = f"{neighbor_search}"

        # compare addresses
        interface: str = ""
        vlan_id: Optional[int] = None
        network: Optional[Network] = None

        addresses = RBQuery()
        addresses.add_attrib("dynamic", "false")
        addresses.add_attrib("disabled", "false")

        if self.addresses:
            search: Optional[Union[List[Any], Dict[Any, Any]]] = self.addresses.search(
                addresses.query
            )
            if search and isinstance(search, List):
                for item in search:
                    if "address" in item:
                        network = Network(item["address"])
                        if address >= network.network and address <= network.broadcast:
                            # found item
                            interface = item["interface"]
                            break

        # check vlans
        out_interface: Optional[str] = None
        out_vlan_id: Optional[int] = None
        while True:
            out_interface, out_vlan_id = self.__get_vlan_interface(interface)
            if out_interface:
                interface = out_interface
                if not vlan_id and out_vlan_id:
                    vlan_id = out_vlan_id
            else:
                break

        return interface, vlan_id, network

    def _build_routers_data(self) -> List[Dict[str, Any]]:
        """Build and returns list of routers data from collected elements."""
        out: List[Dict[str, Any]] = []
        neighbors = RBQuery()
        neighbors.add_attrib("state", "Full")
        if self.neighbors:
            search: Optional[Union[List[Any], Dict[Any, Any]]] = self.neighbors.search(
                neighbors.query
            )
            if search and isinstance(search, List):
                for item in search:
                    tmp: Dict[str, Any] = {}
                    if "router-id" in item:
                        tmp["router-id"] = Address(item["router-id"])
                    if "address" in item:
                        tmp["address"] = Address(item["address"])
                        # search for interface
                        inf: str
                        vlan_id: Optional[int]
                        network: Optional[Network]
                        inf, vlan_id, network = self.__get_neighbor_interface(
                            Address(item["address"])
                        )
                        tmp["interface"] = inf
                        tmp["vlan-id"] = vlan_id
                        tmp["network"] = network
                    out.append(tmp)
        return out

    @property
    def addresses(self) -> Optional[Element]:
        return self._data[_Keys.ADDRESS]

    @addresses.setter
    def addresses(self, value: Optional[Element]) -> None:
        self._data[_Keys.ADDRESS] = value

    @property
    def ethers(self) -> Optional[Element]:
        return self._data[_Keys.ETHER]

    @ethers.setter
    def ethers(self, value: Optional[Element]) -> None:
        self._data[_Keys.ETHER] = value

    @property
    def neighbors(self) -> Optional[Element]:
        return self._data[_Keys.NEIGHBOR]

    @neighbors.setter
    def neighbors(self, value: Optional[Element]) -> None:
        self._data[_Keys.NEIGHBOR] = value

    @property
    def ppp(self) -> Optional[Element]:
        return self._data[_Keys.PPP]

    @ppp.setter
    def ppp(self, value: Optional[Element]) -> None:
        self._data[_Keys.PPP] = value

    @property
    def vlans(self) -> Optional[Element]:
        return self._data[_Keys.VLAN]

    @vlans.setter
    def vlans(self, value: Optional[Element]) -> None:
        self._data[_Keys.VLAN] = value

    def dump(self) -> None:
        # self.logs.message_debug = f"{self.ethers}"
        # self.logs.message_debug = f"{self.vlans}"
        self.logs.message_debug = f"{self.neighbors}"
        # self.logs.message_debug = f"{self.addresses}"
        # self.logs.message_debug = f"{self.ppp}"


class BRouterBoardCollector:
    """Base class for RouterBoardCollector."""


class RouterBoardCollector6(IRouterBoardCollector, __Collector):
    """Collector class for ROS 6."""

    def collect(self) -> None:
        """Fire up collector procedures."""

        if not self.rb:
            return None

        # interfaces
        # example:
        # {'.id': '*9', 'name': 'ether9', 'default-name': 'ether9', 'mtu': '1500', 'l2mtu': '1592', 'mac-address': 'DC:2C:6E:0F:57:67',
        # 'orig-mac-address': 'DC:2C:6E:0F:57:67', 'arp': 'enabled', 'arp-timeout': 'auto', 'loop-protect': 'default',
        # 'loop-protect-status': 'off', 'loop-protect-send-interval': '5s', 'loop-protect-disable-time': '5m', 'auto-negotiation': 'true',
        # 'advertise': '10M-half,10M-full,100M-half,100M-full,1000M-half,1000M-full', 'full-duplex': 'true', 'tx-flow-control': 'off',
        # 'rx-flow-control': 'off', 'speed': '1Gbps', 'bandwidth': 'unlimited/unlimited', 'switch': 'switch2',
        # 'driver-rx-byte': '4689493024635', 'driver-rx-packet': '29087429173', 'driver-tx-byte': '76438567589070',
        # 'driver-tx-packet': '59971028302', 'rx-bytes': '4788662691081', 'rx-broadcast': '2231013', 'rx-pause': '0',
        # 'rx-multicast': '57934019', 'rx-fcs-error': '0', 'rx-fragment': '0', 'rx-unknown-op': '0', 'rx-code-error': '0',
        # 'rx-jabber': '0', 'rx-drop': '0', 'tx-bytes': '76669861134963', 'tx-broadcast': '1274818', 'tx-pause': '0',
        # 'tx-multicast': '150818408', 'tx-collision': '0', 'tx-excessive-collision': '0', 'tx-multiple-collision': '0',
        # 'tx-single-collision': '0', 'tx-deferred': '0', 'tx-late-collision': '0', 'tx-drop': '0', 'tx-rx-64': '13318772',
        # 'tx-rx-65-127': '20979172934', 'tx-rx-128-255': '2202001769', 'tx-rx-256-511': '1194620381', 'tx-rx-512-1023': '1250729860',
        # 'tx-rx-1024-1518': '55351848828', 'rx-unicast': '24732296476', 'tx-unicast': '59818934528', 'running': 'true',
        # 'disabled': 'false', 'comment': 'SOHO'}
        self.ethers = self.rb.element("/interface/ethernet/", auto_load=True)

        # vlans
        # example:
        # {'.id': '*12', 'name': 'vlan154-air_kosowo', 'mtu': '1500', 'l2mtu': '1588', 'mac-address': 'DC:2C:6E:0F:57:67',
        # 'arp': 'enabled', 'arp-timeout': 'auto', 'loop-protect': 'default', 'loop-protect-status': 'off',
        # 'loop-protect-send-interval': '5s', 'loop-protect-disable-time': '5m', 'vlan-id': '154', 'interface': 'ether9',
        # 'use-service-tag': 'false', 'running': 'true', 'disabled': 'false'}, {'.id': '*18', 'name': 'vlan222', 'mtu': '1500',
        # 'l2mtu': '1588', 'mac-address': 'DC:2C:6E:0F:57:67', 'arp': 'enabled', 'arp-timeout': 'auto', 'loop-protect': 'default',
        # 'loop-protect-status': 'off', 'loop-protect-send-interval': '5s', 'loop-protect-disable-time': '5m', 'vlan-id': '222',
        # 'interface': 'ether9', 'use-service-tag': 'false', 'running': 'true', 'disabled': 'false'}
        self.vlans = self.rb.element("/interface/vlan/", auto_load=True)

        # ospf-neighbors
        # example:
        # {'.id': '*30C5B8', 'instance': 'default', 'router-id': '10.1.68.154', 'address': '10.0.68.226', 'interface': 'vlan154-air_kosowo',
        # 'priority': '1', 'dr-address': '0.0.0.0', 'backup-dr-address': '0.0.0.0', 'state': 'Full', 'state-changes': '8',
        # 'ls-retransmits': '0', 'ls-requests': '0', 'db-summaries': '0', 'adjacency': '14w6d14h42m11s'}
        self.neighbors = self.rb.element("/routing/ospf/neighbor/", auto_load=True)

        # address
        # example:
        # {'.id': '*A', 'address': '10.0.68.225/30', 'network': '10.0.68.224', 'interface': 'vlan154-air_kosowo',
        # 'actual-interface': 'vlan154-air_kosowo', 'invalid': 'false', 'dynamic': 'false', 'disabled': 'false'}
        self.addresses = self.rb.element("/ip/address/", auto_load=True)

        # ppp
        # example
        # {'.id': '*80000077', 'name': '48:8F:5A:7C:13:3A', 'service': 'pppoe', 'caller-id': 'B8:69:F4:B7:52:BB',
        # 'address': '10.30.246.13', 'uptime': '3d17h14m31s', 'encoding': '', 'session-id': '0x81300077', 'limit-bytes-in': '0',
        # 'limit-bytes-out': '0', 'radius': 'true'}
        self.ppp = self.rb.element("/ppp/active/", auto_load=True)

    def get_data(self) -> RBData:
        """Returns RBData objects."""
        out = RBData()
        # routers
        for item in self._build_routers_data():
            out.routers.append(item)

        return out


class RouterBoardCollector7(IRouterBoardCollector, __Collector):
    """Collector class for ROS 7."""

    def collect(self) -> None:
        """Fire up collector procedures."""

        if not self.rb:
            return None

        # interfaces
        # example:
        # {'.id': '*2', 'name': 'sfp-sfpplus2', 'default-name': 'sfp-sfpplus2', 'mtu': '1500', 'l2mtu': '1580', 'mac-address': '64:D1:54:3B:20:87',
        # 'orig-mac-address': '64:D1:54:3B:20:87', 'arp': 'enabled', 'arp-timeout': 'auto', 'loop-protect': 'default', 'loop-protect-status': 'off',
        # 'loop-protect-send-interval': '5s', 'loop-protect-disable-time': '5m', 'auto-negotiation': 'true', 'advertise': '1000M-full,10000M-full',
        # 'tx-flow-control': 'off', 'rx-flow-control': 'off', 'bandwidth': 'unlimited/unlimited', 'sfp-rate-select': 'high',
        # 'sfp-shutdown-temperature': '95', 'driver-rx-byte': '2653989249963585', 'driver-rx-packet': '4258597579513',
        # 'driver-tx-byte': '736967427358593', 'driver-tx-packet': '3291524111452', 'rx-bytes': '2661690913444462', 'rx-packet': '2433236930193',
        # 'rx-too-short': '0', 'rx-64': '48350420886', 'rx-65-127': '342172077400', 'rx-128-255': '57102386351', 'rx-256-511': '37087502813',
        # 'rx-512-1023': '33888927492', 'rx-1024-1518': '1912048884034', 'rx-1519-max': '2586731217', 'rx-too-long': '0',
        # 'rx-broadcast': '2603251807', 'rx-pause': '0', 'rx-multicast': '2863955093', 'rx-fcs-error': '0', 'rx-align-error': '0',
        # 'rx-overflow': '0', 'rx-length-error': '0', 'rx-code-error': '0', 'rx-jabber': '0', 'rx-ip-header-checksum-error': '0',
        # 'rx-tcp-checksum-error': '0', 'rx-udp-checksum-error': '0', 'tx-bytes': '742565666175825', 'tx-packet': '1736745950222',
        # 'tx-64': '100846746263', 'tx-65-127': '1071026858665', 'tx-128-255': '63678629009', 'tx-256-511': '28625710225',
        # 'tx-512-1023': '24084519187', 'tx-1024-1518': '443480477106', 'tx-1519-max': '5003009767', 'tx-broadcast': '1874135',
        # 'tx-pause': '0', 'tx-multicast': '257942994', 'tx-underrun': '0', 'tx-excessive-collision': '0', 'tx-multiple-collision': '0',
        # 'tx-single-collision': '0', 'tx-deferred': '0', 'tx-late-collision': '0', 'tx-fcs-error': '63', 'tx-carrier-sense-error': '0',
        # 'running': 'true', 'disabled': 'false'}
        self.ethers = self.rb.element("/interface/ethernet/", auto_load=True)

        # vlans
        # example:
        # {'.id': '*1D', 'name': 'vlan165-dude', 'mtu': '1500', 'l2mtu': '1576', 'mac-address': '64:D1:54:3B:20:87', 'arp': 'enabled',
        # 'arp-timeout': 'auto', 'loop-protect': 'default', 'loop-protect-status': 'off', 'loop-protect-send-interval': '5s',
        # 'loop-protect-disable-time': '5m', 'vlan-id': '165', 'interface': 'sfp-sfpplus2', 'use-service-tag': 'false', 'running': 'true',
        # 'disabled': 'false'}
        self.vlans = self.rb.element("/interface/vlan/", auto_load=True)

        # ospf-neighbors
        # example:
        # {'.id': '*F3FED9A8', 'instance': 'ospf-lan', 'area': 'ospf-area-backbone', 'address': '10.0.0.74', 'router-id': '10.1.0.165',
        # 'state': 'Full', 'state-changes': '4', 'ls-retransmits': '2', 'adjacency': '1h49m55s', 'timeout': '32s', 'dynamic': 'true'}
        self.neighbors = self.rb.element("/routing/ospf/neighbor/", auto_load=True)

        # address
        # example:
        # {'.id': '*25', 'address': '10.0.0.73/30', 'network': '10.0.0.72', 'interface': 'vlan165-dude', 'actual-interface': 'vlan165-dude',
        # 'invalid': 'false', 'dynamic': 'false', 'disabled': 'false'}
        self.addresses = self.rb.element("/ip/address/", auto_load=True)

        # ppp
        # example
        # {'.id': '*80000068', 'name': 'D4:CA:6D:D5:82:E3', 'service': 'pppoe', 'caller-id': 'B4:FB:E4:BE:86:DB',
        # 'address': '10.30.214.21', 'uptime': '5d18h59m42s', 'encoding': '', 'session-id': '0x81000068', 'limit-bytes-in': '0',
        # 'limit-bytes-out': '0', 'radius': 'true'}
        self.ppp = self.rb.element("/ppp/active/", auto_load=True)

    def get_data(self) -> RBData:
        """Returns RBData objects."""
        out = RBData()
        # routers
        for item in self._build_routers_data():
            out.routers.append(item)

        return out


# #[EOF]#######################################################################

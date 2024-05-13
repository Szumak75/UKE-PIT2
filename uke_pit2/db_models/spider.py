# -*- coding: utf-8 -*-
"""
  spider.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 18.04.2024, 17:14:50
  
  Purpose: 
"""

from sqlalchemy import Boolean, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from jsktoolbox.netaddresstool.ipv4 import Address
from uke_pit2.base import LmsBase


class TRouter(LmsBase):
    """Mapping class for routers data."""

    __tablename__: str = "uke_pit_routers"

    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, autoincrement=True
    )
    # router identification IP address as int
    router_id: Mapped[int] = mapped_column(
        Integer, unique=True, nullable=False, index=True
    )
    last_update: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"id='{self.id}',"
            f"router_id='{Address(self.router_id)}',"
            f"last_update='{self.last_update}'"
            ")"
        )


class TCustomer(LmsBase):
    """Mapping class for customers data."""

    __tablename__: str = "uke_pit_customers"

    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, autoincrement=True
    )
    # router record id
    rid: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(18), nullable=False, index=True)
    ip: Mapped[int] = mapped_column(Integer, nullable=False)
    last_update: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"id='{self.id}',"
            f"rid='{self.rid}',"
            f"name='{self.name}',"
            f"ip='{Address(self.ip)}',"
            f"last_update='{self.last_update}'"
            ")"
        )


class TConnection(LmsBase):
    """Mapping class for inter routers connection."""

    __tablename__: str = "uke_pit_connections"

    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, autoincrement=True
    )
    rid: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    vlan_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True, default=1, server_default=text("1")
    )
    network: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    last_update: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"id='{self.id}',"
            f"rid='{self.rid}',"
            f"vlan_id='{self.vlan_id}',"
            f"network='{Address(self.network)}',"
            f"last_update='{self.last_update}'"
            ")"
        )


class TInterfaceName(LmsBase):
    """Mapping class for network interface name."""

    __tablename__: str = "uke_pit_if_name"

    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(" f"id='{self.id}'," f"name='{self.name}'" ")"
        )


class TInterface(LmsBase):
    """Mapping class for connection interface."""

    __tablename__: str = "uke_pit_if"

    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, autoincrement=True
    )
    # connection id
    cid: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    # interface name id
    if_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    last_update: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"id='{self.id}',"
            f"cid='{self.cid}',"
            f"if_id='{self.if_id}'"
            f"last_update='{self.last_update}',"
            ")"
        )


class TNodeAssignment(LmsBase):
    """Mapping class for assigning routers to nodes."""

    __tablename__: str = "uke_pit_assignment"

    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, autoincrement=True
    )
    # lms netnode.id
    nid: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    # router.id
    rid: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"id='{self.id}',"
            f"nid='{self.nid}',"
            f"rid='{self.rid}'"
            ")"
        )


class TDivisions(LmsBase):
    """Mapping class for select main lms division."""

    __tablename__: str = "uke_pit_divisions"

    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, autoincrement=True
    )
    # lms divisions.id
    did: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    # division identification string
    ident: Mapped[str] = mapped_column(String(100), nullable=True)
    # main flag
    main: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"id='{self.id}',"
            f"nid='{self.did}',"
            f"rid='{self.main}'"
            ")"
        )


class TForeign(LmsBase):
    """Mapping class for foreign."""

    __tablename__: str = "uke_pit_foreign"

    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tin: Mapped[str] = mapped_column(String(10), nullable=False)
    # foreign identification string
    ident: Mapped[str] = mapped_column(String(100), nullable=False)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"id='{self.id}',"
            f"name='{self.name}',"
            f"tin='{self.tin}',"
            f"ident='{self.ident}'"
            ")"
        )


# #[EOF]#######################################################################

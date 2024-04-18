# -*- coding: utf-8 -*-
"""
  spider.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 18.04.2024, 17:14:50
  
  Purpose: 
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql import (
    DECIMAL,
    INTEGER,
    SMALLINT,
    TEXT,
    TINYINT,
    VARCHAR,
)

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
            f"last_update='{self.last_update}',"
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
            f"name='{self.name}'"
            f"ip='{Address(self.ip)}',"
            f"last_update='{self.last_update}',"
            ")"
        )


# #[EOF]#######################################################################

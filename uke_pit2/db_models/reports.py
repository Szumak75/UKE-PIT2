# -*- coding: utf-8 -*-
"""
  reports.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 27.08.2024, 10:16:24
  
  Purpose: Database model classes for reports.
"""

import time
import datetime

from typing import Dict, List, Tuple, Any, TypeVar, Optional

from crypt import crypt

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, Integer, Boolean, String, func, text, and_
from sqlalchemy.orm import Mapped, mapped_column, Query, relationship, aliased
from sqlalchemy.dialects.mysql import (
    BIGINT,
    BINARY,
    BIT,
    BLOB,
    BOOLEAN,
    CHAR,
    DATE,
    DATETIME,
    DECIMAL,
    DOUBLE,
    ENUM,
    FLOAT,
    INTEGER,
    LONGBLOB,
    LONGTEXT,
    MEDIUMBLOB,
    MEDIUMINT,
    MEDIUMTEXT,
    NCHAR,
    NUMERIC,
    NVARCHAR,
    REAL,
    SET,
    SMALLINT,
    TEXT,
    TIME,
    TIMESTAMP,
    TINYBLOB,
    TINYINT,
    TINYTEXT,
    VARBINARY,
    VARCHAR,
    YEAR,
)

from jsktoolbox.datetool import DateTime
from jsktoolbox.netaddresstool.ipv4 import Address

from uke_pit2.base import LmsBase


class LmsDivision(LmsBase):
    __tablename__: str = "divisions"

    id: Mapped[int] = mapped_column(
        INTEGER(11), primary_key=True, nullable=False, autoincrement=True
    )
    shortname: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, default="")
    name: Mapped[str] = mapped_column(TEXT(), nullable=False)
    ten: Mapped[str] = mapped_column(VARCHAR(128), nullable=False, default="")
    # regon: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, default="")
    rbe: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, default="")
    # rbename: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, default="")
    # telecomnumber: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, default="")
    # account: Mapped[str] = mapped_column(VARCHAR(48), nullable=False, default="")
    # inv_header: Mapped[str] = mapped_column(TEXT(), nullable=False)
    # inv_footer: Mapped[str] = mapped_column(TEXT(), nullable=False)
    # inv_author: Mapped[str] = mapped_column(TEXT(), nullable=False)
    # inv_paytime: Mapped[int] = mapped_column(SMALLINT(6), default=None)
    # inv_paytype: Mapped[int] = mapped_column(SMALLINT(6), default=None)
    # description: Mapped[str] = mapped_column(TEXT(), nullable=False)
    # status: Mapped[int] = mapped_column(TINYINT(1), nullable=False, default=0)
    # tax_office_code: Mapped[str] = mapped_column(VARCHAR(8), default=None)
    # address_id: Mapped[int] = mapped_column(ForeignKey("addresses.id"))
    # inv_cplace: Mapped[str] = mapped_column(TEXT(), nullable=False)
    # PRIMARY KEY (`id`),
    # UNIQUE KEY `shortname` (`shortname`),
    # KEY `divisions_address_id_fk` (`address_id`),
    # CONSTRAINT `divisions_address_id_fk` FOREIGN KEY (`address_id`) REFERENCES `addresses` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
    # address: Mapped["Address"] = relationship("Address")
    map: Mapped["Division"] = relationship("Division")

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id='{self.id}', "
            f"shortname='{self.shortname}', "
            f"name='{self.name}', "
            f"ten='{self.ten.replace('-','')}', "
            # f"regon='{self.regon}', "
            f"rbe='{self.rbe}', "
            # f"rbename='{self.rbename}', "
            # f"telecomnumber='{self.telecomnumber}', "
            # f"account='{self.account}', "
            # f"inv_header='{self.inv_header}', "
            # f"inv_footer='{self.inv_footer}', "
            # f"inv_author='{self.inv_author}', "
            # f"inv_paytime='{self.inv_paytime}', "
            # f"inv_paytype='{self.inv_paytype}', "
            # f"inv_cplace='{self.inv_cplace}', "
            # f"description='{self.description}', "
            # f"status='{self.status}', "
            # f"tax_office_code='{self.tax_office_code}', "
            # f"address_id='{self.address_id}', "
            # f"address='{self.address}' "
            f"map='{self.map}'"
            ")"
        )


class Division(LmsBase):
    """Mapping class for select main lms division."""

    __table_args__ = {"extend_existing": True}
    __tablename__: str = "uke_pit_divisions"

    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, autoincrement=True
    )
    # lms divisions.id
    # did: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    did: Mapped[int] = mapped_column(ForeignKey("divisions.id"))
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
            f"did='{self.did}',"
            f"main='{self.main}'"
            ")"
        )


# #[EOF]#######################################################################

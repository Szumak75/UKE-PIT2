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
from sqlalchemy.ext.hybrid import hybrid_property

from jsktoolbox.datetool import DateTime
from jsktoolbox.netaddresstool.ipv4 import Address

from uke_pit2.base import LmsBase


class LmsLocationState(LmsBase):
    __tablename__: str = "location_states"

    # `id` int(11) NOT NULL AUTO_INCREMENT,
    id: Mapped[int] = mapped_column(
        INTEGER(11), primary_key=True, nullable=False, autoincrement=True
    )
    # `ident` varchar(8) COLLATE utf8_polish_ci NOT NULL,
    ident: Mapped[str] = mapped_column(VARCHAR(8), nullable=False)
    # `name` varchar(64) COLLATE utf8_polish_ci NOT NULL,
    name: Mapped[str] = mapped_column(VARCHAR(64), unique=True, nullable=False)
    # PRIMARY KEY (`id`),
    # UNIQUE KEY `name` (`name`)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id='{self.id}', "
            f"ident='{self.ident}', "
            f"name='{self.name}' "
            ") "
        )


class LmsLocationDistrict(LmsBase):
    __tablename__: str = "location_districts"

    # `id` int(11) NOT NULL AUTO_INCREMENT,
    id: Mapped[int] = mapped_column(
        INTEGER(11), primary_key=True, nullable=False, autoincrement=True
    )
    # `name` varchar(64) COLLATE utf8_polish_ci NOT NULL,
    name: Mapped[str] = mapped_column(VARCHAR(64), nullable=False)
    # `ident` varchar(8) COLLATE utf8_polish_ci NOT NULL,
    ident: Mapped[str] = mapped_column(VARCHAR(8), nullable=False)
    # `stateid` int(11) NOT NULL,
    stateid: Mapped[int] = mapped_column(ForeignKey("location_states.id"))
    # PRIMARY KEY (`id`),
    # UNIQUE KEY `stateid` (`stateid`,`name`),
    # CONSTRAINT `location_districts_ibfk_1` FOREIGN KEY (`stateid`) REFERENCES `location_states` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
    state: Mapped["LmsLocationState"] = relationship("LmsLocationState")

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(id='{self.id}', "
            f"name='{self.name}', "
            f"ident='{self.ident}', "
            f"stateid='{self.stateid}', "
            f"state='{self.state}' "
            ") "
        )


class LmsLocationBorough(LmsBase):
    __tablename__: str = "location_boroughs"

    # `id` int(11) NOT NULL AUTO_INCREMENT,
    id: Mapped[int] = mapped_column(
        INTEGER(11), primary_key=True, nullable=False, autoincrement=True
    )
    # `name` varchar(64) COLLATE utf8_polish_ci NOT NULL,
    name: Mapped[str] = mapped_column(VARCHAR(64), nullable=False)
    # `ident` varchar(8) COLLATE utf8_polish_ci NOT NULL,
    ident: Mapped[str] = mapped_column(VARCHAR(8), nullable=False)
    # `districtid` int(11) NOT NULL,
    districtid: Mapped[int] = mapped_column(ForeignKey("location_districts.id"))
    # `type` smallint(6) NOT NULL,
    type: Mapped[int] = mapped_column(SMALLINT(6), nullable=False)
    # PRIMARY KEY (`id`),
    # UNIQUE KEY `districtid` (`districtid`,`name`,`type`),
    # CONSTRAINT `location_boroughs_ibfk_1` FOREIGN KEY (`districtid`) REFERENCES `location_districts` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
    district: Mapped["LmsLocationDistrict"] = relationship("LmsLocationDistrict")

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id='{self.id}', "
            f"name='{self.name}', "
            f"ident='{self.ident}', "
            f"districtid='{self.districtid}', "
            f"type='{self.type}', "
            f"district='{self.district}' "
            ") "
        )


class LmsLocationCity(LmsBase):
    __tablename__: str = "location_cities"

    # `id` int(11) NOT NULL AUTO_INCREMENT,
    id: Mapped[int] = mapped_column(
        INTEGER(11), primary_key=True, nullable=False, autoincrement=True
    )
    # `ident` varchar(8) COLLATE utf8_polish_ci NOT NULL,
    ident: Mapped[str] = mapped_column(VARCHAR(8), nullable=False)
    # `name` varchar(64) COLLATE utf8_polish_ci NOT NULL,
    name: Mapped[str] = mapped_column(VARCHAR(64), nullable=False)
    # `cityid` int(11) DEFAULT NULL,
    cityid: Mapped[int] = mapped_column(INTEGER(11), index=True, default=None)
    # `boroughid` int(11) DEFAULT NULL,
    boroughid: Mapped[int] = mapped_column(ForeignKey("location_boroughs.id"))
    # PRIMARY KEY (`id`),
    # KEY `cityid` (`cityid`),
    # KEY `boroughid` (`boroughid`,`name`),
    # CONSTRAINT `location_cities_ibfk_1` FOREIGN KEY (`boroughid`) REFERENCES `location_boroughs` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
    borough: Mapped["LmsLocationBorough"] = relationship("LmsLocationBorough")

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id='{self.id}', "
            f"ident='{self.ident}', "
            f"name='{self.name}', "
            f"cityid='{self.cityid}', "
            f"boroughid='{self.boroughid}', "
            f"borough='{self.borough}' "
            ") "
        )


class LmsLocationStreet(LmsBase):
    __tablename__: str = "location_streets"

    # `id` int(11) NOT NULL AUTO_INCREMENT,
    id: Mapped[int] = mapped_column(
        INTEGER(11), primary_key=True, nullable=False, autoincrement=True
    )
    # `name` varchar(128) COLLATE utf8_polish_ci NOT NULL,
    name: Mapped[str] = mapped_column(VARCHAR(128), nullable=False)
    # `name2` varchar(128) COLLATE utf8_polish_ci DEFAULT NULL,
    name2: Mapped[str] = mapped_column(VARCHAR(128), default=None)
    # `ident` varchar(8) COLLATE utf8_polish_ci NOT NULL,
    ident: Mapped[str] = mapped_column(VARCHAR(8), nullable=False)
    # `typeid` int(11) DEFAULT NULL,
    typeid: Mapped[int] = mapped_column(ForeignKey("location_street_types.id"))
    # `cityid` int(11) NOT NULL,
    cityid: Mapped[int] = mapped_column(ForeignKey("location_cities.id"))
    # PRIMARY KEY (`id`),
    # UNIQUE KEY `cityid` (`cityid`,`name`,`ident`),
    # KEY `typeid` (`typeid`),
    # CONSTRAINT `location_streets_ibfk_1` FOREIGN KEY (`typeid`) REFERENCES `location_street_types` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
    street_type: Mapped["LmsLocationStreetType"] = relationship("LmsLocationStreetType")
    # CONSTRAINT `location_streets_ibfk_2` FOREIGN KEY (`cityid`) REFERENCES `location_cities` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
    city: Mapped["LmsLocationCity"] = relationship("LmsLocationCity")

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id='{self.id}', "
            f"name='{self.name}', "
            f"name2='{self.name2}', "
            f"ident='{self.ident}', "
            f"typeid='{self.typeid}', "
            f"cityid='{self.cityid}', "
            f"street_type='{self.street_type}', "
            f"city='{self.city}' "
            ") "
        )


class LmsLocationStreetType(LmsBase):
    __tablename__: str = "location_street_types"

    # `id` int(11) NOT NULL AUTO_INCREMENT,
    id: Mapped[int] = mapped_column(
        INTEGER(11), primary_key=True, nullable=False, autoincrement=True
    )
    # `name` varchar(8) COLLATE utf8_polish_ci NOT NULL,
    name: Mapped[str] = mapped_column(VARCHAR(8), nullable=False)
    # PRIMARY KEY (`id`)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id='{self.id}', " f"name='{self.name}' ) "


class LmsCountry(LmsBase):
    __tablename__: str = "countries"

    # `id` int(11) NOT NULL AUTO_INCREMENT,
    id: Mapped[int] = mapped_column(
        INTEGER(11), primary_key=True, nullable=False, autoincrement=True
    )
    # `name` varchar(255) COLLATE utf8_polish_ci NOT NULL DEFAULT '',
    name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, default="")
    # PRIMARY KEY (`id`),
    # UNIQUE KEY `name` (`name`)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id='{self.id}', " f"name='{self.name}' ) "


class LmsAddress(LmsBase):
    __tablename__: str = "addresses"

    # `id` int(11) NOT NULL AUTO_INCREMENT,
    id: Mapped[int] = mapped_column(
        INTEGER(11), primary_key=True, nullable=False, autoincrement=True
    )
    # `name` text COLLATE utf8_polish_ci,
    name: Mapped[str] = mapped_column(TEXT())
    # `state` varchar(64) COLLATE utf8_polish_ci DEFAULT NULL,
    state: Mapped[str] = mapped_column(VARCHAR(64), default=None)
    # `state_id` int(11) DEFAULT NULL,
    state_id: Mapped[int] = mapped_column(ForeignKey("location_states.id"))
    # `city` varchar(100) COLLATE utf8_polish_ci DEFAULT NULL,
    city: Mapped[str] = mapped_column(VARCHAR(100), default=None)
    # `city_id` int(11) DEFAULT NULL,
    city_id: Mapped[int] = mapped_column(ForeignKey("location_cities.id"))
    # `postoffice` varchar(32) COLLATE utf8_polish_ci DEFAULT NULL,
    postoffice: Mapped[str] = mapped_column(VARCHAR(32), default=None)
    # `street` varchar(255) COLLATE utf8_polish_ci DEFAULT NULL,
    street: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    # `street_id` int(11) DEFAULT NULL,
    street_id: Mapped[int] = mapped_column(ForeignKey("location_streets.id"))
    # `zip` varchar(10) COLLATE utf8_polish_ci DEFAULT NULL,
    zip: Mapped[str] = mapped_column(VARCHAR(10), default=None)
    # `country_id` int(11) DEFAULT NULL,
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"))
    # `house` varchar(20) COLLATE utf8_polish_ci DEFAULT NULL,
    house: Mapped[str] = mapped_column(VARCHAR(20), default=None)
    # `flat` varchar(20) COLLATE utf8_polish_ci DEFAULT NULL,
    flat: Mapped[str] = mapped_column(VARCHAR(20), default=None)
    # PRIMARY KEY (`id`),
    # KEY `addresses_state_id_fk` (`state_id`),
    # KEY `addresses_city_id_fk` (`city_id`),
    # KEY `addresses_street_id_fk` (`street_id`),
    # KEY `addresses_country_id_fk` (`country_id`),
    # CONSTRAINT `addresses_city_id_fk` FOREIGN KEY (`city_id`) REFERENCES `location_cities` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
    location_city: Mapped["LmsLocationCity"] = relationship("LmsLocationCity")
    # CONSTRAINT `addresses_country_id_fk` FOREIGN KEY (`country_id`) REFERENCES `countries` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
    location_country: Mapped["LmsCountry"] = relationship("LmsCountry")
    # CONSTRAINT `addresses_state_id_fk` FOREIGN KEY (`state_id`) REFERENCES `location_states` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
    location_state: Mapped["LmsLocationState"] = relationship("LmsLocationState")
    # CONSTRAINT `addresses_street_id_fk` FOREIGN KEY (`street_id`) REFERENCES `location_streets` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
    location_street: Mapped["LmsLocationStreet"] = relationship("LmsLocationStreet")

    @hybrid_property
    def terc(self) -> Optional[str]:
        """Return TERC string."""
        if self.location_city:
            city: LmsLocationCity = self.location_city
            if city.borough:
                borough: LmsLocationBorough = city.borough
                if borough.district:
                    district: LmsLocationDistrict = borough.district
                    if district.state:
                        state: LmsLocationState = district.state
                        tmp = f"{state.ident}{district.ident}{borough.ident}{borough.type}"
                        if len(tmp) == 7:
                            return tmp
        return None

    @hybrid_property
    def simc(self) -> Optional[str]:
        """Return SIMC string."""
        if self.location_city:
            city: LmsLocationCity = self.location_city
            tmp = f"{city.ident}"
            if len(tmp) == 7:
                return tmp
        return None

    @hybrid_property
    def ulic(self) -> Optional[str]:
        """Return ULIC string."""
        if self.location_street:
            street: LmsLocationStreet = self.location_street
            tmp = f"{street.ident}"
            if len(tmp) == 5:
                return tmp
        return None

    @hybrid_property
    def nr(self) -> Optional[str]:
        """Return NR string."""
        if self.house and str(self.house).lower() != "b/n":
            return self.house
        return None

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id='{self.id}', "
            f"name='{self.name}', "
            f"state='{self.state}', "
            f"state_id='{self.state_id}', "
            f"city='{self.city}', "
            f"city_id='{self.city_id}', "
            f"postoffice='{self.postoffice}', "
            f"street='{self.street}', "
            f"street_id='{self.street_id}', "
            f"zip='{self.zip}', "
            f"country_id='{self.country_id}', "
            f"house='{self.house}', "
            f"flat='{self.flat}', "
            f"location_country='{self.location_country}', "
            f"location_state='{self.location_state}', "
            f"location_city='{self.location_city}', "
            f"location_street='{self.location_street}' "
            ") "
        )


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


## Nodes
class LmsNetNode(LmsBase):
    __tablename__: str = "netnodes"

    id: Mapped[int] = mapped_column(
        INTEGER(11), primary_key=True, nullable=False, autoincrement=True
    )
    name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    type: Mapped[int] = mapped_column(TINYINT(4), default=0)
    # invprojectid: Mapped[int] = mapped_column(INTEGER(11), default=None)
    status: Mapped[int] = mapped_column(TINYINT(4), default=0)
    longitude: Mapped[float] = mapped_column(DECIMAL(10, 6), default=None)
    latitude: Mapped[float] = mapped_column(DECIMAL(10, 6), default=None)
    ownership: Mapped[int] = mapped_column(TINYINT(1), default=0)
    # coowner: Mapped[str] = mapped_column(VARCHAR(255), default="")
    uip: Mapped[int] = mapped_column(TINYINT(1), default=0)
    miar: Mapped[int] = mapped_column(TINYINT(1), default=0)
    createtime: Mapped[int] = mapped_column(INTEGER(11), default=None)
    # lastinspectiontime: Mapped[int] = mapped_column(INTEGER(11), default=None)
    admcontact: Mapped[str] = mapped_column(TEXT())
    # divisionid: Mapped[int] = mapped_column(ForeignKey("divisions.id"))
    # address_id: Mapped[int] = mapped_column(ForeignKey("addresses.id"))
    info: Mapped[str] = mapped_column(TEXT())
    # PRIMARY KEY (`id`),
    # KEY `netnodes_address_id_fkey` (`address_id`),
    # KEY `invprojectid` (`invprojectid`),
    # KEY `divisionid` (`divisionid`),
    # CONSTRAINT `netnodes_address_id_fkey` FOREIGN KEY (`address_id`) REFERENCES `addresses` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
    # address: Mapped["Address"] = relationship("Address")
    # CONSTRAINT `netnodes_ibfk_1` FOREIGN KEY (`invprojectid`) REFERENCES `invprojects` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
    # CONSTRAINT `netnodes_ibfk_2` FOREIGN KEY (`divisionid`) REFERENCES `divisions` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
    # division: Mapped["Division"] = relationship("Division")

    def __repr__(self) -> str:
        return (
            f"NetNode(id='{self.id}', "
            f"name='{self.name}', "
            f"type='{self.type}', "
            # f"invprojectid='{self.invprojectid}', "
            f"status='{self.status}', "
            f"longitude='{self.longitude}', "
            f"latitude='{self.latitude}', "
            f"ownership='{self.ownership}', "
            # f"coowner='{self.coowner}', "
            f"uip='{self.uip}', "
            f"miar='{self.miar}', "
            f"createtime='{self.createtime}', "
            # f"lastinspectiontime='{self.lastinspectiontime}', "
            f"admcontact='{self.admcontact}', "
            # f"divisionid='{self.divisionid}', "
            # f"address_id='{self.address_id}', "
            f"info='{self.info}', "
            # f"address='{self.address}', "
            # f"division='{self.division}'"
            ")"
        )


class Foreign(LmsBase):
    """Mapping class for foreign."""

    __table_args__ = {"extend_existing": True}
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


class Router(LmsBase):
    """Mapping class for routers data."""

    __table_args__ = {"extend_existing": True}
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


class Customer(LmsBase):
    """Mapping class for customers data."""

    __table_args__ = {"extend_existing": True}
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


class Connection(LmsBase):
    """Mapping class for inter routers connection."""

    __table_args__ = {"extend_existing": True}
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


class NodeAssignment(LmsBase):
    """Mapping class for assigning routers to nodes."""

    __table_args__ = {"extend_existing": True}
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


# #[EOF]#######################################################################

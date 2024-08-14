# -*- coding: utf-8 -*-
"""
  models.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 25.02.2024, 09:51:47
  
  Purpose: Database models
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

from uke_pit2.db_models.spider import TRouter
from web_service.routes import db

###
# Types bound

TRouter = TypeVar("TRouter", bound="Router")


###
# LMS tables
class LmsUser(db.Model):
    __tablename__: str = "users"

    # Table schema
    id: Mapped[int] = mapped_column(
        INTEGER(11), primary_key=True, nullable=False, autoincrement=True
    )
    login: Mapped[str] = mapped_column(VARCHAR(32), nullable=False, default="")
    firstname: Mapped[str] = mapped_column(VARCHAR(64), nullable=False, default="")
    lastname: Mapped[str] = mapped_column(VARCHAR(64), nullable=False, default="")
    email: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, default="")
    phone: Mapped[str] = mapped_column(VARCHAR(32), nullable=False, default="")
    position: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, default="")
    rights: Mapped[str] = mapped_column(TEXT(), nullable=False)
    hosts: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, default="")
    passwd: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, default="")
    ntype: Mapped[int] = mapped_column(SMALLINT(6), default=None)
    lastlogindate: Mapped[int] = mapped_column(INTEGER(11), nullable=False, default=0)
    lastloginip: Mapped[str] = mapped_column(VARCHAR(16), nullable=False, default="")
    failedlogindate: Mapped[int] = mapped_column(INTEGER(11), nullable=False, default=0)
    failedloginip: Mapped[str] = mapped_column(VARCHAR(16), nullable=False, default="")
    deleted: Mapped[int] = mapped_column(TINYINT(1), nullable=False, default=0)
    passwdexpiration: Mapped[int] = mapped_column(
        INTEGER(11), nullable=False, default=0
    )
    passwdlastchange: Mapped[int] = mapped_column(
        INTEGER(11), nullable=False, default=0
    )
    access: Mapped[int] = mapped_column(TINYINT(1), nullable=False, default=1)
    accessfrom: Mapped[int] = mapped_column(INTEGER(11), nullable=False, default=0)
    accessto: Mapped[int] = mapped_column(INTEGER(11), nullable=False, default=0)
    settings: Mapped[str] = mapped_column(MEDIUMTEXT(), nullable=False)
    persistentsettings: Mapped[str] = mapped_column(MEDIUMTEXT(), nullable=False)

    # Instance methods
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id='{self.id}', "
            f"login='{self.login}', "
            f"firstname='{self.firstname}', "
            f"lastname='{self.lastname}', "
            f"email='{self.email}', "
            f"phone='{self.phone}', "
            f"position='{self.position}', "
            f"rights='{self.rights}', "
            f"hosts='{self.hosts}', "
            f"passwd='{self.passwd}', "
            f"ntype='{self.ntype}', "
            f"lastlogindate='{self.lastlogindate}', "
            f"lastloginip='{self.lastloginip}', "
            f"failedlogindate='{self.failedlogindate}', "
            f"failedloginip='{self.failedloginip}', "
            f"deleted='{self.deleted}', "
            f"passwdexpiration='{self.passwdexpiration}', "
            f"passwdlastchange='{self.passwdlastchange}', "
            f"access='{self.access}', "
            f"accessfrom='{self.accessfrom}', "
            f"accessto='{self.accessto}', "
            f"settings='{self.settings}', "
            f"persistentsettings='{self.persistentsettings}' ) "
        )

    # Class methods
    @classmethod
    def all(cls):
        return cls.query.all()

    @classmethod
    def find_by_login(cls, login: str) -> Query:
        return cls.query.filter(cls.login == login)

    @classmethod
    def check_login(cls, login: str, password: str) -> bool:
        out = cls.query.filter(cls.login == login).first()
        if out:
            passwd = out.passwd
            return passwd == crypt(password, passwd)
        return False


class LmsCustomer(db.Model):
    __tablename__: str = "customers"

    # Table schema
    id: Mapped[int] = mapped_column(
        INTEGER(11), primary_key=True, nullable=False, autoincrement=True
    )
    extid: Mapped[str] = mapped_column(VARCHAR(32), nullable=False, default="")
    lastname: Mapped[str] = mapped_column(VARCHAR(128), nullable=False, default="")
    name: Mapped[str] = mapped_column(VARCHAR(128), nullable=False, default="")
    status: Mapped[int] = mapped_column(SMALLINT(6), nullable=False, default=0)
    type: Mapped[int] = mapped_column(SMALLINT(6), nullable=False, default=0)
    ten: Mapped[str] = mapped_column(VARCHAR(16), nullable=False, default="")
    ssn: Mapped[str] = mapped_column(VARCHAR(11), nullable=False, default="")
    regon: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, default="")
    rbe: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, default="")
    icn: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, default="")
    rbename: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, default="")
    info: Mapped[str] = mapped_column(TEXT(), nullable=False)
    creationdate: Mapped[int] = mapped_column(INTEGER(11), nullable=False, default=0)
    moddate: Mapped[int] = mapped_column(INTEGER(11), nullable=False, default=0)
    notes: Mapped[str] = mapped_column(TEXT(), nullable=False)
    creatorid: Mapped[int] = mapped_column(INTEGER(11), default=None)
    modid: Mapped[int] = mapped_column(INTEGER(11), default=None)
    deleted: Mapped[int] = mapped_column(TINYINT(1), nullable=False, default=0)
    message: Mapped[str] = mapped_column(TEXT(), nullable=False)
    cutoffstop: Mapped[int] = mapped_column(INTEGER(11), nullable=False, default=0)
    consentdate: Mapped[int] = mapped_column(INTEGER(11), nullable=False, default=0)
    pin: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, default="0")
    invoicenotice: Mapped[int] = mapped_column(TINYINT(1), default=None)
    einvoice: Mapped[int] = mapped_column(TINYINT(1), default=None)
    divisionid: Mapped[int] = mapped_column(INTEGER(11), default=None)
    mailingnotice: Mapped[int] = mapped_column(TINYINT(1), default=None)
    paytype: Mapped[int] = mapped_column(SMALLINT(6), default=None)
    paytime: Mapped[int] = mapped_column(SMALLINT(6), nullable=False, default="-1")

    # Instance methods
    def __repr__(self) -> str:
        return (
            f"Customer(id='{self.id}', "
            f"extid='{self.extid}', "
            f"lastname='{self.lastname}', "
            f"name='{self.name}', "
            f"status='{self.status}', "
            f"type='{self.type}', "
            f"ten='{self.ten}', "
            f"ssn='{self.ssn}', "
            f"regon='{self.regon}', "
            f"rbe='{self.rbe}', "
            f"icn='{self.icn}', "
            f"rbename='{self.rbename}', "
            # f"info='{self.info}', "
            f"creationdate='{self.creationdate}', "
            f"moddate='{self.moddate}', "
            # f"notes='{self.notes}', "
            f"creatorid='{self.creatorid}', "
            f"modid='{self.modid}', "
            f"deleted='{self.deleted}', "
            # f"message='{self.message}', "
            f"cutoffstop='{self.cutoffstop}', "
            f"consentdate='{self.consentdate}', "
            f"pin='{self.pin}', "
            f"invoicenotice='{self.invoicenotice}', "
            f"einvoice='{self.einvoice}', "
            f"divisionid='{self.divisionid}', "
            f"mailingnotice='{self.mailingnotice}', "
            f"paytype='{self.paytype}', "
            f"paytime='{self.paytime}' ) "
        )


class LmsDivision(db.Model):
    __tablename__: str = "divisions"

    id: Mapped[int] = mapped_column(
        INTEGER(11), primary_key=True, nullable=False, autoincrement=True
    )
    shortname: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, default="")
    name: Mapped[str] = mapped_column(TEXT(), nullable=False)
    ten: Mapped[str] = mapped_column(VARCHAR(128), nullable=False, default="")
    regon: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, default="")
    rbe: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, default="")
    rbename: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, default="")
    telecomnumber: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, default="")
    account: Mapped[str] = mapped_column(VARCHAR(48), nullable=False, default="")
    # inv_header: Mapped[str] = mapped_column(TEXT(), nullable=False)
    # inv_footer: Mapped[str] = mapped_column(TEXT(), nullable=False)
    # inv_author: Mapped[str] = mapped_column(TEXT(), nullable=False)
    # inv_paytime: Mapped[int] = mapped_column(SMALLINT(6), default=None)
    # inv_paytype: Mapped[int] = mapped_column(SMALLINT(6), default=None)
    description: Mapped[str] = mapped_column(TEXT(), nullable=False)
    status: Mapped[int] = mapped_column(TINYINT(1), nullable=False, default=0)
    tax_office_code: Mapped[str] = mapped_column(VARCHAR(8), default=None)
    # address_id: Mapped[int] = mapped_column(ForeignKey("addresses.id"))
    # inv_cplace: Mapped[str] = mapped_column(TEXT(), nullable=False)
    # PRIMARY KEY (`id`),
    # UNIQUE KEY `shortname` (`shortname`),
    # KEY `divisions_address_id_fk` (`address_id`),
    # CONSTRAINT `divisions_address_id_fk` FOREIGN KEY (`address_id`) REFERENCES `addresses` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
    # address: Mapped["Address"] = relationship("Address")
    main: Mapped["Division"] = relationship("Division")

    def __repr__(self) -> str:
        return (
            f"Division(id='{self.id}', "
            f"shortname='{self.shortname}', "
            f"name='{self.name}', "
            f"ten='{self.ten}', "
            f"regon='{self.regon}', "
            f"rbe='{self.rbe}', "
            f"rbename='{self.rbename}', "
            f"telecomnumber='{self.telecomnumber}', "
            f"account='{self.account}', "
            # f"inv_header='{self.inv_header}', "
            # f"inv_footer='{self.inv_footer}', "
            # f"inv_author='{self.inv_author}', "
            # f"inv_paytime='{self.inv_paytime}', "
            # f"inv_paytype='{self.inv_paytype}', "
            # f"inv_cplace='{self.inv_cplace}', "
            f"description='{self.description}', "
            f"status='{self.status}', "
            f"tax_office_code='{self.tax_office_code}', "
            # f"address_id='{self.address_id}', "
            # f"address='{self.address}' "
            f"main='{self.main}'"
            ") "
        )

    @classmethod
    def get_division_list(cls) -> List[Tuple[int, str, int]]:
        """Returns division list."""
        out = []

        rows = cls.query.all()
        if rows:
            for item in rows:
                # print(item)
                if item.main is None:
                    out.append((item.id, item.name, 0))
                else:
                    out.append((item.id, item.name, int(item.main.main)))
        else:
            print("error")

        return out


class LmsNetNode(db.Model):
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

    # class methods
    @classmethod
    def all(cls) -> List[Any]:
        return cls.query.all()

    @classmethod
    def get_all_list(cls) -> List[Tuple[int, str]]:
        out: List[Tuple[int, str]] = []
        for item in cls.all():
            out.append((item.id, item.name))  # type: ignore
        return out


###
# UKE-PIT-Spider tables


class Router(db.Model):
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

    @classmethod
    def all(cls) -> List[TRouter]:
        """Gets all routers from database."""
        return cls.query.order_by(Router.router_id).all()

    @classmethod
    def get_all_list(cls) -> List[Tuple[int, str]]:
        out = []
        for item in cls.all():
            out.append((item.id, str(Address(item.router_id))))
        return out

    @classmethod
    def get_unbound_list(cls) -> List[Tuple[int, str]]:
        out = []
        rows = (
            cls.query.outerjoin(NodeAssignment, Router.id == NodeAssignment.rid)
            .filter(NodeAssignment.id == None)
            .order_by(Router.router_id)
            .all()
        )
        if rows:
            for item in rows:
                out.append((item.id, str(Address(item.router_id))))
        return out


class Connection(db.Model):
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


class NodeAssignment(db.Model):
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

    @classmethod
    def get_routers_list(cls, node_id: int) -> List[Tuple[int, str]]:
        out = []
        rows: List[Router] = (
            Router.query.join(NodeAssignment, Router.id == NodeAssignment.rid)
            .filter(NodeAssignment.nid == node_id)
            .order_by(Router.router_id)
            .all()
        )
        if rows:
            for item in rows:
                out.append((item.id, str(Address(item.router_id))))
        return out

    @classmethod
    def get_all(cls) -> List[Tuple[int, str]]:
        out = []
        rows: List[Router] = (
            Router.query.join(NodeAssignment, Router.id == NodeAssignment.rid)
            .order_by(Router.router_id)
            .all()
        )
        if rows:
            for item in rows:
                out.append((item.id, str(Address(item.router_id))))
        return out

    @classmethod
    def new(cls, node_id: str, router_id: str) -> "NodeAssignment":
        """Create new NodeAssignment object."""
        obj = NodeAssignment()
        obj.nid = int(node_id)
        obj.rid = int(router_id)
        return obj

    @classmethod
    def remove(cls, router_id: str) -> Optional["NodeAssignment"]:
        """Returns object for remove."""
        obj = cls.query.filter(NodeAssignment.rid == int(router_id)).first()
        return obj


class Division(db.Model):
    """Mapping class for select main lms division."""

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

    @classmethod
    def all(cls) -> List["Division"]:
        return cls.query.all()


class Foreign(db.Model):
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

    @classmethod
    def all(cls) -> List["Foreign"]:
        return cls.query.all()

    @classmethod
    def get_id(cls, id: str) -> Optional["Foreign"]:
        return cls.query.filter(cls.id == int(id)).first()


class Customer(db.Model):
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


class InterfaceName(db.Model):
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


class Interface(db.Model):
    """Mapping class for connection interface."""

    __tablename__: str = "uke_pit_if"

    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, autoincrement=True
    )
    # connection id
    cid: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    # interface name id
    # if_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    if_id: Mapped[int] = mapped_column(ForeignKey("uke_pit_if_name.id"))
    if_name: Mapped["InterfaceName"] = relationship()
    last_update: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"id='{self.id}',"
            f"cid='{self.cid}',"
            f"if_id='{self.if_id}',"
            f"if_name='{self.if_name}',"
            f"last_update='{self.last_update}',"
            ")"
        )


class Flow(db.Model):
    """Mapping class for connection flow definitions."""

    __tablename__: str = "uke_pit_flow"

    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, autoincrement=True
    )
    foreign_id: Mapped[int] = mapped_column(
        Integer, nullable=True, index=True, default=0, server_default=text("0")
    )
    node1_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True, default=0, server_default=text("0")
    )
    node2_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True, default=0, server_default=text("0")
    )
    speed: Mapped[int] = mapped_column(
        Integer, nullable=False, default=100, server_default=text("100")
    )
    medium_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True, default=0, server_default=text("0")
    )
    desc: Mapped[str] = mapped_column(String(30), nullable=True)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"id='{self.id}',"
            f"foreign_id='{self.foreign_id}',"
            f"node1_id='{self.node1_id}',"
            f"node2_id='{self.node2_id}',"
            f"medium_id='{self.medium_id}',"
            f"desc='{self.desc}'"
            ")"
        )


class Medium(db.Model):
    """Mapping class for medium dictionary."""

    __tablename__: str = "uke_pit_media"

    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(50))

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(" f"id='{self.id}'," f"name='{self.name}'" ")"
        )


# #[EOF]#######################################################################

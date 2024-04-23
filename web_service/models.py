# -*- coding: utf-8 -*-
"""
  models.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 25.02.2024, 09:51:47
  
  Purpose: Database models
"""

import time
import datetime

from typing import Dict, List, Any

from crypt import crypt

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, text
from sqlalchemy.orm import Mapped, mapped_column, Query
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

from web_service.routes import db


class User(db.Model):
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


class Customer(db.Model):
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


# #[EOF]#######################################################################

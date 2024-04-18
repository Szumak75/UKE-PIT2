# -*- coding: utf-8 -*-
"""
  update.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 18.04.2024, 16:05:44
  
  Purpose: 
"""
from typing import Tuple
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql import (
    DECIMAL,
    INTEGER,
    SMALLINT,
    TEXT,
    TINYINT,
    VARCHAR,
)

from uke_pit2.base import LmsBase


class TLastUpdate(LmsBase):
    """Mapping class for store information about updating timestamp."""

    __tablename__: str = "uke_pit_update"

    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, autoincrement=True
    )
    last_update: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"id='{self.id}',"
            f"last_update='{self.last_update}',"
            ")"
        )


# #[EOF]#######################################################################

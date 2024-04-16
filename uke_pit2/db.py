# -*- coding: utf-8 -*-
"""
  db.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 15.04.2024, 13:22:36
  
  Purpose: Classes for lms database connection
"""

from sqlalchemy import Subquery, create_engine, and_, or_, text, func
from sqlalchemy.orm import Session, DeclarativeBase
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine.base import Engine
from sqlalchemy.engine import URL, engine_from_config
from sqlalchemy.util import immutabledict


class LmsBase(DeclarativeBase):
    """Declarative Base class."""


# #[EOF]#######################################################################

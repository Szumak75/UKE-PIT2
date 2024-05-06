#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  spider.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 27.03.2024, 13:05:51
  
  Purpose: Spider for collecting infrastructure data
"""

import sys
from uke_pit2.main import SpiderApp

if __name__ == "__main__":
    app = SpiderApp()
    app.run()
    sys.exit(0)

# #[EOF]#######################################################################

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  wsgi.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 27.02.2024, 10:18:37
  
  Purpose: 
"""

from sanlms import routes

if __name__ == "__main__":
    routes.app.run()

# #[EOF]#######################################################################

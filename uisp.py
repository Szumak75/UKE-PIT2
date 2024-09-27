#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  uisp.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 27.09.2024, 13:32:51
  
  Purpose: Generate UISP node csv.
"""

import sys
from tool.nodes_uips import NodeApp

if __name__ == "__main__":
    app = NodeApp()
    app.run()
    sys.exit(0)

# #[EOF]#######################################################################

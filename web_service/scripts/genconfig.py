#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  genconfig.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 24.02.2024, 13:51:12
  
  Purpose: 
"""


import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from jsktoolbox.stringtool.crypto import SimpleCrypto

from web_service.tools import WebConfig

if __name__ == "__main__":
    conf = WebConfig()
    print("Updating the password to connect to the LMS database.")
    print("To interrupt the procedure, enter: EXIT")
    while True:
        password: str = input("Enter password: ")
        if password == "":
            print('Type: "EXIT" to break.')
        elif password == "EXIT":
            sys.exit(0)
        else:
            break
    if conf.salt is None:
        print("The 'salt' variable in the configuration file is not set correctly.")
        sys.exit(1)
    encrypt: str = SimpleCrypto.multiple_encrypt(conf.salt, password)
    conf.db_password = encrypt
    sys.exit(0)

# #[EOF]#######################################################################

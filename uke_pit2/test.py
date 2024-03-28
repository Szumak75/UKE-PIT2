# -*- coding: utf-8 -*-
"""
  test.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 28.03.2024, 15:34:21
  
  Purpose: string shuffler :)
"""

from random import shuffle

x: str = "Jeżeli jesteś w stanie to przeczytać to znaczy , że jesteś nienormalny"

ret = ""
for word in x.split():
    tmp = [*word]
    out = ""
    if len(tmp) > 2:
        tmp2 = tmp[1 : len(tmp) - 1]
        out = tmp[0]
        shuffle(tmp2)
        tmp3 = "".join(tmp2)
        out += f"{tmp3}{tmp[len(tmp)-1]}"
    else:
        out = "".join(tmp)
    if ret:
        ret += f" {out}"
    else:
        ret = out
print(ret)

# #[EOF]#######################################################################

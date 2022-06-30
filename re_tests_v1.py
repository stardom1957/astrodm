# -*- coding: utf-8 -*-
"""
Created on Thu Nov  4 22:20:15 2021

@author: dominique

quelques params :
re.IGNORECASE

mots clés Google : 'python re examples'
"""

import re

# longueur fixe du nom de la source pour recherche dans WDS Notes
WDS_SRC_LEN = 7

src = 'bu365'.upper()
print("src= '" + src + "'")

# RE écrite dans un raw string pour éviter '\' --> '\\'
# recherche du discoverer
str_re_pat = r'[A-Z]+'
obj_pat = re.compile(str_re_pat)
obj_match = obj_pat.match(src)
str_id_disc = obj_match.group(0)

print("str_id_disc= '" + str_id_disc + "'")

# recherche du no de système
str_re_pat = r'[0-9]+'
obj_pat = re.compile(str_re_pat)
obj_match = obj_pat.search(src)

try:
    str_no_sys = obj_match.group(0)
    print("str_no_sys= '" + str_no_sys + "'")

except AttributeError:
    print('no match pour no système')


# normalisation sur 7 car

nbr_espaces = WDS_SRC_LEN - len(str_id_disc) - len(str_no_sys)
print('nbr_espaces= ', nbr_espaces)

src_normalise = str_id_disc + ' ' * nbr_espaces + str_no_sys
print("src_normalise = '" + src_normalise + "'")
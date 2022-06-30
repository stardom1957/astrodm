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
WDS_SYSTEM_LEN = 7

systeme = 'bu365'.lower()
print("systeme= '" + systeme + "'")

# RE écrite dans un raw string pour éviter '\' --> '\\'
# recherche du discoverer
str_re_pat = r'[a-z]+'
obj_pat = re.compile(str_re_pat)
obj_match = obj_pat.match(systeme)
str_id_disc = obj_match.group(0)

print("str_id_disc= '" + str_id_disc + "'")

# recherche du no de système
str_re_pat = r'[0-9]+'
obj_pat = re.compile(str_re_pat)
obj_match = obj_pat.search(systeme)

try:
    str_no_sys = obj_match.group(0)
    print("str_no_sys= '" + str_no_sys + "'")

except AttributeError:
    print('no match pour no système')


# normalisation sur 7 car

nbr_espaces = WDS_SYSTEM_LEN - len(str_id_disc) - len(str_no_sys)
print('nbr_espaces= ', nbr_espaces)

systeme_normalise = str_id_disc.upper() + ' ' * nbr_espaces + str_no_sys
print("systeme_normalise = '" + systeme_normalise + "'")
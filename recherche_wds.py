# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 16:31:40 2020

@author: dominique
version 07
"""

###IMPORT

import sys
# insérer le chemin suivant dans sys.path pour trouver le package astro_doubles
if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesoutils as do


# %% PRINCIPAL
if __name__ == "__main__":
    ### saisir source
    print('Attention :')
    print(' H x n : entrer hx*')
    strSource = input("Nom de la source (max 7 car) : ")
    if len(strSource) > 7:
        print('Source non valide.')
        sys.exit()

    # pour toutes les paires strPaire = '*'
    strPaire = '*'
    do.info_src_wds(strSource, strPaire)
    
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
    # strSource = input("Nom de la source (Disc max 7 car | WDS id max 10 car) : ")
    print("Nom de 'Disc' max 7 car | 'WDS' id max 10 car)")
    strSource, strPaire = input("Disc | WDS , paire : ").split(',')
    print()

    # pour obtenir toutes les paires strPaire = '*'
    if strPaire == '':
        strPaire = '*'
    
    if strSource[0].isalpha() and len(strSource) <= 7:
        do.info_src_wds(strSource, strPaire.upper())
    elif strSource[0].isdigit() and len(strSource) == 10:
        res = do.rech_wds_id(strSource, strPaire.upper())
        if len(res) != 0:
            res[0].pprint(show_unit=True, max_width=140, max_lines=150)
    else:
        print('Entrée non acceptable!')
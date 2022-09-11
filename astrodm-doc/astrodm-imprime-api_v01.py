# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 06:40:14 2022

@author: dominique
"""
import sys

# insérer le chemin suivant dans sys.path pour trouver le package astrodm
if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesoutils as do

# %% PRINCIPAL
if __name__ == "__main__":
    # sortie vers fichier out.txt dans rép d'exécution
    ancien_stdout = sys.stdout
    f = open('astrodm-api.txt', 'w')
    sys.stdout = f
    print(help(do))
    sys.stdout = ancien_stdout
    f.close()

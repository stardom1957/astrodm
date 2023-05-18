# -*- coding: utf-8 -*-
"""
Created on Mon Feb 21 17:11:24 2022

@author: dominique
"""

import os
import pandas as pd
import sys
# insérer le chemin suivant dans sys.path pour trouver le package astrodm
if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesoutils as do
# %% INITIALISATIONS
### pandas options d'affichage des tables
pd.set_option('display.expand_frame_repr', True)
pd.set_option('display.colheader_justify', 'right')
pd.set_option('display.max_colwidth', 100)
pd.set_option('display.max_column', 15)
pd.set_option('display.width', 200)
pd.set_option('display.max_row', 10000)
pd.set_option("display.precision", 6)

if __name__ == '__main__':
    # demander sortie au terminal ou fichier
    sortie = 'terminal'
    rep = input("Sortie au terminal (t) ou  fichier (f) : ").upper()

    # nom complet fichier calibration e
    ncfmc = os.getcwd() + '/med/cal_e/master_calibrations_e.csv'

    if rep == 'F':
        # sortie vers fichier ./med/med-planification/....txt
        systag = do.produire_systag()
        # nom complet fichier sortie
        
        ncfs = os.getcwd() + '/med/med-planification/LISTES/astrodm-liste-master_cal_e' + systag + '.txt'
        ancien_stdout = sys.stdout
        f = open(ncfs, mode='w', encoding="utf-8")
        sys.stdout = f

    master_calibrations_e_df = pd.read_csv(ncfmc)
    
    print("\nListe du fichier des calibrations d'échelle.")
    print(master_calibrations_e_df)

    if rep == 'F':
        # rétablir stdout
        sys.stdout = ancien_stdout
        f.close()
        print("Sortie dans le fichier :\n  {0}".format(ncfs))
        
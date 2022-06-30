# -*- coding: utf-8 -*-
"""
Created on Mon Dec 28 22:10:56 2020

@author: dominique
"""

import pandas as pd
from tabulate import tabulate
import sys
import pickle
# insérer le chemin suivant dans sys.path pour trouver le package astrodm
if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesOutils as do
from astrodm import doublesListeProgrammes as dlp

if __name__ == "__main__":
    #df = pd.DataFrame(index=list('abcde'), data={'Abel': range(5), 'Cain': range(5)})
    #df.columns = pd.MultiIndex.from_arrays([df.columns, ['"', "'"]])
    #print(tabulate(df,headers='firstrow'))
    #print(tabulate(df,headers='keys'))
    ### pandas options d'affichage des tables
    pd.set_option('display.expand_frame_repr', True)
    pd.set_option('display.colheader_justify', 'right')
    pd.set_option('display.max_colwidth', 50)
    pd.set_option('display.max_column', 30)
    pd.set_option('display.width', 80)

    chsysteme = 'D:\DOCUMENTS\Astronomie\dev\med\STTA254'
    systeme = do.Systeme(chsysteme)
    print('\r')
    print(tabulate(systeme.informations_df, headers='keys', numalign='right',\
                   stralign='right'))
    print('\n')

    # charger objet DoubleSessions
    with open(r'D:\DOCUMENTS\Astronomie\dev\med/STTA254\AB\P2021-023\STTA254_AB_P2021-023_sessions.obj', 'rb') as f:
        s = pickle.load(f)
    print(tabulate(s.sommaire_obs_df, headers='keys', numalign='right',\
                   stralign='right'))
    

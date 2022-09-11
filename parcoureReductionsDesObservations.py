# -*- coding: utf-8 -*-
"""
Created on Sun Jan 10 10:52:06 2021

@author: dominique
"""
import pickle
#import sys
import pandas as pd

# insérer le chemin suivant dans sys.path pour trouver le package astrodm
#if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
#    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
#from astrodm import doublesOutils as do

if __name__ == '__main__':
    ### pandas options d'affichage des tables
    pd.set_option('display.expand_frame_repr', True)
    pd.set_option('display.colheader_justify', 'right')
    pd.set_option('display.max_colwidth', 50)
    pd.set_option('display.max_column', 30)
    pd.set_option('display.width', 200)
    pd.set_option("precision", 4)

    # charger objet DoubleSessions
    with open(r'D:\DOCUMENTS\Astronomie\dev\med/STTA254\AB\P2021-023\STTA254_AB_P2021-023_sessions.obj', 'rb') as f:
        s = pickle.load(f)
        
    reductions = s.reductions_des_observations_df

    for reduction in reductions:
        print(reduction)

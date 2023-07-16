# -*- coding: utf-8 -*-
"""
Created on Thu Nov  4 22:20:15 2021

@author: dominique

mots clés Google : 'python re examples'
"""
import sys
import pandas as pd

# insérer le chemin suivant dans sys.path pour trouver le package astrodm
if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesoutils as do

def inits():
    ### pandas options d'affichage des tables
    pd.set_option('display.expand_frame_repr', True)
    pd.set_option('display.colheader_justify', 'right')
    pd.set_option('display.max_colwidth', 50)
    pd.set_option('display.max_column', 30)
    pd.set_option('display.width', 200)
    pd.set_option("display.precision", 4)

# %% PRINCIPAL
if __name__ == "__main__":
    inits()
    gaia_excel = 'D:\\DOCUMENTS\\Astronomie\\Catalogues et listes\\WDSGaiaDR2\\WDSGaiaDR2_Ver3_test_pour_pandas.ods'

    ##########################################
    # ATTENTION CECI PREND PLUSIEURS MINUTES
    ##########################################
    gaia_pd = pd.read_excel(gaia_excel)
    print(len(gaia_pd))
    # taille 139782 lignes x 33 colonnes

    '''
    gaia_pd.loc[gaia_pd.Discoverer == 'STI1247']
    gaia_pd.loc[gaia_pd.Discoverer == 'LDS 6408']
    gaia_pd.loc[gaia_pd.WDSName == '23599+6113']
    # liste des découvreurs
    gaia_pd.iloc[0:].Discoverer
    
    # découvreur d'enr 145
    gaia_pd.iloc[144].Discoverer
    
    gaia_pd.loc[gaia_pd.Discoverer == 'STTA 253 AC ', 'WDSName']
    gaia_pd.loc[gaia_pd.WDSName == '00013+6021', 'Discoverer']
    gaia_pd.iloc[range(12)]
    gaia_pd.iloc[range(12), [0, 1, 3, 7, 14]]
    gaia_pd.loc[lambda gaia_pd: gaia_pd['Discoverer'] == 'STTA 253 AC ', 'WDSName']
    gaia_pd.loc[lambda gaia_pd: gaia_pd.Discoverer == 'STTA 253 AC ', 'WDSName']
    
    gaia_pd.loc[lambda gaia_pd: gaia_pd.Discoverer.isin(['STTA 253 AC']), 'WDSName']
    gaia_pd.loc[:'STTA 253' in gaia_pd.Discoverer.str.replace(' ',''), 'WDSName']
    gaia_pd.loc[45124:90150]['PM Prob'].mean()
    '''
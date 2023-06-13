# -*- coding: utf-8 -*-
"""
Created on Tue June 13 10:58 2023

@author: dominique
"""

import pandas as pd
from tkinter import Tk
from tkinter.filedialog import askopenfile
import sys
from astropy.coordinates import SkyCoord
from astropy import units as u

# insérer le chemin suivant dans sys.path pour trouver le package astrodm
if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesoutils as do

# %% FONCTIONS

def selectionner_jeu():
    ### Sélectionner répertoire source
    root = Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()
    
    # sélectionner le jeu de données
    ncfj = askopenfile(mode ='r', filetypes =[('Fichiers obj', '*.csv')],\
     title = 'Sélectionnez le jeu de données')

    # trouver racine du répertoire système
    return ncfj.name


# %% PRINCIPAL
if __name__ == '__main__':
    ### pandas options d'affichage des tables
    pd.set_option('display.expand_frame_repr', True)
    pd.set_option('display.colheader_justify', 'right')
    pd.set_option('display.max_colwidth', 50)
    pd.set_option('display.max_column', 30)
    pd.set_option('display.width', 200)
    pd.set_option("display.precision", 4)

    # for tkinter
    root = Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()

    # charger le jeu de données tap Vizier (csv)
    fich_jeu_data_initial = selectionner_jeu()
    jeu_initial_df = pd.read_csv(fich_jeu_data_initial)
    
    # ajouter et renseigner la colonne const avec une valeur par défaut
    # TODO paramétriser const
    constellation = '---'
    jeu_initial_df['const'] = constellation
    
    # prendre AD et DEC à partir de l'enregistrement courant
    raj2000 = jeu_initial_df['RAJ2000'][0]
    dej2000 = jeu_initial_df['DEJ2000'][0]
    
    # trouver la constellation d'après les coordonnées de l'enr 0
    coordonnees = SkyCoord(ra=raj2000, dec=dej2000, frame='icrs', unit=(u.deg, u.deg))
    item_const = coordonnees.get_constellation(short_name=True)
    jeu_initial_df.loc[0, 'const'] = coordonnees.get_constellation(short_name=True)



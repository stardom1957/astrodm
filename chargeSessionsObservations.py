# -*- coding: utf-8 -*-
"""
Created on Sun Jan 10 10:52:06 2021

@author: dominique
"""
import pickle
#import sys
import pandas as pd
from tkinter import Tk
from tkinter.filedialog import askopenfile
import sys

# insérer le chemin suivant dans sys.path pour trouver le package astrodm
if r'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, r'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesoutils as do

# %% FONCTIONS

def selectionner_obj():
    global bool_informations_df_OK
   
    ### Sélectionner répertoire source
    root = Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()
    
    # sélectionner le fichier obj
    ncfo = askopenfile(mode ='r', filetypes =[('Fichiers obj', '*.obj')],\
     title = 'Sélectionnez le fichier objet')

    # trouver racine du répertoire système
    #rrs = os.path.dirname(ncfo.name)
    return ncfo.name


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

    # charger objet DoubleSessions
    fich_obj_sessions = selectionner_obj()
    with open(fich_obj_sessions, 'rb') as f:
        sessions = pickle.load(f)
    
    checksum = do.calcule_ckecksum_fichiers(sessions.cheminProgramme)
    print()
    print('sessions :', sessions.checksum)
    print('fichiers :', checksum)
    if sessions.checksum != checksum:
        print('************ Les données ont changées! ****************')
    else:
        print('************ Aucun changements! ************')
    
    print('\nHiérarchie complète, exécuter : sessions.hier()\n')
    print("Pour les rapports, exécuter :")
    print("  sessions.imprimerRapport('l')")
    print("  sessions.imprimerRapport('m')")

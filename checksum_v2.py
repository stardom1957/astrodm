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
import os
import hashlib

# insérer le chemin suivant dans sys.path pour trouver le package astrodm
#if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
#    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
#from astrodm import doublesOutils as do

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

def ajoute_ckecksum(fich):
    with open(fich,"rb") as f:
        # Read fich  in chunks of 1K and update hash
        for byte_block in iter(lambda: f.read(1024),b""):
            md5_hash.update(byte_block)

def liste_fichiers_logs(s):
    fichiers = list()
    for index_session in range(len(s.lstObjSession)):
        for index_bloc in range(len(s.lstObjSession[index_session].lstBlocs)):
            fichiers.append(s.lstObjSession[index_session].lstBlocs[index_bloc].sep.ncfle)
            fichiers.append(s.lstObjSession[index_session].lstBlocs[index_bloc].sep.ncfla)
            fichiers.append(s.lstObjSession[index_session].lstBlocs[index_bloc].pos.ncfle)
            fichiers.append(s.lstObjSession[index_session].lstBlocs[index_bloc].pos.ncfla)
            fichiers.append(s.lstObjSession[index_session].lstBlocs[index_bloc].reduc.ncflr_sep)
            fichiers.append(s.lstObjSession[index_session].lstBlocs[index_bloc].reduc.ncflr_pos)
    
    return fichiers

if __name__ == '__main__':
    ### pandas options d'affichage des tables
    pd.set_option('display.expand_frame_repr', True)
    pd.set_option('display.colheader_justify', 'right')
    pd.set_option('display.max_colwidth', 50)
    pd.set_option('display.max_column', 30)
    pd.set_option('display.width', 200)
    pd.set_option("precision", 4)

    # charger objet DoubleSessions
    with open(selectionner_obj(), 'rb') as f:
        s = pickle.load(f)
    
    # calculer le checksum des données de s
    global md5_hash
    md5_hash = hashlib.md5()

    lst_fichiers = liste_fichiers_logs(s)

    # calculer et ajouter le md5 de chaque fichier à md5_hash
    for fichier in lst_fichiers:
        if fichier != '':
            #debug print(fichier)
            ajoute_ckecksum(fichier)

    print(md5_hash.hexdigest())
    checksum = md5_hash.hexdigest()

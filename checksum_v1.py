# -*- coding: utf-8 -*-
"""
Created on Sun Jan 10 10:52:06 2021

@author: dominique
"""
from tkinter import Tk
from tkinter.filedialog import askopenfile
import hashlib

# insérer le chemin suivant dans sys.path pour trouver le package astrodm
#if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
#    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
#from astrodm import doublesOutils as do

# %% FONCTIONS

def selectionner_fich():
    global bool_informations_df_OK
   
    ### Sélectionner répertoire source
    root = Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()
    
    # sélectionner le fichier obj
    fichier = askopenfile(mode ='r', filetypes =[('Fichier log ou acquisition', '*.txt')],\
     title = 'Sélectionnez le fichier')

    # trouver racine du répertoire système
    #rrs = os.path.dirname(ncfo.name)
    return fichier.name


if __name__ == '__main__':

    # calculer le checksum des données de s
    fichier = selectionner_fich()
    md5_hash = hashlib.md5()
    with open(fichier,"rb") as f:
        # Read and update hash in chunks of 4K
        for byte_block in iter(lambda: f.read(1024),b""):
            md5_hash.update(byte_block)
        print(md5_hash.hexdigest())

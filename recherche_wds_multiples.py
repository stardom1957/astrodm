# -*- coding: utf-8 -*-
"""
Created on Sun Nov 13 22:32:06 2022

@author: dominique
"""
#%% IMPORTS
import os
import sys
from tkinter import Tk
#from tkinter.filedialog import askdirectory
from tkinter.filedialog import askopenfile

# insérer le chemin suivant dans sys.path pour trouver le package astro_doubles
if r'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, r'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesoutils as do

def selectionner_et_lire_fichier_des_sources():
    """ Lire le fichier texte des sources. """
    ### Sélectionner répertoire source
    #
    root = Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()

    # sélectionner le fichier liste des sources
    #
    ncf = askopenfile(mode ='r', filetypes =[('Fichier liste des sources ', '*.txt')],\
     title = 'Sélectionnez le fichier liste des sources')

    # retourner ncf et racine du répertoire source
    #
    return ncf.name, os.path.dirname(ncf.name)


# %% PRINCIPAL
if __name__ == '__main__':
    
    # charger fichier liste des sources (txt)
    #
    nf, rep = selectionner_et_lire_fichier_des_sources()
    print(nf, rep)
    print()

    # lire nf
    #
    with open(nf, encoding='UTF-8') as f:
        lignesLues = f.readlines()
    f.close()

    # lire les sources dans un set (pour éliminer doublons)
    #
    if lignesLues != '':
        # entreeSources = []
        sources = set()
        for l in lignesLues:
            #entreeSources.append(l.strip('\n'))
            sources.add(l.strip('\n'))
    else:
        print("Erreur, {0} est vide!".format(nf))
        sys.exit()

    # créer une liste à partir du set
    #
    entreeSources = list(sources)
    sources
    #entreeSources = ['L49', 'ber1']

    # effectuer la première recherche
    #
    collige = do.rech_wds(entreeSources[0], '*')
    assert len(collige) != 0, 'La première source doit avoir un résultat WDS valide!'

    for idx in range(1, len(entreeSources)):
        rech = do.rech_wds(entreeSources[idx], '*')
        if len(rech) != 0:
            for r in rech:
                collige.add_row(r)
        else:
            print("{0} non trouvé dans WDS!".format(entreeSources[idx]))

    collige.sort(['Disc', 'Comp'])
    collige.pprint(show_unit=True, max_width=150, max_lines=1500)
    
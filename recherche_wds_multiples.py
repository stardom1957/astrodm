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
import pandas as pd

# insérer le chemin suivant dans sys.path pour trouver le package astro_doubles
if r'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, r'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesoutils as do

#%% FONCTIONS
def systeme_dans(pr):
    ''' indique si "système" in pr '''
    return 'système' in pr

def selectionner_et_lire_fichier_des_sources():
    """ Lire le fichier texte des sources. """
    ### Sélectionner répertoire source
    #
    root = Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()

    # sélectionner le fichier liste des sources
    #
    ncf = askopenfile(mode ='r', filetypes =[('Fichier liste des sources ', '*.txt *.log *.ods')],\
     title = 'Sélectionnez le fichier liste des sources')

    # retourner ncf et racine du répertoire source
    #
    return ncf.name, os.path.dirname(ncf.name)


# %% PRINCIPAL
if __name__ == '__main__':
    '''
    Produit un objet astropy.table.table.Table qui contient les données
    du WDS pour tous les systemes/paires qui se trouvent dans la liste
    chargée à partir d'un fichier.
    
    Entrée
    ------
     L'un de ces types de fichiers :
         *.txt; une liste simple de systèmes chacun sur une ligne.
         
                collige retourne les données WDS de toutes les paires de
                ces systèmes.
         
         *.log; à partir de la liste des systèmes choisis qui se trouvent
               dans le log produit par le script cree_systemes.py.

                collige retourne les données WDS de toutes les paires de
                ces systèmes.
               
               
         *.ods; à partir d'une feuille Calc formattée pour l'entrée de données
                du script cree_systemes.py. Dans ce fichier, la colonne 'choisi'
                n'est pas prise en compte, c.-à-d., toutes les paires sont
                listées.

                collige retourne les données WDS de seulement less paires indiquées
                dans le fichier.
    
    Sortie
    ------
     collige : astropy.table.table.Table
    '''
    
    # sélectionner le fichier liste des sources
    #
    nf, rep = selectionner_et_lire_fichier_des_sources()
    print(nf)
    print()

    # traitement du cas fichier ods
    if '.ods' in nf:
        # lire fichier ods dans un df
        #
        lot_df = pd.read_excel(nf, engine="odf")
        #
        # enlever les lignes vides (nan ...) qui correspondent au lignes blanches dans nf
        #
        lignes_vides_serie = lot_df['id_system'].apply(do.estNan)
        lot_complet_df = lot_df.drop(lot_df.loc[lignes_vides_serie].index).reset_index(drop=True)
        
        # enlever toutes lignes avec 'système' dans paire
        lignes_systeme_serie = lot_complet_df['paire'].apply(systeme_dans)
        lot_complet_df = lot_complet_df.drop(lot_complet_df.loc[lignes_systeme_serie].index).reset_index(drop=True)

        # indique la création de collige à partir du premiet système/paire
        collige_cree = False

        for idx in lot_complet_df.index:
            nom_systeme = lot_complet_df.iloc[idx].id_system
            pr = lot_complet_df.iloc[idx].paire

            # utiliser le premier système/paire pour créer collige
            # effectuer la première recherche pour créer la structure effective du df
            #
            if not collige_cree:
                if pr == 'PPL':
                    pr = '*'
                collige = do.rech_wds(nom_systeme, pr)
                assert len(collige) != 0, 'La première source doit avoir un résultat WDS valide!'
                collige_cree = True
            else:
                if pr == 'PPL':
                    pr = '*'
                rech = do.rech_wds(nom_systeme, pr)
                if len(rech) != 0:
                     for r in rech:
                         collige.add_row(r)
                else:
                    print("{0}/{1} non trouvés dans WDS!".format(nom_systeme, pr))
            
    
    # traitement du cas *.txt (simple liste)
    if '.txt' in nf:
        # lire nf
        #
        with open(nf, encoding='UTF-8') as f:
            lignesLues = f.readlines()
        f.close()

        # placer les sources dans un set (pour éliminer doublons)
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
        # créer une liste à partir du set sources
        #
        entreeSources = list(sources)
        sources
        #entreeSources = ['L49', 'ber1']
    
    # traitement de la liste imbriquée dans un log de cree_systeme.py
    #
    if '.log' in nf:
        # lire nf
        #
        with open(nf, encoding='UTF-8') as f:
            lignesLues = f.readlines()
        f.close()

        # rechercher la ligne contenant 'systèmes choisis'
        idx = 0
        for l in lignesLues:
            idx+=1
            if 'systèmes choisis' in l:
                break
        #
        # idx est le no de ligne qui contient la liste des systèmes choisis
        # sous la forme "{'BRT2257', 'PKO16', ...}"
        #
        sc = lignesLues[idx]
        del lignesLues
        sc = sc.replace('{', '')
        sc = sc.replace('}', '')
        sc = sc.replace("'", '')
        sc = sc.replace("\r", '')
        sc = sc.replace("\n", '')
        entreeSources = list(sc.split(','))
        
    if '.log' in nf or '.txt' in nf:
        # effectuer la première recherche pour créer la structure effective du df
        #
        collige = do.rech_wds(entreeSources[0], '*')
        assert len(collige) != 0, 'La première source doit avoir un résultat WDS valide!'
    
        for idx in range(1, len(entreeSources)):
            #debug rech = do.rech_wds(entreeSources[idx], '*')
            rech = do.rech_wds(entreeSources[idx].lstrip(' ',),'*')
            if len(rech) != 0:
                for r in rech:
                    collige.add_row(r)
            else:
                print("{0} non trouvé dans WDS!".format(entreeSources[idx]))

    # terminer le traitement
    print()
    collige.sort(['Disc', 'Comp'])
    collige.pprint(show_unit=True, max_width=150, max_lines=1500)
    
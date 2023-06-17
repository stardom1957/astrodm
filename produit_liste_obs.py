# -*- coding: utf-8 -*-
"""
Created on Tue June 13 10:58 2023

@author: dominique
"""

import pandas as pd
from tkinter import Tk
from tkinter.filedialog import askopenfile
from astropy.coordinates import SkyCoord
from astropy import units as u
import sys

# insérer le chemin suivant dans sys.path et importer le package astrodm
'''
if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesoutils as do
'''

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

def non_physique(Notes):
    ''' Si une des lettres suivantes se trouvent dans Notes, alors La paire est jugée non physique.'''
    if 'X' in Notes or\
       'S' in Notes or\
       'U' in Notes or\
       'Y' in Notes:
        return True
    else:
        return False
    

# %% PRINCIPAL
if __name__ == '__main__':
    ### pandas options d'affichage des tables
    pd.set_option('display.expand_frame_repr', True)
    pd.set_option('display.colheader_justify', 'right')
    pd.set_option('display.max_colwidth', 50)
    pd.set_option('display.max_column', 30)
    pd.set_option('display.width', 200)
    pd.set_option("display.precision", 4)
    pd.set_option('display.max_rows', None)
    # for tkinter
    root = Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()

    # charger le jeu de données tap Vizier (csv)
    fich_jeu_data_initial = selectionner_jeu()
    df = pd.read_csv(fich_jeu_data_initial)
    assert len(df) !=0, "Jeu de données vide ! Au revoir !"
    print("Lecture du jeu de données ...\n")

    #########################
    # constellation ciblée
    const_cible = 'Lyr'
    #########################
    
    # ajouter la colonne const et la renseigner avec une valeur par défaut
    df['const'] = '---'
    
    # Parcourir le df et renseigner la colonne constellation avec le nom abrégé de la constellation d'appartenance
    # liste_constellations est un set qui contiendra la liste de toutes les constellations trouvées dans df moins const_cible
    #
    liste_constellations = set()
    for s in range(df.index.start, df.index.stop):
        # prendre AD et DEC de l'enregistrement courant
        raj2000 = df.iloc[s]['RAJ2000']
        dej2000 = df.iloc[s]['DEJ2000']
        
        # trouver et renseigner le champ const avec le nom de la constellation d'appartenance
        coordonnees = SkyCoord(ra=raj2000, dec=dej2000, frame='icrs', unit=(u.deg, u.deg))
        nom_abr_const = coordonnees.get_constellation(short_name=True)
        df.at[s, 'const'] = nom_abr_const
        liste_constellations.add(nom_abr_const)
  
    # enlever const_cible du set
    liste_constellations.discard(const_cible)
    
    # taille de la liste originale
    nbr_initial = len(df)

    # enlever de df toutes les entrée qui ne sont pas const_cible, réinitialser l'index et placer dans ndf
    # pour qu'il recommence à 0
    ndf = df.drop(df[df.const != const_cible].index).reset_index(drop=True)
    assert len(ndf) != 0, "Après élaguage, il semble n'y avoir aucune paire restante dans {0} !".format(const_cible)
    nbrfinal = len(ndf)
    
    # en appliquant la fonction non_physique à ndf, la série suivante contiendra tous les index qui sont non physique
    # (True vis-à-vis l'index correspondant)
    non_physique_serie = ndf['Notes'].apply(non_physique)
    
    # le df suivant contiendra toutes les paires non physiques tirées de ndf
    non_physiques_df = ndf.loc[non_physique_serie]
    
    # finalement, le df suivant contiendra seulement les paires qui peuvent être physiques
    probables_df = ndf.drop(ndf.loc[non_physique_serie].index)


    # rapport
    print("Constellation ciblée : {0}".format(const_cible))
    print("-"*len("Constellation ciblée : {0}"))
    print("  Nombre de paires dans la liste source : {0:6d}".format(nbr_initial))
    print("          Nombre de paires NON DANS {0} : {1:6d}         {2} enlevées (de liste_constellations)".format(const_cible, nbr_initial-nbrfinal, liste_constellations))
    print("    Nombre de paires RESTANTES dans {0} : {1:6d}\n".format(const_cible, nbrfinal))

    print("         Nombre de paires non physiques : {0:6d}         (dans non_physiques_df)".format(len(non_physiques_df)))
    print("Nombre de paires probablement physiques : {0:6d}             (dans probables_df)\n".format(len(probables_df)))

    print("Le dataframe « probables_df » peut maintenant être affiné ! Voici un exemple de requête :\n")
    print('...: q1 = probables_df.query("Obs2 <= 2010 and sep2 >= 5.0 and sep2 < 180.0 and abs(mag2-mag1) < 3.0").reset_index(drop=True)')

    # NOTES
    """
    q1 = probables_df.query("Obs2 <= 2010 and sep2 >= 5.0 and sep2 < 180.0 and abs(mag2-mag1) < 3.0")
    df.query("'Her' in const")
    """
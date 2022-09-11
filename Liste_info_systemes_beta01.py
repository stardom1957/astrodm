# -*- coding: utf-8 -*-
"""
Created on Mon Feb 21 17:11:24 2022

@author: dominique
"""

import os
import glob
import pandas as pd
import sys
# insérer le chemin suivant dans sys.path pour trouver le package astrodm
if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesoutils as do
# %% INITIALISATIONS
### pandas options d'affichage des tables
pd.set_option('display.expand_frame_repr', True)
pd.set_option('display.colheader_justify', 'right')
pd.set_option('display.max_colwidth', 75)
pd.set_option('display.max_column', 15)
pd.set_option('display.width', 200)
pd.set_option('display.max_row', 10000)
pd.set_option("precision", 1)

if __name__ == '__main__':
    # demander sortie au terminal ou fichier
    sortie = 'terminal'
    rep = input("Sortie au terminal (t) ou  fichier (f) : ").upper()

    # construire la liste de tri
    liste_de_tri = [['id_system'],\
                    ['const'],
                    ['id_system', 'const'],
                    ['id_WDS']
                   ]

    i = 0
    print('\n')
    for t in liste_de_tri:
        print(i, t)
        i+=1
    tri = input("Indiquez ordre de tri [0-" +\
                str(len(liste_de_tri)-1) + "] : ")

    assert int(tri) in range(len(liste_de_tri)), 'Oups «{0}» is illégal! Bye!'.format(tri)

    ch = os.getcwd() + '/med'
    dirs = glob.glob(ch + r'\**\*_info_système.csv', recursive=True)
    info_systemes_df = pd.read_csv(dirs[0])
    dirs.pop(0)
    
    for dir in dirs:
        info_systemes_df = info_systemes_df.append(pd.read_csv(dir),ignore_index=True)

    if rep == 'F':
        # sortie vers fichier ./med/med-planification/....txt
        systag = do.produire_systag()
        
        # construire chaîne ordre de tri
        tempo = ""
        for eltri in liste_de_tri[int(tri)]:
            tempo = tempo + eltri + "+"
        tempo = tempo.rstrip("+")
        tempo = "(" + tempo + ")"
        ncfis = os.getcwd() + '/med/med-planification/LISTES/astrodm-liste-info-systemes-trie' + tempo + "-"  + systag + '.txt'
        ancien_stdout = sys.stdout
        f = open(ncfis, 'w')
        sys.stdout = f

    # trier le df
    info_systemes_df.sort_values(by=liste_de_tri[int(tri)], ignore_index=True,\
                              inplace=True)
    
    print("\nTri sur : {0}".format(liste_de_tri[int(tri)]))
    print(info_systemes_df)

    if rep == 'F':
        # rétablir stdout
        sys.stdout = ancien_stdout
        f.close()
        print("Sortie dans :\n  {0}".format(ncfis))
        
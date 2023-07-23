# -*- coding: utf-8 -*-
"""
Created on Thu Jan 14 14:48:43 2021

@author: dominique
version 05
"""
import os
import sys

# insérer le chemin suivant dans sys.path pour trouver le package astrodm
if r'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, r'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesoutils as do

if __name__ == '__main__':
    # demander ordre de tri
    #
    i = 0
    for t in do.liste_de_tri_prog:
        print(i, t)
        i+=1
    tri = input("\nIndiquez ordre de tri [0-" +\
                str(len(do.liste_de_tri_prog)-1) + "] 1 par défaut : ") or 1
    print(" Tri sur {0}".format(do.liste_de_tri_prog[int(tri)]))

    # demander si sortie sur disque
    #
    sortir_ici = input("\n t Sortie au terminal (par défaut) ou fichier (f) : ").upper() or 'T'
    assert sortir_ici in ('T', 'F'), 'Mauvaise valeur!'
    print(" Sortie vers {0}".format(sortir_ici))
    
    if int(tri) in range(len(do.liste_de_tri_prog)):
        # dernier paramètre == True, imprime tables des notes
        ch = chemin=os.getcwd() + '/med'
        suivi_df = do.suivi(ch, tri=int(tri), impr_table_etat=True, sortie=sortir_ici)
    else:
        print('Oups «{0}» is illégal! Bye!'.format(tri))

    # la variable programme permet de filtrer suivi_df au besoin
    # if programme is not None:
    #    suivi_df.query("obs_prog == @programme")
    print('\n\nAfin de filtrer pour un programme spécifique,\n veuillez définir la variable programme\n et exécuter :\n')
    print("q1 = suivi_df.query('obs_prog == @programme')")
    print("q2 = suivi_df.query('obs_prog == @programme and État != \"P L\"')")
          


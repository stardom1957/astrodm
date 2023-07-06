# -*- coding: utf-8 -*-
"""
Created on Thu Jan 14 14:48:43 2021

@author: dominique
version 01
"""
import os
import sys

# insérer le chemin suivant dans sys.path pour trouver le package astrodm
if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesoutils as do

if __name__ == '__main__':
    # demander vers quelle sortie
    #
    sortir_ici = input("\n t Sortie au terminal (par défaut) ou fichier (f) : ").upper() or 'T'
    assert sortir_ici == 'T' or sortir_ici == 'F', 'Mauvaise valeur!'
    # debug print(" Sortie vers {0}".format(sortir_ici))

    # demander ordre de tri
    i = 0
    for t in do.liste_de_tri_reduc:
        print(i, t)
        i+=1
    tri = input("\nIndiquez ordre de tri [0-" + str(len(do.liste_de_tri_reduc)-1) + "] : ") or '1'
    del t, i
    
    if int(tri) in range(len(do.liste_de_tri_reduc)):
        # dernier paramètre == True, imprime tables des notes

        reductions = do.imprime_liste_reductions(os.getcwd() + '/med', int(tri), True, sortir_ici)
    else:
        print('Oups «{0}» is illégal! Bye!'.format(tri)) 

    del tri

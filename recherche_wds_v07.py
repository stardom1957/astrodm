# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 16:31:40 2020

@author: dominique
version 07
"""

###IMPORT

import sys
# insérer le chemin suivant dans sys.path pour trouver le package astro_doubles
if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesoutils as do


        
def info_src_wds(src, paire):
    # recherche Vizier.query_constraints
    # source sur 7 caractères (A7)
    # caractères de remplacement ? et * acceptés
    # pour 'stfa nn' ==> 'stf? nn'
    
    '''
    ATTENTION L'ON DOIT FORMATER CORRECTEMENT strSource
    avec 7 caractères
    '''
    strSource = src.upper()
    # pour toutes les paires strPaire = '*'
    strPaire = paire.upper()
    
    ### soumettre la requête à WDS
    qres = do.rech_wds(strSource, strPaire)
    
    if qres != []:
        longueur = qres[0].__len__()
        print('\nIl y a {0} résultats pour «{1}», paire = «{2}».\n'.format(longueur, strSource, strPaire))
        # trier sur WDS et composants
        qres[0].sort(['Disc', 'Comp'])
        #qres[qres.keys()[0]].pprint()
    
        print('Données tirées du Washington Double Stars Catalog (WDS)')
        print('Tris sur "Disc" et "Comp"')
        print('-' * 120)
        qres[0].pprint(show_unit=True, max_width=120, max_lines=150)
        print('-' * 120)
        
        ### obtenir WDS Notes
        # il faut normaliser strSource sur 7 car
        wds_notes = do.rech_wds_notes(strSource)
        
        if wds_notes != []:
            print('\n ***** WSD Notes pour {0} *****'.format(strSource))
            wds_notes[0].pprint(max_width=120)
        else:
            print('Aucune note trouvée.')
    
    else:
        print("La requête pour '{0}' n'a donné aucun résultat".format(strSource))
        sys.exit()
    

# %% PRINCIPAL
if __name__ == "__main__":
    ### saisir source
    print('Attention :')
    print(' H x n : entrer hx*')
    strSource = input("Nom de la source (max 7 car) : ")
    if len(strSource) > 7:
        print('Source non valide.')
        sys.exit()

    # pour toutes les paires strPaire = '*'
    strPaire = '*'
    info_src_wds(strSource, strPaire)
    
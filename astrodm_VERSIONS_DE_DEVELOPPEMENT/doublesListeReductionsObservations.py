# -*- coding: utf-8 -*-
#! /usr/bin/env python
# version 8 pour inclusion dans astrodm

import os
#from os.path import join, getsize
import os.path
import pandas as pd
import numpy as np


import sys
# insérer le chemin suivant dans sys.path pour trouver le package astrodm
if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesOutils as do


# %% FONCTIONS
def parcoure_chemin_au_complet(ch):
    global int_N_sources, set_programmes
    liste_prog_lst = list()
    int_N_sources = 0
    set_programmes = set()
    #global liste_résultat
    for root, dirs, files in os.walk(ch):
        #print ('\n' + root + ' :')
        for dir in dirs:
            if 'P20' in dir:
                set_programmes.add(dir)
        for name in files:
            if os.path.isfile(os.path.join(root, name)):
                #print ('   ', name, ' (', os.path.getsize(os.path.join(root, name)), ' octets)', end='\n')
                #print ('   ', root, ' (', os.path.getsize(os.path.join(root, name)), ' octets)', end='\n')
                if '_info_système.csv' in name:
                    #print('   -> fichier source trouvé!')
                    #print ('   ', name, ' (', os.path.getsize(os.path.join(root, name)), ' octets)', end='\n')
                    int_N_sources += 1
                    # ouvrir le fichier info_source
                    informations_df = pd.read_csv(os.path.join(root, name))
                    nom_complet_fichier_informations = os.path.join(root, name)

                    # lire id_source, id_WDS et const
                    id_source = informations_df.loc[0, 'id_source']
                    id_WDS = informations_df.loc[0, 'id_WDS']
                    const = informations_df.loc[0, 'const']
                    
                if '_observations.csv' in name:
                    # ouvrir le fichier observations
                    ch_rep_paire = root.replace('\\mesures', '')
                    observations_df = pd.read_csv(os.path.join(root, name), \
                       dtype={'N':pd.Int8Dtype(), 'transp':pd.Int8Dtype()})
                    
                    # nombre d'observation et liste des N dans une série pd
                    Nobs = observations_df.loc[:, 'N'].count()
                    #liste_des_N_df = observations_df.loc[:, 'N']

                    # lire paire, N, obs_prog et notes
                    obs_prog = observations_df.loc[0, 'obs_prog']
                    paire = observations_df.loc[0, 'paire'].replace('"', '')
                    notes = observations_df.loc[0, 'notes']
                    
                    # initialiser valeurs WDS
                    WDS_pa2 = np.nan
                    WDS_sep2 = np.nan
                    WDS_epoch = np.nan

                    # trouver obs_debut pour la dernière observations valide
                    if Nobs != 0:
                        # il y des observations valides, alors réduire
                        obs_debut_dern_obs = observations_df.loc[observations_df.loc[:, 'N'].count()-1, 'obs_debut']
                        
                        ### effectuer la réduction des observations
                        # res est un dictionnaire des résultats
                        res = do.reduireObservations(nom_complet_fichier_informations, ch_rep_paire)
                        
                        # trouver info WDS
                        qres = do.rech_wds(id_source, paire)
                        if qres != []:
                            WDS_pa2 = qres[0][0]['pa2']
                            WDS_sep2 = qres[0][0]['sep2']
                            WDS_epoch = qres[0][0]['Obs2']

                        # composer le dict des résultats
                        ligne_dict = {
                           'obs_prog': obs_prog,
                           'id_source': id_source,
                           'paire': paire,
                           'id_WDS': id_WDS,
                           'const': const,
                           'N': Nobs,
                           'Date_obs_N': obs_debut_dern_obs.split('T')[0],
                           'pa' : res['theta_moy'],
                           'sep': res['rho_moy'],
                           'époque_obs_N': 'B{0:4.4f}'.format(res['epoque_moy']),
                           'WDS_pa2': WDS_pa2,
                           'WDS_sep2': WDS_sep2,
                           'WDS_epoch': WDS_epoch,
                           'notes': notes
                        }

                    else:
                        #il n'y a pas d'observations valides, alors inscrire null aux res de réduction
                        # composer le dict des résultats
                        ligne_dict = {
                           'obs_prog': obs_prog,
                           'id_source': id_source,
                           'paire': paire,
                           'id_WDS': id_WDS,
                           'const': const,
                           'N': Nobs,
                           'Date_obs_N': np.nan,
                           'pa' : np.nan,
                           'sep': np.nan,
                           'époque_obs_N': np.nan,
                           'WDS_pa2': WDS_pa2,
                           'WDS_sep2': WDS_sep2,
                           'WDS_epoch': WDS_epoch,
                           'notes': notes
                        }

                    #print ('   ', name, ' (', os.path.getsize(os.path.join(root, name)), ' octets)', end='\n')
                    #print('   --> {0} {1} {2} {3} {4} {5} {6}\n'.format(obs_prog, id_source, paire, id_WDS, const, Nobs, obs_debut_dern_obs))

                    # ajouter à liste des dict des résultats
                    liste_prog_lst.append(ligne_dict)
                    
                
        # exclusions
        if 'listes' in dirs:
            dirs.remove('listes')
        if 'astro_doubles' in dirs:
            dirs.remove('astro_doubles')
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
        if '.ipynb_checkpoints' in dirs:
            dirs.remove('.ipynb_checkpoints')
        if 'aaabackups' in dirs:
            dirs.remove('aaabackups')
        if 'Astropy' in dirs:
            dirs.remove('Astropy')
        if 'sources' in dirs:
            dirs.remove('sources')
        if 'traitement' in dirs:
            dirs.remove('traitement')

    #retourner le df
    return pd.DataFrame(liste_prog_lst)

def imprime_reductions_ed(chemin, avec_notes=True):
    ### parcourir le chemin
    
    liste_df = parcoure_chemin_au_complet(chemin)
    int_nbr_programmes = len(set_programmes)
    
    ### trier résultat
    #tri1_lst = ['obs_prog', 'id_source', 'paire']
    tri1_lst = ['obs_prog']
    liste_df.sort_values(by=tri1_lst, ignore_index=True, inplace=True)
    #liste_df.fillna(' ', inplace=True)

    ### pandas options d'affichage des tables
    pd.set_option('display.expand_frame_repr', True)
    pd.set_option('display.colheader_justify', 'right')
    pd.set_option('display.max_colwidth', 50)
    pd.set_option('display.max_column', 15)
    pd.set_option('display.width', 150)
    pd.set_option('display.max_row', 1000)
    pd.set_option("precision", 1)

    ### imprimer les résultats
    print("RÉSULTATS DES PROGRAMMES D'OBSERVATIONS\n")
    print ('Le chemin de base est : ' + chemin + '\n')
    print('DataFrame «liste_prog_df» triée par', tri1_lst, ' :')
    print('-' * 124)
    print(liste_df)
    print('-' * 124)
    print('      Nombre de sources différentes : {0:>3d}'.format(int_N_sources))
    print("Nombre de programmes d'observations : {0:>3d}".format(int_nbr_programmes))
    
    if avec_notes:
        ### Liste dictionnaire des codes de notes d'observations
        print('\nnotes [descriptions] :')
        
        for code in do.notes_obs_dict:
            print(' ', code, do.notes_obs_dict[code])
    
    print('\nEXEMPLES DE REQUÊTES :')
    print("reductions.query(\"id_source == 'STF 982'\")")
    print("reductions.query(\"notes == 'P  '\")")
    print("reductions.query(\"const == 'And'\")")
    print("reductions.query(\"const == 'And' or const == 'Gem'\")")
    
    return liste_df
# %% PRINCIPAL
if __name__ == '__main__':
    import os
    str_chemin_racine = os.getcwd()
    reductions = imprime_reductions_ed(str_chemin_racine)
    
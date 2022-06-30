# -*- coding: utf-8 -*-
#! /usr/bin/env python
######################################
# version 7 pour intégrer à astrodm
######################################
import os
#from os.path import join, getsize
import pandas as pd
#import numpy as np
#import cree_notes_observations_dict_v02 as cno
import pickle

import sys
# insérer le chemin suivant dans sys.path pour trouver le package astrodm
if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesOutils as do

# %% INITIALISATIONS
### pandas options d'affichage des tables
pd.set_option('display.expand_frame_repr', True)
pd.set_option('display.colheader_justify', 'right')
pd.set_option('display.max_colwidth', 50)
pd.set_option('display.max_column', 15)
pd.set_option('display.width', 150)
pd.set_option('display.max_row', 10000)
pd.set_option("precision", 1)

# %% FONCTIONS
def version():
    print("doublesListeProgrammes version " + str(nversion))

def liste_programmes_obs(ch):
    '''
    Produit une liste (de dictionnaires) des programmes d'observations d'étoiles
    doubles qui se trouvent dans le répertoire courant.

    Parameters
    ----------
    ch : string :: chemin complet de la tête du répertoire des observations.

    Returns
    -------
    None.

    '''
    global int_nbr_sources_lues, liste_programmes_uniques
    global nbr_obs_C, nbr_obs_T, nbr_obs_P, nbr_obs_X, nbr_obs_E
    
    # décompte des observation avec note d'état C, T et P
    nbr_obs_X, nbr_obs_E, nbr_obs_C, nbr_obs_T, nbr_obs_P,\
        int_nbr_sources_lues = 0, 0, 0, 0, 0, 0
    liste_prog_dates_lst = list()
    liste_programmes_uniques = set()
    
    for root, dirs, files in os.walk(ch):
        for dir in dirs:
            if 'P20' in dir:
                liste_programmes_uniques.add(dir)
        for name in files:
            if os.path.isfile(os.path.join(root, name)):
                if '_info_système.csv' in name:
                    #print('   -> fichier source trouvé!')
                    #print ('   ', name, ' (', os.path.getsize(os.path.join(root, name)), ' octets)', end='\n')
                    int_nbr_sources_lues += 1
                    # ouvrir le fichier info_source
                    informations_df = pd.read_csv(os.path.join(root, name))

                    # lire id_source, id_WDS et const
                    id_source = informations_df.loc[0, 'id_source']
                    id_WDS = informations_df.loc[0, 'id_WDS']
                    const = informations_df.loc[0, 'const']
                    
                if '_sessions.obj' in name:
                    # ouvrir du résultats des sessions d'observations
                    # charger l'objet DoubleSessions (sérialisé)
                    with open(os.path.join(root, name), 'rb') as f:
                        s = pickle.load(f)

                    #nbr_lignes_dans_observations = len(observations_df.index)

                    # lire paire, N, obs_prog et État
                    
                    obs_prog = s.prog
                    paire = s.paire

                    # faire le décompte des États 'XECPT'
                    if 'P' in s.etat:
                       nbr_obs_P += 1
                    if 'C' in s.etat:
                       nbr_obs_C += 1
                    if 'T' in s.etat:
                       nbr_obs_T += 1
                    if 'E' in s.etat:
                       nbr_obs_E += 1
                    if 'X' in s.etat:
                       nbr_obs_X += 1
                    
                    #obs_debut = observations_df.loc[observations_df.loc[:, 'N'].count()-1, 'obs_debut']
                    obsN = s.nbrN
                    dateDernObs = s.date_obs_n

                    # transformer liste état en str                    
                    strEtat = ''
                    for i in range(0, len(s.etat)):
                        strEtat += s.etat[i]


                    # composer le dict des résultats
                    ligne_dict = {
                       'obs_prog': obs_prog,
                       'id_source': id_source,
                       'paire': paire,
                       'id_WDS': id_WDS,
                       'const': const,
                       'N (obs)': obsN,
                       'Date_obs_N': dateDernObs,
                       'État': strEtat
                    }

                    # ajouter à liste des dict des résultats
                    #liste_prog_dates_lst.append(ligne_dict)
                    
                
        # exclusions
        if 'cal_e' in dirs:
            dirs.remove('cal_e')
        if '.ipynb_checkpoints' in dirs:
            dirs.remove('.ipynb_checkpoints')

        '''debug    
        if 'astro_doubles' in dirs:
            dirs.remove('astro_doubles')
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
        if 'aaabackups' in dirs:
            dirs.remove('aaabackups')
        if 'Astropy' in dirs:
            dirs.remove('Astropy')
        if 'sources' in dirs:
            dirs.remove('sources')
        if 'traitement' in dirs:
            dirs.remove('traitement')
        '''
    return liste_prog_dates_lst

def imprime_liste(chemin, tri, avec_notes = True):
    '''
    imprime la liste des programmes d''observations

    Parameters
    ----------
    chemin : TYPE txt chemin
        
    tri : TYPE int, ordre de tri de 1 à 4.'

    avec_notes : TYPE, optional

    Returns
    -------
    liste_prog_dates_df : pandas.core.frame.DataFrame
        Dataframe Pandas.  L''on peu utiliser de la manière suivante :
            data.query("id_source == 'STF 982'")

    '''
    chemin_complet_rep_racine = chemin
    
    ### parcourir le répertoire racine
    print ('Le chemin de base est : ' + chemin_complet_rep_racine + '\n')
    lst_prog = liste_programmes_obs(chemin_complet_rep_racine)
    int_nbr_programmes = len(liste_programmes_uniques)
    
    ### transformer résultat en dataFrame
    liste_prog_dates_df = pd.DataFrame(lst_prog)
   
    ### trier résultat
    #tri1_lst = ['obs_prog', 'id_source', 'paire', 'obs']
    # construire la liste de tri 4 
    tri1_lst = [['obs_prog', 'id_source'], ['id_source', 'obs_prog'], ['const'], ['Date_obs_N']]
    #tri1_lst = ['obs_prog', 'id_source']
    liste_prog_dates_df.sort_values(by=tri1_lst[tri], ignore_index=True, inplace=True)
    #liste_prog_dates_df.fillna(' ', inplace=True)
    
    ### lister résultat
    print('DataFrame «liste_prog_dates_df» triée par', tri1_lst[tri], ' :')
    print('-' * 72)
    print(liste_prog_dates_df)
    print('-' * 72)
    print('      Nbr sources différentes lues : {0:>3d}.'.format(int_nbr_sources_lues))
    print("                  Nbr prog obs lus : {0:>3d}, dont :".format(int_nbr_programmes))
    print("                                        {0:>3d} sont terminées.".format(nbr_obs_T))
    print("                                        {0:>3d} sont en planification.".format(nbr_obs_P))
    print("                                        {0:>3d} sont en cours.".format(nbr_obs_C))
    print("                                        {0:>3d} sont à reprendre.".format(nbr_obs_X))
    print("                                        {0:>3d} sont en erreur.".format(nbr_obs_E))
    
    if avec_notes:    
        ### Liste dictionnaire des codes de notes d'observations
        print('\nnotes [descriptions] :')
        for code in do.notes_obs_dict:
            print(' ', code, do.notes_obs_dict[code])
    
    print('\nEXEMPLES DE REQUÊTES :')
    print("data.query(\"id_source == 'STF 982'\")")
    print("data.query(\"notes == 'P  '\")")
    print("data.query(\"const == 'And'\")")
    print("data.query(\"const == 'And' or const == 'Gem'\")")
    return liste_prog_dates_df
      
# %% inits
nversion = 7

# %% PRINCIPAL
if __name__ == '__main__':
    data = imprime_liste('D:\DOCUMENTS\Astronomie\dev')
    

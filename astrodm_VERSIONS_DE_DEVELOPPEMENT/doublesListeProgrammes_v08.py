# -*- coding: utf-8 -*-
#! /usr/bin/env python
######################################
# version 8 pour intégrer à astrodm
######################################
import os
from os import path
#from os.path import join, getsize
import pandas as pd
#import numpy as np
#import cree_notes_observations_dict_v02 as cno
import pickle
import glob
import re

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

def est_une_paire(chaine):
    '''
      Cette méthode vérifie si la chaine passée en paramètre est valide.
      
    Parameters
    ----------
    String chaine :: nom du répertoire (basename) à vérifier.

    Returns
    -------
    
    True | False selon le cas
    String la désignation validée de la paire
      
    '''
    #pattern = r'([A-Z]{2}\-[0-9]{2}\-[0-9]{2}b[0-9]{2})'
    #res = filter(re.compile(str_re_pattern).match, l[1])
    #obj_match = obj_pat.match(l[1])

    str_re_pattern = r'[A-Z]{3}|[A-Z]{2}'
    obj_pat = re.compile(str_re_pattern)
    if ',' not in chaine:
        res = obj_pat.search(chaine)
        if res != None:
            return True, res.group(0)
        else:
            return False, None
    else:
        return True, chaine


def est_un_programme(chemin):
    '''
      Cette méthode vérifie si la chaine passée en paramètre est valide pour
      un programme d'observation.
      
    Parameters
    ----------
    String chemin :: chemin du répertoire à vérifier.

    Returns
    -------
    
    True | False selon le cas
      
    '''
    #pattern = r'([A-Z]{2}\-[0-9]{2}\-[0-9]{2}b[0-9]{2})'
    #res = filter(re.compile(str_re_pattern).match, l[1])
    #obj_match = obj_pat.match(l[1])

    valide = False
    str_re_pattern = r'P[0-9]{4}-[0-9]{3}'
    obj_pat = re.compile(str_re_pattern)
    res = obj_pat.search(chemin)
    if res != None:
        if len(res.group(0)) == 9:
            valide = True
    return valide


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
    liste_progs = list()
    liste_programmes_uniques = set()
    
    # obtenir la liste des dir (sources) dans ch
    dirSources = glob.glob(ch+'/*')
    for dir_source in dirSources:
        if 'cal_e' not in dir_source:
            # ititialisations
            id_source, id_WDS, const, paire, obs_prog, dateDernObs =\
                None, None, None, '<NA>', '<NA>', '<NA>'
            obsN, delai = 0, 0
            strEtat = '?  '
            int_nbr_sources_lues += 1
            
            id_source = path.basename(dir_source)
            #debug print('traitement ' + id_source)

            # rechercher fichier «source + '_info_système.csv'»
            lstFichiers = glob.glob(dir_source + '/*_info_système.csv')
            #debug print(lstFichiers)
            assert len(lstFichiers) == 1,\
             print("Erreur traitement {0} :: plus d'un _info_système.csv".\
                  format(id_source))
                 
            # lire info_système
            # ouvrir le fichier info_source
            informations_df = pd.read_csv(lstFichiers[0])
            #debug print(informations_df)

            # relire id_source et lire id_WDS et const
            id_source = informations_df.loc[0, 'id_source']
            id_WDS = informations_df.loc[0, 'id_WDS']
            const = informations_df.loc[0, 'const']
            
            # bâtir la liste des paires potentielles présentent dans dir_source
            lstPairesPotentielles = glob.glob(dir_source + '/*/')
            
            # dans le cas où il n'y a pas de paire
            # il faut quand même créer un enregistrement
            if len(lstPairesPotentielles) == 0:
                ligne_dict = {
                   'obs_prog': obs_prog,
                   'id_source': id_source,
                   'paire': paire,
                   'id_WDS': id_WDS,
                   'const': const,
                   'N (obs)': obsN,
                   'Date_obs_N': dateDernObs,
                   'delai': delai,
                   'État': strEtat
                }

                # ajouter à liste des dict des résultats
                liste_progs.append(ligne_dict)
            
            for pr in lstPairesPotentielles:
                # valider s'il s'agit d'une paire
                tempo = path.basename(path.dirname(pr))
                boolPaire, paire = est_une_paire(tempo)                
                #debug print("debug {0} {1} {2}".format(pr, boolPaire, paire))
                
                # C'est une paire valide, on continue
                if boolPaire:
                    # trouver la liste des programmes
                    lstProgs = glob.glob(pr + '/P*/')
                    #debug print(lstProgs)
                    for prog in lstProgs:
                        if est_un_programme(prog):
                            # ajouter à la liste des programmes (uniques)
                            liste_programmes_uniques.add(path.basename(path.dirname(prog)))
                            #debug print('  prog ' , prog)
                            obs_prog = path.basename(path.dirname(prog))
                            
                            # s'il existe un fichier *.obj (un seul!) du résultat
                            # des sessions d'observations, alors traiter
                            # sinon il n'y a pas encore eue de post-réduction
                            fich = glob.glob(prog+'/*.obj')
                            if len(fich) == 1:
                                # charger le fichier .obj de sessions dans s
                                try:
                                    with open(fich[0], 'rb') as f:
                                        s = pickle.load(f)
                                        obsN = s.nbrN
                                        dateDernObs = s.resultats_reductions_sessions_df.loc[0, 'dern_obs_utc']
                                        strEtat = s.resultats_reductions_sessions_df.loc[0, 'État']
                                        delai = s.resultats_reductions_sessions_df.loc[0, 'delai']
                                        
                                except FileNotFoundError:
                                    # fichier objet illisible! Continuer
                                    # tout de même
                                    pass
                            else:
                                # pas de fichier obj, alors il n'y a pas eu
                                # post-réduction
                                obsN = 'NaN'
                                dateDernObs = 'NaN'
                                strEtat = 'P  '
                                delai = 'NaN'
                            
                # faire le décompte des États 'XECPT'
                if 'P' in strEtat:
                   nbr_obs_P += 1
                if 'C' in strEtat:
                   nbr_obs_C += 1
                if 'T' in strEtat:
                   nbr_obs_T += 1
                if 'E' in strEtat:
                   nbr_obs_E += 1
                if 'X' in strEtat:
                   nbr_obs_X += 1

                #debug imprimer enregistrement
                '''
                tempo = "{0}: '{1}' {2} '{3}' {4} {5} {6} {7} {8} '{9}'"
                print(tempo.format(\
                            int_nbr_sources_lues,\
                            id_source,\
                            obs_prog,\
                            id_WDS,\
                            paire,\
                            const,\
                            obsN,\
                            dateDernObs,\
                            delai,\
                            strEtat))
                '''

                #debug print('\n')
                # composer le dict des résultats
                ligne_dict = {
                   'obs_prog': obs_prog,
                   'id_source': id_source,
                   'paire': paire,
                   'id_WDS': id_WDS,
                   'const': const,
                   'N (obs)': obsN,
                   'Date_obs_N': dateDernObs,
                   'delai': delai,
                   'État': strEtat
                }

                # ajouter à liste des dict des résultats
                liste_progs.append(ligne_dict)


    '''
    print("debug Nbr de sources uniques traitées : {0}".format(len(liste_programmes_uniques)))
    tempo = "P:{0} C:{1} T:{2} E:{3} X:{4}"
    print(tempo.format(\
             nbr_obs_P,
             nbr_obs_C,
             nbr_obs_T,
             nbr_obs_E,
             nbr_obs_X))
    '''
    return liste_progs
    

def imprime_liste(chemin, tri, avec_notes = True):
    '''
    imprime la liste des programmes d'observations

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
    int_nbr_prog_uniques = len(liste_programmes_uniques)
    
    ### transformer résultat en dataFrame
    liste_prog_dates_df = pd.DataFrame(lst_prog)
   
    ### trier résultat
    #tri1_lst = ['obs_prog', 'id_source', 'paire', 'obs']
    # construire la liste de tri
    tri1_lst = [['obs_prog', 'id_source'],\
                ['id_source', 'obs_prog'],
                ['const'],
                ['Date_obs_N']]
        
    #tri1_lst = ['obs_prog', 'id_source']
    liste_prog_dates_df.sort_values(by=tri1_lst[tri], ignore_index=True, inplace=True)
    #liste_prog_dates_df.fillna(' ', inplace=True)
    
    ### lister résultat
    print('DataFrame «liste_prog_dates_df» triée par', tri1_lst[tri], ' :')
    print('-' * 78)
    print(liste_prog_dates_df)
    print('-' * 78)
    print('      Nbr sources différentes lues : {0:>3d}.'.format(int_nbr_sources_lues))
    print("      Nbr de programmes différents : {0:>3d}".format(int_nbr_prog_uniques))
    print("      Distribution : ")
    print("          {0:>3d} sont terminées.".format(nbr_obs_T))
    print("          {0:>3d} sont en planification.".format(nbr_obs_P))
    print("          {0:>3d} sont en cours.".format(nbr_obs_C))
    print("          {0:>3d} sont à reprendre.".format(nbr_obs_X))
    print("          {0:>3d} sont en erreur.".format(nbr_obs_E))
    
    if avec_notes:    
        ### Liste dictionnaire des codes de notes d'observations
        print('\nnotes [descriptions] :')
        for code in do.codes_etat_obs_dict:
            print(' ', code, do.codes_etat_obs_dict[code])
    
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
    

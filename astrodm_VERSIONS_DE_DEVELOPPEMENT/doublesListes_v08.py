# -*- coding: utf-8 -*-
#! /usr/bin/env python
############
# version 10
############
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
    #print("doublesListeProgrammes version " + str(nversion))
    print(__name__ + ' ' + str(nversion))

def est_une_paire(chaine):
    '''
      Cette méthode vérifie si la chaine passée en paramètre est une paire 
      valide.
      
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

    str_re_pattern = r'^[A-Z]{3}|^[A-Z]{2}'
    obj_pat = re.compile(str_re_pattern)
    if ',' not in chaine:
        res = obj_pat.search(chaine)
        if res != None:
            return True, res.group(0)
        else:
            return False, 'ERREUR'
    else:
        return True, chaine


def est_un_programme(chemin):
    '''
      Cette méthode vérifie si le chemin passé en paramètre est un programme
      d'observation valide.
      
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


def produit_liste_programmes_obs(ch):
    '''
    Parcoure le chemin ch et retourne une liste (list()) des programmes
    d'observations.

    Parameters
    ----------
    ch : string :: chemin complet de la tête du répertoire des observations.

    Returns
    -------
    list() des programmes d'observations.

    '''
    global int_nbr_systemes_exam, liste_programmes_uniques
    global nbr_etat_C, nbr_etat_T, nbr_etat_P, nbr_etat_X, nbr_etat_E,\
        nbr_etat_NA
    
    # décompte des observation avec note d'état C, T et P
    nbr_etat_X, nbr_etat_E, nbr_etat_C, nbr_etat_T, nbr_etat_P, nbr_etat_NA,\
        int_nbr_systemes_exam = 0, 0, 0, 0, 0, 0, 0
    liste_progs = list()
    liste_programmes_uniques = set()
    
    # obtenir la liste des dir (systemes) dans ch
    dirSystemes = glob.glob(ch+'/*')
    for dir_systeme in dirSystemes:
        if 'cal_e' not in dir_systeme:
            # ititialisations
            id_system, id_WDS, const, paire, obs_prog, dateDernObs =\
                None, None, None, 'aucune', 'aucun', 'aucune'
            obsN, delai = 'NaN', 'NaN'
            strEtat = '?  '
            int_nbr_systemes_exam += 1
            
            id_system = path.basename(dir_systeme)
            #debug print('traitement ' + id_system)

            # rechercher fichier «source + '_info_système.csv'»
            lstFichiers = glob.glob(dir_systeme + '/*_info_système.csv')
            #debug print(lstFichiers)
            assert len(lstFichiers) == 1,\
             print("Erreur traitement {0} :: plus d'un _info_système.csv".\
                  format(id_system))
                 
            # lire info_système
            # ouvrir le fichier info_source
            informations_df = pd.read_csv(lstFichiers[0])
            #debug print(informations_df)

            # relire id_system et lire id_WDS et const
            id_system = informations_df.loc[0, 'id_system']
            id_WDS = informations_df.loc[0, 'id_WDS']
            const = informations_df.loc[0, 'const']
            
            # bâtir la liste des paires potentielles présentent
            # dans dir_systeme
            lstPairesPotentielles = glob.glob(dir_systeme + '/*/')
            
            # EXCLUSIONS dans le liste des répertoires du système
            # enlever planif
            for r in lstPairesPotentielles:
                if 'planif' in r:
                    lstPairesPotentielles.remove(r)
            
            # dans le cas où il n'y a pas de paire
            # il faut quand même incrémenter les compteurs d'états
            # et créer un enregistrement
            if len(lstPairesPotentielles) == 0:
                nbr_etat_NA += 1
                ligne_dict = {
                   'obs_prog': obs_prog,
                   'id_system': id_system,
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
                
            #
            # traiter les paires
            #
            for pr in lstPairesPotentielles:
                # valider s'il s'agit d'une paire
                tempo = path.basename(path.dirname(pr))
                boolPaire, paire = est_une_paire(tempo)               
                #debug print("debug {0} {1} {2}".format(pr, boolPaire, paire))
                
                # ré initialisations
                obs_prog = 'aucun'
                obsN = 'NaN'
                dateDernObs = 'aucune'
                strEtat = '?  '
                delai = 'NaN'

                # C'est une paire valide, on continue
                if boolPaire:
                    
                    # trouver la liste des programmes
                    lstProgs = glob.glob(pr + '/P*/')
                    
                    # s'il n'y à pas de programme, il faut incrémenter le
                    # compteur nbr_etat_NA
                    #debug print(lstProgs)
                    if len(lstProgs) == 0:
                        nbr_etat_NA += 1
                    
                    for prog in lstProgs:
                        if est_un_programme(prog):
                            # ajouter à la liste des programmes (uniques)
                            liste_programmes_uniques.add(path.basename(\
                                                           path.dirname(prog)))
                            #debug print('  prog ' , prog)
                            obs_prog = path.basename(path.dirname(prog))
                            
                            # s'il existe un fichier *.obj (un seul!)
                            # des sessions d'observations, alors traiter
                            # sinon il n'y a pas encore eue de post-réduction
                            fich = glob.glob(prog+'/*.obj')
                            if len(fich) == 1:
                                # charger le fichier .obj de sessions dans s
                                try:
                                    with open(fich[0], 'rb') as f:
                                        s = pickle.load(f)
                                        obsN = s.nbrN
                                        dateDernObs = s.sommaire_obs_df.loc[0,\
                                                                'dern_obs_utc']
                                        strEtat = s.sommaire_obs_df.loc[0, 'État']
                                        delai = s.sommaire_obs_df.loc[0, 'delai']
                                        
                                except FileNotFoundError:
                                    # fichier objet illisible! Continuer
                                    # tout de même
                                    pass
                            else:
                                # pas de fichier obj, alors il n'y a pas eu
                                # post-réduction
                                obsN = 'NaN'
                                dateDernObs = 'aucune'
                                strEtat = 'P  '
                                delai = 'NaN'
                            
                # faire le décompte des États 'XECPT'
                if 'P' in strEtat:
                   nbr_etat_P += 1
                if 'C' in strEtat:
                   nbr_etat_C += 1
                if 'T' in strEtat:
                   nbr_etat_T += 1
                if 'E' in strEtat:
                   nbr_etat_E += 1
                if 'X' in strEtat:
                   nbr_etat_X += 1

                #debug print('\n')
                # composer le dict des résultats
                ligne_dict = {
                   'obs_prog': obs_prog,
                   'id_system': id_system,
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
    return liste_progs
    

def imprime_liste_programmes(chemin=os.getcwd()+'/med', tri=0, impr_table_etat=True):
    '''
    Imprime un rapport détaillé des programmes d'observations et retourne un
    Pandas DataFrame contenant la liste triée des programme d'observations
    et leur état.

    Parameters
    ----------
    chemin : TYPE txt chemin
        
    tri : TYPE int, ordre de tri de 1 à 4, selon dictionnaire liste_de_tri

    impr_table_etat : TYPE booleen, optionnel

    Returns
    -------
    programmes_df : pandas.core.frame.DataFrame
    '''
    chemin_complet_rep_racine = chemin
    
    ### parcourir le répertoire racine
    print ('Le chemin de base est : ' + chemin_complet_rep_racine + '\n')

    # produire la liste et transformer résultat en df
    programmes_df = \
        pd.DataFrame(produit_liste_programmes_obs(chemin_complet_rep_racine))
    nbrEnregistrements = len(programmes_df)
    int_nbr_prog_uniques = len(liste_programmes_uniques)
   
    ### trier le résultat
    programmes_df.sort_values(by=liste_de_tri[tri], ignore_index=True,\
                              inplace=True)
    #programmes_df.fillna(' ', inplace=True)
    
    ### imprimer le rapport
    print('Trié par', liste_de_tri[tri])
    print('-' * 82)
    print(programmes_df)
    print('-' * 82)
    print("  {0:>3d} programmes différents.".format(int_nbr_prog_uniques))
    print('  {0:>3d} systèmes différents.'.format(int_nbr_systemes_exam))
    print("\r")
    
    print("   États des {0} enregistrements".format(nbrEnregistrements))
    print(' ' + '-'*35)
    print("  {0:>3d} terminés.".format(nbr_etat_T))
    print("  {0:>3d} en planification.".format(nbr_etat_P))
    print("  {0:>3d} sans programme assigné.".format(nbr_etat_NA))
    print("  {0:>3d} en cours.".format(nbr_etat_C))
    print("  {0:>3d} en délai dépassé.".format(nbr_etat_X))
    print("  {0:>3d} avec erreur.".format(nbr_etat_E))
    
    if impr_table_etat:    
        ### Liste dictionnaire des codes de notes d'observations
        print("\n Légende des codes d'état")
        print(' ' + '-'*24)
        print(' Code  [descriptions] :')
        for code in do.codes_etat_obs_dict:
            print('   {0} {1}'.format( code, do.codes_etat_obs_dict[code]))
    
    print('\nEXEMPLES DE REQUÊTES :')
    print("programmes.query(\"id_system == 'STF 982'\")")
    print("programmesquery(\"État == 'P  '\")")
    print("programmes.query(\"const == 'And'\")")
    print("programmes.query(\"const == 'And' or const == 'Gem'\")")
    return programmes_df
      
# %% inits
nversion = 10
# construire la liste de tri
liste_de_tri = [['obs_prog', 'id_system'],\
               ['id_system', 'obs_prog'],
               ['const'],
               ['Date_obs_N']]

    

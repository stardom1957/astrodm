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

def liste_info_systemes(sortie='terminal'):
    """
    Retourne un pandas dataframe des info_systemes.csv lus dans ./med.
    """
    ch = os.getcwd() + '/med'
    dirs = glob.glob(ch + r'\**\*_info_système.csv', recursive=True)
    info_systemes_df = pd.read_csv(dirs[0])
    dirs.pop(0)
    for dir in dirs:
        info_systemes_df = info_systemes_df.append(pd.read_csv(dir),ignore_index=True)
    return info_systemes_df

def est_une_paire(chaine):
    """
    Retourne un Tupple (True, paire) si la chaine (nom d'un répertoire) passée
    en paramètre «semble» être une paire valide. La valeur paire est extraire
    de chaine pour servir à une forme de normalisation.
    
    Retourne (False, 'ERREUR') si chaine ne «semble» pas être une paire valide.
      
    Paramètre positionnel
     chaine -- String nom de du répertoire (basename) à vérifier.
    """
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
    """
      Retourne True | False si le chemin passé en paramètre est un programme
      d'observation valide selon le format Paaaa-nnn; où aaaa = année
      et nnn = 000 à 999 (par ex. P2022-004).
      
    Paramètre positionnel
     chemin -- chemin du répertoire à vérifier.
    """

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


def produit_liste_reductions(chSystemes):
    """
    Balais chSystemes et retourne une liste (List) des noms complets des fichiers
    *.obj trouvés.

    Paramètre positionnel
     chSystemes -- String chemin complet de la tête du répertoire des systèmes.
    """

    return glob.glob(chSystemes+r'\**\*.obj', recursive=True)

def imprime_liste_reductions(chemin='', tri=0, impr_table_etat=True):
    """
    Imprime un rapport détaillé des programmes d'observations et retourne un
    Pandas DataFrame trié contenant la liste des programmes d'observations.

    Paramètres Keyword
     chemin          -- String chemin de tête des systèmes (par défaut '')
     tri             -- Int ordre de tri de 1 à 4, selon dictionnaire
                        liste_de_tri_prog
     impr_table_etat -- Boolean imprime légende des états (par défaut True)
    """
    
    lst_ncor = produit_liste_reductions(chemin)
    
    # enregistrements pour produire df
    liste_reductions = list()
    
    # init des compteurs
    int_nbr_obj_ses_exam, nbr_etat_T, nbr_etat_C,\
        nbr_etat_X, nbr_etat_E = 0, 0, 0, 0, 0

    liste_programmes_uniques = set()

    # ncos : nom complet objet sessions
    for ncos in lst_ncor:
        #
        # lire l'objet ncos par pickle dans obj_sessions
        #
        try:
            with open(ncos, 'rb') as f:
                obj_sessions = pickle.load(f)
                
        except FileNotFoundError:
            print("doublesListes.imprime_liste_reductions :: Fichier {0} illisible".\
                  format(ncos))
            sys.exit()

        #
        # produire l'enr sous forme d'un dictionnaire
        #
        enr_dict = {
           'obs_prog': obj_sessions.prog,
           'id_system': obj_sessions.systeme.nom,
           'paire': obj_sessions.paire,
           'const': obj_sessions.systeme.informations_df.loc[0,'const'],
           'N': obj_sessions.resultats_pour_publication_df.loc[0,'N'],
           'groupe': obj_sessions.resultats_pour_publication_df.loc[0,'groupe'],
           'Dates': obj_sessions.resultats_pour_publication_df.loc[0,'Dates'],
           'delai_entre_N': obj_sessions.resultats_pour_publication_df.loc[0,'delai_entre_N'],
           'Liste sessions (N)': obj_sessions.resultats_pour_publication_df.loc[0,'Liste sessions (N)'],
           'époque': obj_sessions.resultats_pour_publication_df.loc[0,'epoque'],
           'pa': obj_sessions.resultats_pour_publication_df.loc[0,'pa'],
           'pa_sig': obj_sessions.resultats_pour_publication_df.loc[0,'pa_sig'],
           'sep': obj_sessions.resultats_pour_publication_df.loc[0,'sep'],
           'sep_sig': obj_sessions.resultats_pour_publication_df.loc[0,'sep_sig'],
           'WDS_obs2': obj_sessions.resultats_pour_publication_df.loc[0,'WDS_o2'],
           'WDS_pa2': obj_sessions.resultats_pour_publication_df.loc[0,'WDS_pa2'],
           'WDS_sep2': obj_sessions.resultats_pour_publication_df.loc[0,'WDS_sep2'],
           
           'État': obj_sessions.resultats_pour_publication_df.loc[0,'État']
        }


        #
        # faire le décompte des États 'XECPT'
        #
        tempo = obj_sessions.resultats_pour_publication_df.loc[0,'État']
        if 'C' in tempo:
           nbr_etat_C += 1
        elif 'T' in tempo:
           nbr_etat_T += 1
        elif 'E' in tempo:
           nbr_etat_E += 1
        elif 'X' in tempo:
           nbr_etat_X += 1

        # autres compteurs
        # int_nbr_prog_uniques
        # ajouter le programme au set des programmes (uniques)
        liste_programmes_uniques.add(obj_sessions.prog)
        int_nbr_obj_ses_exam += 1

        # ajouter à lst_reduc
        liste_reductions.append(enr_dict)
    # créer reductions_df à partir de lst_reduc et trier
    reductions_df = pd.DataFrame(liste_reductions)
    reductions_df.sort_values(by=liste_de_tri_reduc[tri], ignore_index=True,\
                              inplace=True)
  
        
    #### imprimer le rapport
    print('Trié par', liste_de_tri_reduc[tri])
    print('-' * 136)

    pd.set_option('display.expand_frame_repr', True)
    pd.set_option('display.colheader_justify', 'right')
    pd.set_option('display.max_colwidth', 50)
    pd.set_option('display.max_column', 18)
    pd.set_option('display.width', 200)
    pd.set_option('display.max_row', 10000)
    pd.set_option("precision", 1)

    print(reductions_df)
    print('-' * 136)
    print("  {0:>3d} programmes différents.".format(len(liste_programmes_uniques)))
    print('  {0:>3d} objets sessions examinés.'.format(int_nbr_obj_ses_exam))
    print("\r")
    
    print("   États des {0} enregistrements".format(len(reductions_df)))
    print(' ' + '-'*35)
    print("  {0:>3d} terminés.".format(nbr_etat_T))
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
    print("reductions.query(\"id_system == 'STF 982'\")")
    print("reductions.query(\"État == 'P  '\")")
    print("reductions.query(\"const == 'And'\")")
    print("reductions.query(\"const == 'And' or const == 'Gem'\")")
    return reductions_df
    
        


def produit_liste_programmes_obs(ch):
    """
    Parcoure le chemin ch et retourne une liste (List) des programmes
    d'observations.

    Paramètre positionnel
    ch -- String chemin complet de la tête du répertoire des systèmes.
    """
    #
    # initialisations
    #

    global int_nbr_systemes_exam, liste_programmes_uniques
    global nbr_etat_C, nbr_etat_T, nbr_etat_P, nbr_etat_X, nbr_etat_E,\
        nbr_etat_NA
    
    nbr_etat_X, nbr_etat_E, nbr_etat_C, nbr_etat_T, nbr_etat_P, nbr_etat_NA,\
        int_nbr_systemes_exam = 0, 0, 0, 0, 0, 0, 0
    liste_progs = list()
    liste_programmes_uniques = set()
    
    # obtenir la liste des dir (systemes) dans ch
    dirSystemes = glob.glob(ch + '/*')
    for dir_systeme in dirSystemes:
        # passer par-dessus la liste d'exclusions
        if path.basename(dir_systeme) not in ('cal_e', 'planif'):
            id_system, id_WDS, const, paire, obs_prog, dateDernObs =\
                None, None, None, 'aucune', 'aucun', 'aucune'
            obsN, delai = 'NaN', 'NaN'
            strEtat = '?  '
            int_nbr_systemes_exam += 1
            
            id_system = path.basename(dir_systeme)
            #debug print('traitement ' + id_system)

            # rechercher fichier «source + '_info_système.csv'»
            lstFichiers = glob.glob(dir_systeme + '/*_info_système.csv')
            assert len(lstFichiers) == 1, "Erreur : plus d'un _info_système.csv dans «{0}»".\
                  format(id_system)
                 
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
            # enlever 'planif'
            for r in lstPairesPotentielles:
                if path.basename(r.rstrip(r'\\')) in 'planif':
                    lstPairesPotentielles.remove(r)
            
            # dans le cas où il n'y a pas de paire, automatiquement il n'y a
            # pas de programme. Donc, il faut quand même créer un enregistre-
            # ment et incrémenter le nombre de systèmes sans affectation de
            # programme
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
                    
                    # s'il n'y à pas de programme, il faut aussi créer
                    # l'enregistrement et incrémenter le
                    # compteur nbr_etat_NA et ajouter l'enregistrement à la
                    # liste
                    if len(lstProgs) == 0:
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
                        liste_progs.append(ligne_dict)
                    
                    for prog in lstProgs:
                        if est_un_programme(prog):
                            # ajouter au set des programmes (uniques)
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
                                        dateDernObs = s.resultats_pour_publication_df.loc[0,\
                                                                'Dates']
                                        strEtat = s.resultats_pour_publication_df.loc[0, 'État']
                                        delai = s.resultats_pour_publication_df.loc[0, 'delai_entre_N']
                                        
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
                            
                        # faire le décompte des États 'XECPT' trouvés dans
                        # objet .obj
                        if 'P' in strEtat:
                           nbr_etat_P += 1
                        elif 'C' in strEtat:
                           nbr_etat_C += 1
                        elif 'T' in strEtat:
                           nbr_etat_T += 1
                        elif 'E' in strEtat:
                           nbr_etat_E += 1
                        elif 'X' in strEtat:
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
    

def imprime_liste_programmes(chemin='', tri=0, impr_table_etat=True, sortie='T'):
    """
    Imprime un rapport détaillé des programmes d'observation et retourne un
    Pandas DataFrame contenant la liste triée des programmes d'observation
    et leurs états.

    Paramètres Keyword
     chemin          -- String chemin du répertoire de tête des systèmes
     tri             -- Int ordre de tri de 1 à 4, selon dictionnaire
                        liste_de_tri_prog
     impr_table_etat -- Boolean imprime légende des états (par défaut True)
     sortie          -- Car 'T' pour terminal ou 'D' pour disque

    Returns
    -------
    programmes_df : pandas.core.frame.DataFrame
    """
    #
    # redirection de stdout vers un fichier le cas échéant
    #
    if sortie == 'F':
        # sortie vers fichier ./med/planif/Liste_programmes_<systag>.txt
        systag = do.produire_systag()
        ncfis = os.getcwd() + '/med/planif/Liste_prog_observations_' + systag + '.txt'
        ancien_stdout = sys.stdout
        f = open(ncfis, 'w')
        sys.stdout = f
    
    ### parcourir le répertoire racine
    print("Liste des programmes d'observations dans : " + chemin + '\n')

    # produire la liste et transformer résultat en df
    programmes_df = \
        pd.DataFrame(produit_liste_programmes_obs(chemin))
    nbrEnregistrements = len(programmes_df)
    int_nbr_prog_uniques = len(liste_programmes_uniques)
   
    ### trier le résultat
    programmes_df.sort_values(by=liste_de_tri_prog[tri], ignore_index=True,\
                              inplace=True)
    #programmes_df.fillna(' ', inplace=True)
    
    #### imprimer le rapport
    print('Trié par', liste_de_tri_prog[tri])
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
    
    # inutile d'imprimer ces exemples si stdout est redirigé vers un fichier
    if sortie != 'F':
        print('\nEXEMPLES DE REQUÊTES :')
        print("programmes.query(\"id_system == 'STF 982'\")")
        print("programmesquery(\"État == 'P  '\")")
        print("programmes.query(\"const == 'And'\")")
        print("programmes.query(\"const == 'And' or const == 'Gem'\")")

    if sortie == 'F':
        # rétablir stdout
        sys.stdout = ancien_stdout
        f.close()
        print("Sortie dans :\n  {0}".format(ncfis))

    return programmes_df
      
# %% INITIALISATIONS
nversion = 10
# construire la liste de tri
liste_de_tri_prog = [['obs_prog', 'id_system'],\
               ['id_system', 'obs_prog'],
               ['const'],
               ['Date_obs_N']]

    
liste_de_tri_reduc = [['obs_prog', 'id_system'],\
               ['id_system', 'obs_prog'],
               ['const'],
               ['dern_obs_utc']]

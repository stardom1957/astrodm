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
from datetime import datetime
from astropy.time import Time
import numpy as np

# insérer le chemin suivant dans sys.path pour trouver le package astrodm
if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesoutils as do

# %% INITIALISATIONS
### pandas options d'affichage des tables
pd.set_option('display.expand_frame_repr', True)
pd.set_option('display.colheader_justify', 'right')
pd.set_option('display.max_colwidth', 50)
pd.set_option('display.max_column', 15)
pd.set_option('display.width', 150)
pd.set_option('display.max_row', 10000)
pd.set_option("display.precision", 1)

# %% FONCTIONS
def version():
    #print("doublesListeProgrammes version " + str(nversion))
    print(__name__ + ' ' + str(nversion))

def trouverFichierObjetSessions(ch):
    """
    Retourne le nom du fichier log de réduction (REDUC) RLog_*.txt 
    si présent dans le chemin passé en paramètre une chaîne vide sinon.

    Paramètre positionnel :
    ch -- String chemin du dossier d'où commencer la recherche.
    """

    for root, dirs, files in os.walk(ch):
        for name in files:
            if os.path.isfile(os.path.join(root, name)):
                if 'RLog_' in name:
                    #debug return os.path.join(root, name)
                    return name
    return None


def liste_info_systemes(sortie='terminal'):
    """
    Retourne un pandas dataframe des info_systemes.csv lus dans ./med.
    """
    ch = os.getcwd() + '/med'
    #debug dirs = glob.glob(ch + r'\**\*_info_système.csv', recursive=True)
    dirs = glob.glob(ch + r'\**\info-systeme.csv', recursive=True)
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
    
    Retourne (False, 'aucune') si chaine ne «semble» pas être une paire valide.
      
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
            return False, 'aucune'
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


def produit_liste_reductions(chemin_des_systemes):
    """
    Balais chemin_des_systemes et retourne une liste (List) des noms complets des fichiers
    *.obj trouvés.

    Paramètre positionnel
     chemin_des_systemes -- String chemin complet de la tête du répertoire des systèmes.
    """

    return glob.glob(chemin_des_systemes+r'\**\*.obj', recursive=True)

def imprime_liste_reductions(chemin='', tri=0, impr_table_etat=True, sortie='T'):
    """
    Imprime un rapport détaillé des programmes d'observations et retourne un
    Pandas DataFrame trié contenant la liste des programmes d'observations.

    Paramètres Keyword
     chemin          -- String chemin de tête des systèmes (par défaut '')
     tri             -- Int ordre de tri de 1 à 4, selon dictionnaire
                        liste_de_tri_prog
     impr_table_etat -- Boolean imprime légende des états (par défaut True)
     sortie          -- T (terminal) ou F (fichier)
    """
    
    if sortie == 'F':
        # sortie vers fichier ./med/med-planification/....txt
        systag = do.produire_systag()
        
        # construire chaîne ordre de tri
        tempo = ""
        for eltri in liste_de_tri_reduc[int(tri)]:
            tempo = tempo + eltri + "+"
        tempo = tempo.rstrip("+")
        tempo = "(" + tempo + ")"
        ncfliste = os.getcwd() + '/med/med-planification/LISTES/reductions-par' + tempo + "-"  + systag + '.txt'
        
        # rediriger sortie vers f
        ancien_stdout = sys.stdout
        f = open(ncfliste, mode='w', encoding="utf-8")
        sys.stdout = f


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
            return None

        # # int_nbr_prog_uniques
        # ajouter le programme au set des programmes (uniques)
        liste_programmes_uniques.add(obj_sessions.prog)
        int_nbr_obj_ses_exam += 1

        #
        # produire l'enregistrement à partir de resultats_pour_publication_df
        # sous forme d'un dictionnaire
        #
        if len(obj_sessions.resultats_pour_publication_df) != 0:
            for index_s in obj_sessions.resultats_pour_publication_df.index:
                enr_dict = {
                   'obs_prog': obj_sessions.prog,
                   'id_system': obj_sessions.systeme.nom,
                   'paire': obj_sessions.paire,
                   'const': obj_sessions.systeme.informations_df.loc[0,'const'],
                   'N': obj_sessions.resultats_pour_publication_df.loc[index_s,'N'],
                   'groupe': obj_sessions.resultats_pour_publication_df.loc[index_s,'groupe'],
                   'Dates_UTC': obj_sessions.resultats_pour_publication_df.loc[index_s,'Dates_UTC'],
                   'delai_entre_N': obj_sessions.resultats_pour_publication_df.loc[index_s,'delai_entre_N'],
                   'Sessions': obj_sessions.resultats_pour_publication_df.loc[index_s,'Sessions'],
                   'Époque': obj_sessions.resultats_pour_publication_df.loc[index_s,'epoque'],
                   'pa': obj_sessions.resultats_pour_publication_df.loc[index_s,'pa'],
                   'pa_sig': obj_sessions.resultats_pour_publication_df.loc[index_s,'pa_sig'],
                   'sep': obj_sessions.resultats_pour_publication_df.loc[index_s,'sep'],
                   'sep_sig': obj_sessions.resultats_pour_publication_df.loc[index_s,'sep_sig'],
                   'WDS_obs2': obj_sessions.resultats_pour_publication_df.loc[index_s,'WDS_o2'],
                   'WDS_pa2': obj_sessions.resultats_pour_publication_df.loc[index_s,'WDS_pa2'],
                   'WDS_sep2': obj_sessions.resultats_pour_publication_df.loc[index_s,'WDS_sep2'],
                   'État': obj_sessions.resultats_pour_publication_df.loc[index_s,'État']
                }
                #
                # faire le décompte des États 'XECPT'
                #
                tempo = obj_sessions.resultats_pour_publication_df.loc[index_s,'État']
                if 'C' in tempo:
                   nbr_etat_C += 1
                elif 'T' in tempo:
                   nbr_etat_T += 1
                elif 'E' in tempo:
                   nbr_etat_E += 1
                elif 'X' in tempo:
                   nbr_etat_X += 1
        
                # ajouter à lst_reduc
                liste_reductions.append(enr_dict)

    # créer reductions_df à partir de lst_reduc et trier
    if len(liste_reductions) == 0:
        print("Il n'y a aucune réductions.")
        
        # rétablir sortie vers sys.stdout
        if sortie == 'F':
            # rétablir stdout
            sys.stdout = ancien_stdout
            f.close()
            print("Sortie dans :\n  {0}".format(ncfliste))
        return None
    else:
        reductions_df = pd.DataFrame(liste_reductions)
        reductions_df.sort_values(by=liste_de_tri_reduc[tri], ignore_index=True,\
                                  inplace=True)
            
        #### imprimer le rapport
        print('Trié par', liste_de_tri_reduc[tri])
        print('\r')
        #print('-' * 176)
    
        pd.set_option('display.expand_frame_repr', True)
        pd.set_option('display.colheader_justify', 'right')
        pd.set_option('display.max_colwidth', 50)
        pd.set_option('display.max_column', 18)
        pd.set_option('display.width', 300)
        pd.set_option('display.max_row', 10000)
        pd.set_option("precision", 3)
    
        print(reductions_df)
        #print('-' * 176)
        print('\r')
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


        # rétablir sortie vers sys.stdout
        if sortie == 'F':
            # rétablir stdout
            sys.stdout = ancien_stdout
            f.close()
            print("Sortie dans :\n  {0}".format(ncfliste))
        return reductions_df
    

def produire_liste_progammes(ch):
    """
    Parcoure le chemin ch et retourne un pandas dataframe des programmes
    d'observations.

    Paramètre positionnel
    ch -- String chemin complet de la tête du répertoire des systèmes.
    """
    #
    # initialisations
    #
    global int_nbr_systemes_exam, liste_programmes_uniques, lst_prog_df
    global int_nbr_systemes_exam
    global nbr_etat_C, nbr_etat_T, nbr_etat_P, nbr_etat_X, nbr_etat_R,\
       nbr_etat_NA, nbr_etat_E
    nbr_etat_X, nbr_etat_R, nbr_etat_C, nbr_etat_T, nbr_etat_P, nbr_etat_NA, nbr_etat_E = 0, 0, 0, 0, 0, 0, 0

    int_nbr_systemes_exam = 0
    liste_programmes_uniques = set()
    
    #
    # construire le df vide des programme avec les colonnes suivantes :
    lstCol = [
       'obs_prog', 'id_system', 'paire', 'id_WDS', 'const',
       'Sessions', 'Dates_UTC', 'délai (j)', 'écheance', 'État'
    ]
       
    lst_prog_df = pd.DataFrame(list(), columns=lstCol)
    
    # obtenir la liste des dir (systemes) dans ch
    dirSystemes = glob.glob(ch + '/*/')
    for dir_systeme in dirSystemes:
        # initialisations
        obs_prog = 'aucun'
        id_system = None
        paire = 'aucune'
        id_WDS = None
        const = None
        lst_sessions = list()
        lst_sessions.append(np.nan)
        Dates_UTC = 'S. o.'
        delai = np.nan
        str_dth_echeance_utc = 'S. o.'
        etat = '  ?'
        
        # traiter le répertoire système
        # (en passant par-dessus la liste d'exclusions)
        if path.basename(path.dirname(dir_systeme)) not in ('cal_e', 'med-planification', '.ipynb_checkpoints'):
            lst_dates = list()
            lst_dates.append('s. o.')
            int_nbr_systemes_exam += 1
            
            id_system = path.basename(path.dirname(dir_systeme))
            #debug print('traitement ' + id_system)

            # rechercher fichier 'info-systeme.csv'»
            lstFichiers = glob.glob(dir_systeme + '/info-systeme.csv')
            assert len(lstFichiers) == 1, "Erreur de recherche *info-systeme.csv dans «{0}»".\
                  format(dir_systeme)
                 
            # lire info_système
            # ouvrir le fichier info_source
            informations_df = pd.read_csv(lstFichiers[0])
            #debug print(informations_df)

            # lire id_WDS et const
            #debug id_system = informations_df.loc[0, 'id_system']
            id_WDS = informations_df.loc[0, 'id_WDS']
            const = informations_df.loc[0, 'const']
            
            # bâtir la liste des paires potentielles présentent
            # dans dir_systeme
            lstPairesPotentielles = glob.glob(dir_systeme + '/*/')
            
            # EXCLUSIONS dans la liste des répertoires du système
            # enlever 'planif'
            for r in lstPairesPotentielles:
                if path.basename(r.rstrip(r'\\')) in 'planif':
                    lstPairesPotentielles.remove(r)
            
            # dans le cas où il n'y a pas de paire, automatiquement il n'y a
            # pas de programme. Donc, il faut quand même créer un enregistre-
            # ment et incrémenter le nombre de systèmes sans affectation de
            # programme
            if len(lstPairesPotentielles) == 0:
                # construire l'enregistrement
                data = [
                   obs_prog,
                   id_system,
                   paire,
                   id_WDS,
                   const,
                   lst_sessions,
                   Dates_UTC,
                   delai,
                   str_dth_echeance_utc,
                   etat
                ]
                # ajouter à la liste des programmes et incrémenter le compteur
                # approprié
                lst_prog_df.loc[lst_prog_df.index.size] = data
                nbr_etat_NA += 1
            
            else:
                #
                # traiter les paires dans lstPairesPotentielles
                #
                for chemin_paire in lstPairesPotentielles:
                    # ré initialisations
                    obs_prog = 'aucun'
                    lst_sessions = list()
                    lst_sessions.append(np.nan)
                    Dates_UTC = 's. o.'
                    delai = np.nan
                    str_dth_echeance_utc = 's. o.'
                    etat = '  ?'
                    lst_dates = list()
                    lst_dates.append('s. o.')
    
                    # valider s'il le chemin est bien celui d'une paire
                    tempo = path.basename(path.dirname(chemin_paire))
                    boolPaire, paire = est_une_paire(tempo)               
                    #debug print("debug {0} {1} {2}".format(chemin_paire, boolPaire, paire))
                    # si c'est une paire valide
                    # on recherche les programmes
                    
                    if boolPaire:
                        # trouver la liste des programmes
                        lstProgs = glob.glob(chemin_paire + '/P*/')
                        
                        if len(lstProgs) == 0:
                            # s'il n'y à pas de programme, il faut quand même créer
                            # l'enregistrement, l'ajouter au df et
                            # incrémenter le compteur approprié

                            data = [obs_prog, id_system, paire, id_WDS, const, lst_sessions, Dates_UTC, delai, str_dth_echeance_utc, etat]
                            # ajouter à la liste des programmes
                            lst_prog_df.loc[lst_prog_df.index.size] = data
                            nbr_etat_NA += 1
                        else:
                            # on traite chacun des programmes dans lstProgs
                            for chemin_prog in lstProgs:
                                # ré initialisations
                                obs_prog = 'aucun'
                                lst_sessions = list()
                                lst_sessions.append(np.nan)
                                Dates_UTC = 's. o.'
                                delai = np.nan
                                str_dth_echeance_utc = 's. o.'
                                etat = '  ?'
                                lst_dates = list()
                                lst_dates.append('s. o.')
                                
                                if est_un_programme(chemin_prog):
                                    # ajouter au set des programmes (uniques)
                                    liste_programmes_uniques.add(path.basename(path.dirname(chemin_prog)))
                                    #debug print('  chemin_prog ' , chemin_prog)
                                    obs_prog = path.basename(path.dirname(chemin_prog))
                                    
                                    #
                                    # vérifier s'il existe au moins un S et au moins
                                    # in bloc dans ce S
                                    #
                                    pasDeBlocs = True
                                    lstDesRepS = glob.glob(chemin_prog + '/S*/')
                                    nbr_de_rep_S = len(lstDesRepS)
                                    if nbr_de_rep_S != 0:
                                        # chercher s'il y a au moins un bloc dans
                                        # le premier S
                                        listeRepBlocs = glob.glob(lstDesRepS[0] + '/b*/')
                                        if len(listeRepBlocs) != 0:
                                            pasDeBlocs = False
                                        
                                    if pasDeBlocs:
                                        # il n'y a pas de bloc dans S, donc
                                        # état = 'P'
                                        etat = 'P L'
                                        data = [obs_prog, id_system, paire, id_WDS, const, lst_sessions, Dates_UTC, delai, str_dth_echeance_utc, etat]
                                        # ajouter à la liste des programmes
                                        lst_prog_df.loc[lst_prog_df.index.size] = data
                                        nbr_etat_P += 1
                                    else:
                                        # il existe au moins un bloc dans S,
                                        # alors vérifier la présence d'un
                                        # objet *.obj pour voir s'il y a eu
                                        # au moins une post-réduction

                                        # nom complet fichier objet ncfo
                                        ncfo = chemin_prog + '/' + id_system + '_' + paire + '_' + obs_prog  + '_sessions.obj'
    
                                        if path.exists(ncfo):
                                            # lire fichier objet
                                            #debug print("debug lire", ncfo)
                                            try:
                                                with open(ncfo, 'rb') as f:
                                                    s = pickle.load(f)
                                            except FileNotFoundError:
                                                # fichier objet illisible! ou «major fuck up»
                                                print("fichier objet présent mais illisible!")
                                                sys.exit()
                                            
                                            # déterminer si s est à jour
                                            #
                                            
                                            # déterminer la signature (checksum MD5 des fichiers log
                                            # et reduc présents dans le programme)
                                            
                                            checksum = do.calcule_ckecksum_fichiers(s.cheminProgramme)

                                            if s.checksum != checksum:
                                                # ************ Les données ont changées! ****************
                                                # il faut lancer une post-réduction
                                                s = do.post_reduction(type_session='complete', ch_prog=chemin_prog)
                                                        
                                        else:
                                            # il n'y a pas d'objet s,
                                            # il n'y a donc pas eu de réduction exécutée
                                            # mais nous savons qu'il peut exister des 
                                            # données d'acquisition valides...
                                            # on exécute donc une post-réduction ;)
                                            s = do.post_reduction(type_session='complete', ch_prog=chemin_prog)
                                                            
                                        # à partir d'ici on peut « raisonnablement » assumer que s est à jour
                                        # on récupère les données directement de chaque session de l'objet s et
                                        # on traite selon qu'il y a eue une réduction ou non
                                        
                                        #################################################################                                        
                                        # TRAITEMENT DE resultats_pour_publication_df
                                        # d'abord récupérer les sessions resultats_pour_publication_df
                                        # qui comprend toutes les sessions avec un 'T  ' et possèdent
                                        # déjà un code d'état
                                        
                                        for index_s in s.resultats_pour_publication_df.index:
                                            lst_dates = s.resultats_pour_publication_df.loc[index_s, 'Dates_UTC']
                                            lst_sessions = s.resultats_pour_publication_df.loc[index_s, 'Sessions']
                                            etat = s.resultats_pour_publication_df.loc[index_s, 'État']
                                            delai = s.resultats_pour_publication_df.loc[index_s, 'delai_entre_N']
                                            Dates_UTC = s.resultats_pour_publication_df.loc[index_s, 'Dates_UTC']
                                            str_dth_echeance_utc = s.resultats_pour_publication_df.loc[index_s, 'Échéance']
                                            
                                            #TODO récupérer échéance dans s.resultats_pour_publication_df
                                            # si maintenant > échéance, alors actualiser état
                                            # dans s.resultats_pour_publication_df et sauvegarder (pickle) s
                                            # etat 'C L' --> 'TAL', puis enregister objet s
                                            
                                            # construire l'enregistrement
                                            data = [obs_prog, id_system, paire, id_WDS, const, lst_sessions, Dates_UTC, delai, str_dth_echeance_utc, etat]
                                            # ajouter à la liste des programmes
                                            lst_prog_df.loc[lst_prog_df.index.size] = data
                                            
                                            # incrémenter le compteur approprié
                                            #debug if 'P' in etat:
                                            #debug   nbr_etat_P += 1
                                            #debug elif 'C' in etat:
                                            #debug    nbr_etat_C += 1
                                            #debug if 'T' in etat:
                                                
                                            # il n'y a que des sessions terminée dans resultats_pour_publication_df
                                            nbr_etat_T += 1

                                        ########################################################################
                                        # TRAITEMENT DES AUTRES SESSIONS
                                        # s'il reste des sessions qui ne se retrouvent pas dans s.resultats_pour_publication_df,
                                        # les information d'état et le cas échéant, l'échéance ont été calculée lors de la post-réduction
                                        # et se trouvent donc dans l'objet session
                                        
                                        for index_session in range(len(s.lstObjSession)):
                                            if not s.lstObjSession[index_session].reductionCompletee:
                                                # il s'agit des cas qui ont des acquisitions non pré-réduites
                                                # donc avec un R ou un X si aucun bloc valide
                                                # ici on a besoin de date_utc_acq de l'un
                                                # des blocs. En principe, cette valeur est 
                                                # la même pour tous les blocs, mais comme il
                                                # est possible que l'un des blocs ne soit pas valide
                                                # il vaut mieux parcourir la liste des blocs de la
                                                # session et récupérer la date d'exécution UTC d'un des
                                                # blocs valide
                                                #
                                                lst_sessions = '[' + str(s.lstObjSession[index_session].noSession) + ']'
                                                for index_bloc in range(len(s.lstObjSession[index_session].lstBlocs)):
                                                    if s.lstObjSession[index_session].lstBlocs[index_bloc].sep.valide:
                                                        Dates_UTC = s.lstObjSession[index_session].lstBlocs[index_bloc].sep.dtime_utc_acq.value.split('T')[0]
                                                        
                                                        # calculer date d'échéance
                                                        # si moins de 7 jours alors etat = 'CRL' ou 'CEL'
                                                        # sinon etat = 'TRL'
                                                        #debug str_dth_echeance_utc = 'à calculer selon les blocs'
                                                        # calculer le délai
                                                        
                                                        dtUTC_acquisition_sep = s.lstObjSession[index_session].lstBlocs[index_bloc].sep.dtime_utc_acq
                                                        lst_dates = list()
                                                        lst_dates.append(dtUTC_acquisition_sep.value.split('T')[0])
                        
                                                        # dans ce cas, il faut calculer la date
                                                        # d'échéance de l'observation qui est
                                                        # la date unique qui se trouve dans lst_dates
                                                        # + do.MAX_DELAI_ENTRE_OBSERVATIONS
                                                        #
                                                        #debug dth_echeance_utc = do.str_dt_isot_a_TimeIsot(dt=dtUTC_acquisition_sep) + do.MAX_DELAI_ENTRE_OBSERVATIONS
                                                        
                                                        dth_echeance_utc = dtUTC_acquisition_sep + do.MAX_DELAI_ENTRE_OBSERVATIONS
                                                        #debug str_dth_echeance_utc = dth_echeance_utc.value.split('T')[0]
                                                        #TODO est-ce OK?
                                                        str_dth_echeance_utc = dth_echeance_utc.to_value('isot').split('T')[0]
                                                        if s.lstObjSession[index_session].au_moins_un_bloc_valide:
                                                            if maintenant > dth_echeance_utc:
                                                                etat = 'TRL'
                                                                nbr_etat_T += 1
                                                                nbr_etat_R += 1
                                                            else:
                                                                etat = 'CRL'
                                                                nbr_etat_C += 1
                                                                nbr_etat_R += 1
                                                        else:
                                                            etat = 'TXL'
                                                            nbr_etat_X += 1
                                                            nbr_etat_T += 1

                                                        #debug delai = round(do.diff_dt(maintenant.isoformat(), dth_echeance_utc.value),1)
                                                        delai = round(abs((maintenant - dth_echeance_utc).value), 1)
                                                    else:
                                                        # il reste seulement le cas etat = 'P L'
                                                        etat = 'P L'
                                                        nbr_etat_P += 1
                                                        delai = np.nan
                                                
                                                # construire l'enregistrement
                                                data = [obs_prog, id_system, paire, id_WDS, const, lst_sessions, Dates_UTC, delai, str_dth_echeance_utc, etat]
                                                # ajouter à la liste des programmes
                                                lst_prog_df.loc[lst_prog_df.index.size] = data
                                            else:
                                                # il s'agit du cas où une réduction à eue lieue
                                                # donc il aura un C ou un X si aucun bloc valide
                                                # ici on a besoin de date_utc_acq de l'un
                                                # des blocs valides.
                                                #
                                                pass

                                            
                                else:
                                    # le dossier n'est pas valide pour un
                                    # programme, alors il n'y a rien à traiter
                                    # et on passe
                                    pass
                        
                    else:
                        # le dossier n'est pas valide pour une paire, alors
                        # il n'y a rien a traiter et on passe
                        pass

    return lst_prog_df


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
        systag = do.produire_systag()
        
        # construire chaîne ordre de tri
        tempo = ""
        for eltri in liste_de_tri_prog[tri]:
            tempo = tempo + eltri + "+"
            
        tempo = tempo.rstrip("+")
        ncfis = os.getcwd() + '/med/med-planification/LISTES/prog-obs-par(' + tempo + ")-" + systag + '.txt'
        ancien_stdout = sys.stdout
        f = open(ncfis, mode='w', encoding="utf-8")
        sys.stdout = f
    
    ### parcourir le répertoire racine
    print("Liste des programmes d'observations dans : " + chemin + '\n')

    # produire la liste et transformer résultat en df
    programmes_df = produire_liste_progammes(chemin)
    nbrEnregistrements = len(programmes_df)
    int_nbr_prog_uniques = len(liste_programmes_uniques)
   
    ### trier le résultat
    programmes_df.sort_values(by=liste_de_tri_prog[tri], ignore_index=True,\
                              inplace=True)
    #programmes_df.fillna(' ', inplace=True)
    
    #### imprimer le rapport
    print('Trié par', liste_de_tri_prog[tri])
    #print('-' * 82)
    print('\r')
    print(programmes_df)
    #print('-' * 82)
    print('\r')

    print("  {0:>3d} programmes différents.".format(int_nbr_prog_uniques))
    print('  {0:>3d} systèmes différents.'.format(int_nbr_systemes_exam))
    print("\r")
    
    print("   États des {0} enregistrements".format(nbrEnregistrements))
    print(' ' + '-'*35)
    print("  {0:>3d} (T) terminés (voir description du code du centre).".format(nbr_etat_T))
    print("  {0:>3d} (P) en planification.".format(nbr_etat_P))
    print("  {0:>3d} (?) sans programme | paire assigné.".format(nbr_etat_NA))
    print("  {0:>3d} (C) en cours.".format(nbr_etat_C))
    print("  {0:>3d} (R) avec données prêtes pour la PRÉ-RÉDUCTION.".format(nbr_etat_R))
    print("  {0:>3d} (X) avec données inutilisables (voir journal de réduction).".format(nbr_etat_X))
    
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
        print("liste_des_programmes_df.query(\"id_system == 'STF 982'\")")
        print("liste_des_programmes_df.query(\"État == 'P  '\")")
        print("liste_des_programmes_df.query(\"const == 'And'\")")
        print("liste_des_programmes_df.query(\"const == 'And' or const == 'Gem'\")")

    if sortie == 'F':
        # rétablir stdout
        sys.stdout = ancien_stdout
        f.close()
        print("Sortie dans :\n  {0}".format(ncfis))

    return programmes_df
      
# %% INITIALISATIONS
nversion = 20
# construire la liste de tri
liste_de_tri_prog = [['obs_prog', 'id_system'],\
               ['id_system', 'obs_prog'],
               ['const']]

    
liste_de_tri_reduc = [['obs_prog', 'id_system'],\
               ['id_system', 'obs_prog'],
               ['const']]

# maintenant utilisé pour calculer les échéances
# format de <class 'astropy.time.core.Time'> avec scale utc car
# tous les dt sont UTC
maintenant = Time(datetime.utcnow(), scale='utc')

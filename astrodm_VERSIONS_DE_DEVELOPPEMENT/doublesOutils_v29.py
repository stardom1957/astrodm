# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 16:35:23 2020

@author: Dominique Martel
Produit un rapport des observations des mesures de séparation et
angle de position d'une paire d'étoiles doubles.

version 29
"""

# %% imports et définition des constantes
import glob
import pandas as pd
import math
import sys
import numpy as np
from astropy import units as u
#from astropy.coordinates import SkyCoord
#from astropy.time import Time, TimezoneInfo, TimeEpochDate, TimeBesselianEpoch
from astropy.time import Time, TimezoneInfo
from datetime import datetime
from astroquery.vizier import Vizier as v

# %% DÉFINITIONS
'''
Crée un dictionnaire des codes de notes pour les
observations d'étoiles doubles
'''
notes_obs_dict = {
    'X': ['Délais dépassé, à reprendre.'],
    'E': ['Erreur irrécupérable ou résultats incorrects. P. e. mauvaise paire mesurée.'],
    'C': ["en cours d'observation."],
    'P': ['en cours de PLANIFICATION.'],
    'M': ['mesure par Microguide.'],
    'R': ['mesure par Lucky Imaging : REDUC.'],
    'A': ['mesure par autre méthode, voir fichier _observations.csv.'],
    'T': ['Terminé. Au moins 2 observations complétées. Réduction complète.']
}

# %% FONCTIONS

def constantes():
    '''
    Définition des constantes utilisées dans astrodm.
     - Baader Planetarium Microguide : échelles ("/divE_mg2) de chaque instrumentation.
     - Caméras : (à venir) modèles, échelle nominale, etc.

    Returns
    -------
    None.
    

    '''
    ### Baader Planetarium Microguide
    # instrumentations nx (nx Barlow 1x, 2x, 5x)
    # Échelles étalonnées (programme 2018-012)
    # par ex. échelle Microguide 2x en "/divE_mg2 = 3.01
    # incertitude en "/div
    # création d'un dictionnaire des échelles [echelle, delta]
    global echelleMG, intEchelle, intDeltaE
    echelleMG = {'Microguide 1x':[np.nan, np.nan], 'Microguide 2x':[3.66, 0.005], 'Microguide 5x':[3.01, 0.005]}
    intEchelle = 0 # index pour obtenir l'échelle de la liste
    intDeltaE  = 1 # index pour obtenir delta échelle de la liste

def rech_wds(src, paire):
    '''
    Recherche les informations de src et paire au catalogue WDS ('B/wds/wds').

    Parameters
    ----------
    src : TYPE str
        La désignation de découvreur du système (source) recherché.
    paire : str
        La paire, sous la forme 'ab', 'a,bc', etc ou '*' si toutes les paires
        sont recherchées.

    Returns
    -------
    TYPE astroquery.utils.commons.TableList
        Le résultat de la recherche sous la forme d'une table.

    '''
    
    # caractères de remplacement ? pour l'éventuelle 4e lettre, p. e. «stfa 60»
    ### transformer src pour recherche WDS
    # pour 'stfa nn' ==> 'stf? nn'
    # si car 4 est une lettre, replacer par '?'
    v.CACHE = False
    v.ROW_LIMIT = 120000 # au cas où ?
    global strSource_format_pour_Notes
    strSource = strSource_format_pour_Notes = src
    
    spl = src.split(' ')
    if len(spl) == 2: # cas type 'stfa 60'
        if len(spl[0]) == 4 and len(spl[1]) == 2:
            strSource = spl[0][:3] + '? ' + spl[1]
            strSource_format_pour_Notes = spl[0][:3] + '? ' + spl[1]
        else:
            if len(spl[0]) == 3 and len(spl[1]) == 2: # cas type 'stf 60'
                strSource = spl[0][:3] + ' ' + spl[1]
                strSource_format_pour_Notes = spl[0][:3] + '  ' + spl[1]
            elif len(spl[0]) == 3 and len(spl[1]) == 3:
                strSource = src
                strSource_format_pour_Notes = spl[0][:3] + ' ' + spl[1]
            elif len(spl[0]) == 3 and len(spl[1]) == 1:
                strSource = src
                strSource_format_pour_Notes = spl[0] + '   ' + spl[1]

    else:
        if len(spl) == 1: # cas type 'stf2398'
            # on assume que spl[0] contient le nom
            strSource = strSource_format_pour_Notes = src
    
    ### soumettre la requête
    
    return v.query_constraints(catalog='B/wds/wds', Disc=strSource, Comp=paire)

    # variations avec critère Obs2
    #result = v.query_constraints(catalog='B/wds/wds', Disc=source, Comp=paire, Obs2='<=2015')
    ##result = v.query_constraints(catalog='B/wds/wds', Disc=source, Comp=paire, Obs2='2011..2015')

def rech_wds_notes(src):
    '''
    Recherche les notes au sujet de src dans les notes au WDS ('B/wds/notes'), si présentes.

    Parameters
    ----------
    src : TYPE str
        La désignation de découvreur du système recherché.

    Returns
    -------
    TYPE astroquery.utils.commons.TableList
        Il s'agit d'une table des résultats.

    '''
    ### obtenir WDS Notes
    # il faut normaliser strSource sur 7 car pour la recherche dans les notes
    # du WDS
    spl = src.split(' ')
    if len(spl) == 2: # cas type 'stfa 60'
        if len(spl[0]) == 4 and len(spl[1]) == 2:
            nom_src_format_pour_notes = spl[0][:3] + '? ' + spl[1]
        else:
            if len(spl[0]) == 3 and len(spl[1]) == 2: # cas type 'stf 60'
                nom_src_format_pour_notes = spl[0][:3] + '  ' + spl[1]
            elif len(spl[0]) == 3 and len(spl[1]) == 3:
                nom_src_format_pour_notes = spl[0][:3] + ' ' + spl[1]
            elif len(spl[0]) == 3 and len(spl[1]) == 1:
                nom_src_format_pour_notes = spl[0] + '   ' + spl[1]

    else:
        if len(spl) == 1: # cas type 'stf2398'
            # on assume que spl[0] contient le nom
            nom_src_format_pour_notes = src

    notes_q = v.query_constraints(catalog='B/wds/notes', Disc=nom_src_format_pour_notes)
    #wds_notes
    if notes_q != []:
        # garder seulement les deux dernières colonnes
        notes_q[0].keep_columns(['Text', 'RefCode'])
    return notes_q
        
def info_src_wds(src, paire, notes=True):
    '''
    
    Fonction de recherche qui imprime les résultats de recherche dans le catalogue
    WDS.
    
    Parameters
    ----------
    src : TYPE src
        La désignation de découvreur du système recherché.
    paire : TYPE
        La paire, sous la forme 'ab', 'a,bc', etc ou '*' si toutes les paires
        sont recherchées.
    notes : TYPE, bool, optional
        True :: recherche et imprime les notes si présentent au catalogue
        'B/wds/notes'.
        La valeur par défaut est True.

    Returns
    -------
    None. Impression des résultats.

    '''
    strSource = src.upper()
    # pour toutes les paires strPaire = '*'
    strPaire = paire.upper()
    
    ### soumettre la requête à WDS
    qres = rech_wds(strSource, strPaire)
    
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
        wds_notes = rech_wds_notes(strSource)
        
        if notes:
            if wds_notes != []:
                print('\n ***** WSD Notes pour {0} *****'.format(strSource))
                wds_notes[0].pprint(max_width=120)
            else:
                print('Aucune note trouvée.')
    
    else:
        print("La requête pour '{0}' n'a donné aucun résultat".format(strSource))
        sys.exit()


def regle_env_exec(modei=False, impre=False, imprd=False, imprs=False):
    '''
    Règles environement des variables bool pour exécution.

    Parameters
    ----------
    modei : TYPE, optional
        DESCRIPTION. The default is False.
    impre : TYPE, optional
        DESCRIPTION. The default is False.
    imprd : TYPE, optional
        DESCRIPTION. The default is False.
    imprs : TYPE, optional
        DESCRIPTION. The default is False.

    Returns
    -------
    None.

    '''
    global bool_mode_interactif, bool_imprEn_tete, bool_imprDetails, bool_imprSommaire
    bool_mode_interactif = modei
    bool_imprEn_tete = impre
    bool_imprDetails = imprd
    bool_imprSommaire = imprs


def reduireObservations(nom_complet_fichier_info, chemin_rep_prog_obs):
    '''
    Réduit toutes les observations valides dans le fichier _observations.csv
    situé dans chemin_rep_prog_obs.

    Parameters
    ----------
    nom_complet_fichier_info : TYPE
        DESCRIPTION.
    chemin_rep_prog_obs : TYPE
        DESCRIPTION.

    Returns
    -------
    resultat_dict : TYPE dictionnaire
    resultat_dict = {
        'theta_moy': theta_moy,
        'delta_theta': delta_theta,
        'rho_moy': rho_moy,
        'delta_rho': delta_rho,
        'epoque_moy': epoque_moy
    }.

    '''
    ### régler pour mode script
    regle_env_exec(False, False, False, False)
    
    ### initialisations
    constantes()
    inits()

    #selection_interactive_fichier_info_et_rep_programme()
    ### lire fich info, observations et mesures

    lire_informations_et_observations(nom_complet_fichier_info, chemin_rep_prog_obs)
    lire_fichiers_mesures(chemin_rep_prog_obs)

    ### calcul (réduction)
    calculeObservations()
    calculeMoyennes()

    ### produire le dictionnaire des résultats
    #    theta_moy, delta_theta, rho_moy, delta_rho, epoque_moy
    resultat_dict = {
        'theta_moy': theta_moy,
        'delta_theta': delta_theta,
        'rho_moy': rho_moy,
        'delta_rho': delta_rho,
        'epoque_moy': epoque_moy
    }

    return resultat_dict


def creeDateHeureLocal(dhl):
    decallageUTCdhl = int(dhl.rsplit('UTC')[1])
    utc_dhl = TimezoneInfo(utc_offset=decallageUTCdhl*u.hour)
    ### enlever le UTC de la date
    tempo = dhl.split('U')[0]

    ### convertir la date et heure en int (en utilisant list comprehension)
    lst_int_dhl = [int(i) for i in tempo.split('T')[0].split('-')]
    lst_int_heure_dhl = [int(i) for i in tempo.split('T')[1].split(':')]
    a = lst_int_dhl[0]
    m = lst_int_dhl[1]
    j = lst_int_dhl[2]
    h = lst_int_heure_dhl[0]
    mi = lst_int_heure_dhl[1]
    s = lst_int_heure_dhl[2]
    
    ### créer un datetime qui contient l'information de fuseau horaire
    return datetime(a, m, j, h, mi, s, tzinfo=utc_dhl)

def calculeMoyennes():
    global rho_moy, delta_rho, theta_moy, delta_theta, epoque_moy
    global rhos, thetas, epoques

    # créer des ndarray à partir des listes
    rhos = np.array(lstRhos)
    thetas = np.array(lstThetas)
    epoques = np.array(lstIntEpoquesB)
    
    ### calcul des moyennes et des incertitudes
    rho_moy = rhos.mean(axis=0)[0]
    # delta_rho en quadrature : racine carrée de la somme des carrés des delta_rho
    delta_rho = np.sqrt(np.sum(np.square(rhos[:,1])))
    
    theta_moy = thetas.mean(axis=0)[0]
    # delta_theta en quadrature : racine carrée de la somme des carrés des delta_theta
    delta_theta = np.sqrt(np.sum(np.square(thetas[:,1])))

    epoque_moy = epoques.mean(axis=0)
    

def calculeObservations():
    for ob in range(Nobs):
        # note : obs + 1 est le no d'observation N dans les rapports
        # instrumentation de l'observation courante
        strInstrCourante = observations_df.loc[ob, 'instrument']
    
        # obtenir le temps local du début d'observation et déterminer l'époque Besselienne
        strObsDateHeure_local_Debut = observations_df.loc[ob, 'obs_debut']
        
        # créer un datetime jeure locale (qui contient l'information de fuseau horaire)
        dtObsDateHeure_local_Debut = creeDateHeureLocal(strObsDateHeure_local_Debut)
        
        # créer un objet astropy.Time.Time qui convertit le datetime en UTC
        ObsDateHeure_local_Debut_UTC = Time(dtObsDateHeure_local_Debut)
        
        # placer époque Besselienne de l'observation dans la liste
        lstIntEpoquesB.append(ObsDateHeure_local_Debut_UTC.byear)
        
        if bool_imprDetails and bool_mode_interactif:
            print('\n')
            print('*' * 40)
            print('{0:^40s}'.format('OBSERVATION ' + str(ob + 1)))
            print('*' * 40)
            print('\n')
            
        ### TRAITEMENT DE RHO
        ### traitement des valeurs aberrantes de séparation
        # les valeurs négatives de m1 sont des valeurs aberrantes et doivent être enlevées
        # index (no de ligne) de tous les m1 <= 0 :: marqués pour supression du jeux de données
        idx_mesures_abb = mesures_sep[ob].query('m1 <= 0').index

        if idx_mesures_abb.size != 0:
            if bool_mode_interactif:
                print('*' * 55)
                print('  RHO - MESURES ABERRANTES SUPPRIMÉES OBSERVATION ' + str(ob + 1))
                print('  (marquées par valeurs mesurée de m1 * -1)')
                print('*' * 55)
                print(mesures_sep[ob].query('m1 <= 0'))
                print('\n')

            # ensuite on les enlève
            mesures_sep[ob] = mesures_sep[ob].drop(idx_mesures_abb)

        
        ### ajouter une colonne "abs(m0-m1)" calculant abs(m0 - m1) à mesures_sep
        mesures_sep[ob]["abs(m0-m1)"] = abs(mesures_sep[ob]["m0"] - mesures_sep[ob]["m1"])

        if bool_imprDetails and bool_mode_interactif:
            print('{0:^40s}'.format('MICROGUIDE - MESURES BRUTES'))
            print('-' * 40)
            print(mesures_sep[ob], '\n')
       
        '''
        mesures_sep_cour["m"].describe() donne les statistiques descriptive de mesures_sep_cour["m=abs(diff)"]
        Mais on calcule ces résultats dans des variables séparées
        '''
        ### calcul statistiques descriptive séparation
        m_min = mesures_sep[ob]["abs(m0-m1)"].min()
        m_max = mesures_sep[ob]["abs(m0-m1)"].max()
        m_moy = mesures_sep[ob]["abs(m0-m1)"].mean()
        sigma_m = mesures_sep[ob]["abs(m0-m1)"].std()
    
        ### propagation des incertitudes de rho
        delta_m = (2 * sigma_m) / math.sqrt(mesures_sep[ob]["abs(m0-m1)"].count())

        if bool_imprDetails and bool_mode_interactif:
            # debug print('*' * 40)
            print('STATISTIQUES DESCRIPTIVES DES abs(m0-m1)')
            print('-' * 40)
            
            print('            m_min {0:>7.2f} div'.format(m_min))
            print('            m_max {0:>7.2f} div'.format(m_max))
            print('            m_moy {0:>7.2f} div'.format(m_moy))
            print('          sigma_m {0:>7.2f} div'.format(sigma_m))
            print('          delta_m {0:>7.2f} div'.format(delta_m))
            print('nombre de mesures {0:>4d}\n'.format(mesures_sep[ob].index.size))
    
        ### calcul de rho ± delta_rho selon l'échelle
        # de l'instrumentation de l'observation en cours
    
        rho = m_moy * echelleMG[strInstrCourante][intEchelle]
        # propagation des incertitudes
        delta_rho = (delta_m / m_moy) + (echelleMG[strInstrCourante][intDeltaE] / echelleMG[strInstrCourante][intEchelle])
        
        #
        ### TRAITEMENT DE THETA
        #

        ### traitement des valeurs aberrantes de theta
        # les valeurs négatives de theta sont des valeurs aberrantes et doivent être enlevées
        # index (no de ligne) de tous les m1 <= 0 :: marqués pour supression du jeux de données
        idx_mesures_abb = theta_brut[ob].query('theta_brut <= 0').index
        
        if idx_mesures_abb.size != 0:
            if  bool_mode_interactif:
                print('  THETA - MESURES ABERRANTES SUPPRIMÉES OBSERVATION ' + str(ob + 1))
                print('  (marquées par valeurs mesurée de theta_brut * -1)')
                print('-' * 55)
                print(theta_brut[ob].query('theta_brut <= 0'))
                print('\n')

            # ensuite on les enlève
            theta_brut[ob] = theta_brut[ob].drop(idx_mesures_abb)

        ## on continue avec les calculs

        if bool_imprDetails and bool_mode_interactif:
            # debug print('*' * 40)
            print('{0:^40s}'.format('THETA - MESURES BRUTES'))
            print('-' * 40)
            print(theta_brut[ob], '\n')

        ### calculs statistiques descriptives des mesures de theta brut
        theta_brut_min = theta_brut[ob]['theta_brut'].min()
        theta_brut_max = theta_brut[ob]['theta_brut'].max()
        theta_brut_moy = theta_brut[ob]['theta_brut'].mean()
        sigma_theta_brut = theta_brut[ob]['theta_brut'].std()
        
        ### propagation des incertitudes theta_brut = theta
        delta_theta = (2 * sigma_theta_brut) / math.sqrt(theta_brut[ob]['theta_brut'].count())
        
        if bool_imprDetails and bool_mode_interactif:
            # debug print('*' * 40)
            print('STATISTIQUES DESCRIPTIVES DE THETA BRUT')
            print('-' * 40)
            
            print('   theta_brut_min {0:>12.2f}'.format(theta_brut_min))
            print('   theta_brut_max {0:>12.2f}'.format(theta_brut_max))
            print('   theta_brut_moy {0:>12.2f}'.format(theta_brut_moy))
            print(' sigma_theta_brut {0:>12.2f}'.format(sigma_theta_brut))
            print(' delta_theta_brut {0:>12.2f}'.format(delta_theta))
            print('nombre de mesures {0:>9d}\n'.format(theta_brut[ob].index.size))
        
        ### correction instrumentale de l'échelle circulaire du Microguide
        theta = theta_brut_moy + 90
        if theta > 360:
            theta -= 360
        
        ### RHO / THETA courants dans deux listes
        # enregistrement des résultats de l'observation courante dans les listes
        #
        lstRhos.append([rho, delta_rho])
        lstThetas.append([theta, delta_theta])

'''
def lire_fichier_codes_notes_obs():
    global notes_obs_df
    notes_obs_df = pd.read_csv(os.getcwd() + '\\codes_notes_obs.csv')
'''

def lire_fichiers_mesures(ch_rep_programme):
    for ob in range(Nobs):
        ### trouver fichier mesures de séparation courant dans liste_fichiers_csv
        for fichier in liste_fichiers_csv:
            if '_sep_N' + str(ob + 1) + '.csv' in fichier:
                break
        if '_sep_N' + str(ob + 1) + '.csv' in fichier:
            mesures_sep.append(pd.read_csv(fichier))
        else:
            print('Fichier {0} non trouvé. Sortie programme.'.format('_mesures_separation_N' + str(ob + 1)))
            sys.exit()

        ### trouver le fichier de mesure theta brut dans liste_fichiers_csv
        for fichier in liste_fichiers_csv:
            if '_theta_N' + str(ob + 1) + '.csv' in fichier:
                break
        if '_theta_N' + str(ob + 1) + '.csv' in fichier:
            theta_brut.append(pd.read_csv(fichier))
        else:
            print('Fichier {0} non trouvé. Sortie programme.'.format('_mesures_theta_brut_N' + str(ob +1)))
            sys.exit()
    

def inits():
    global lstRhos, lstThetas, lstIntEpoquesB, mesures_sep, theta_brut, notes_obs_dict

    ### pandas options d'affichage des tables
    pd.set_option('display.expand_frame_repr', True)
    pd.set_option('display.colheader_justify', 'right')
    pd.set_option('display.max_colwidth', 50)
    pd.set_option('display.max_column', 30)
    pd.set_option('display.width', 80)
    
    ### Initialisation des listes
    # créer les listes des mesures de rho, delta_rho et theta delta_theta
    lstRhos = list() # paires de listes rho, delta_rho pour chaque observation
    lstThetas = list() # paire de listes theta, delta_theta pour chaque observation
    ### liste des époque Besseliennes d'observation et mesures
    lstIntEpoquesB = list()
    mesures_sep = []
    theta_brut = []


def lire_informations_et_observations(nom_compl_fich_info, chemin_rep_programme):
    global Nobs, queryWDS_result, informations_df, observations_df, paire, no_premiere_obs, liste_fichiers_csv
    ### obtenir liste fichiers csv
    liste_fichiers_csv = glob.glob(chemin_rep_programme + '\\mesures\\*.csv')

    ### LIRE FICHIERS «info_système» et «observations»
    informations_df = pd.read_csv(nom_compl_fich_info)
    
    # trouver le nom du fichier des observations dans liste_fichiers_csv
    for fichier in liste_fichiers_csv:
        if '_observations.csv' in fichier:
            break
    
    ### obtenir Nobs, no observation et paire observée
    if '_observations.csv' in fichier:
        observations_df = pd.read_csv(fichier, dtype={'N':pd.Int8Dtype(), 'transp':pd.Int8Dtype()})
    
        # nombre d'enregistrement dans observations_df
        Nobs = observations_df.loc[:, 'N'].count()
    
        # no de la première observation listée
        no_premiere_obs = observations_df.loc[0, 'N']
        
        # la paires ne change pas d'une observation à l'autre dans le même programme
        paire = observations_df.loc[0, 'paire'].replace('"', '')

    else:
        print('Fichier observations non trouvé. Sortie programme.')
        sys.exit()
    
    # si no_premiere_obs == 0 il faut sortir car il n'y a pas encore de données valides
    ### TESTER no_premiere_obs
    if pd.isna(no_premiere_obs):
        print('ATTENTION !')
        print("N est <NA> dans fichier «{0}». Il n'y a probablement pas de données valides.".\
              format(fichier))
        print('Vétifiez la liste des fichiers ci-dessus.\n Sortie du programme.\n')
        print('*' * 15)
        print(observations_df)
        print('*' * 15)
        sys.exit()
    
    ### du WDS, obtenir données astrométriques de la source et paire
    
    #queryWDS_result = recherche_WDS(informations_df.loc[0, 'id_source'], paire.upper())
    queryWDS_result = rech_wds(informations_df.loc[0, 'id_source'], paire.upper())


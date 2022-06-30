# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 16:35:23 2020

@author: Dominique Martel
Produit un rapport des observations des mesures de séparation et
angle de position d'une paire d'étoiles doubles.
"""

# %% imports et définition des constantes
import os
import glob
import pandas as pd
import math
import sys
import numpy as np
from tkinter import Tk
from tkinter.filedialog import askdirectory
from tkinter.filedialog import askopenfile
from astropy import units as u
#from astropy.coordinates import SkyCoord
from astropy.time import Time, TimezoneInfo, TimeEpochDate, TimeBesselianEpoch
from datetime import datetime
from astroquery.vizier import Vizier as v

# insérer le chemin suivant dans sys.path pour trouver le package astro_doubles
if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
import astro_doubles as ad
#import cree_notes_observations_dict_v02 as cno

# %% FONCTIONS
# doit être utilisé en mode module
def reduireObservations(nom_complet_fichier_info, chemin_rep_prog_obs):
    global bool_mode_interactif, bool_imprEn_tete, bool_imprDetails, bool_imprSommaire
    ### régler pour mode script
    bool_mode_interactif = bool_imprEn_tete = bool_imprDetails = bool_imprSommaire = False
    
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

def recherche_WDS(src, paire):
    # caractères de remplacement ? pour l'éventuelle 4e lettre, p. e. «stfa 60»
    ### transformer src pour recherche WDS
    # pour 'stfa nn' ==> 'stf? nn'
    # si car 4 est une lettre, replacer par '?'
    v.CACHE = False
    v.ROW_LIMIT = 150 # au cas où ?
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

def imprimeEn_tete():
    print('Chemin répertoire des mesures : ', ch_repertoire_programme_obs)
    print('\nListe des fichiers de données :')
    print(liste_fichiers_csv, '\n')

    ### lister le fichier informations_df (au sujet de la source)
    print('*' * 80)
    print('{0:^80s}'.format('INFORMATIONS SYSTÈME'))
    print('-' * 80)
    print(informations_df, '\n')
    
    ### Liste (du fichier) des observations
    print('*' * 80)
    print('{0:^80s}'.format('OBSERVATIONS'))
    print('-' * 80)
   
    print(observations_df, '\n')
    # debug test extraction du début des observations dans une table (série selon pandas)
    #tblDateObs = observations["obs_debut"][0], observations["obs_debut"][1]
    #tblDateObs
    
    ### Liste dictionnaire des codes de notes d'observations
    #lire_fichier_codes_notes_obs()
    #pd.set_option('display.max_colwidth', 100)
    #cno.cree_notes_obs_dict()
    print('\nNotes :')
    
    for code in ad.notes_obs_dict:
        print(code, ad.notes_obs_dict[code])

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
    
def imprimeSommaire():
    print('\n')
    print('*' * 40)
    print('{0:^40s}'.format("SOMMAIRE DES OBSERVATIONS"))
    print('*' * 40)
    print('\n')
   
    ### imprimer le résultat de chaque observation obs : N=1,...
    for obs in range(Nobs):
        print('{0:^40s}'.format('THETA / RHO OBSERVATION ' + str(obs + 1)))
        #print('     THETA / RHO OBSERVATION ' + str(obs + 1))
        print('-' * 40)
        print('  theta ± delta_theta : {0:>7.2f}° ± {1:>4.2f}°'.format(thetas[obs][0], thetas[obs][1]))
        print('      rho ± delta_rho : {0:>7.2f}" ± {1:>4.2f}"'.format(rhos[obs][0], rhos[obs][1]))
        print('               époque :   B{0:>6.4f}\n'.format(lstIntEpoquesB[obs]))
    
    #
    ### RÉSULTAT FINAL THETA / RHO
    #
    print('-' * 40)
    print('{0:^40s}'.format("RÉSULTAT FINAL N=" + str(Nobs)))
    print('{0:^40s}'.format('MOYENNE THETA / RHO'))
    print('-' * 40)
    print('  theta ± delta_theta : {0:>7.2f}° ± {1:>4.2f}°'.format(theta_moy, delta_theta))
    print('      rho ± delta_rho : {0:>7.2f}" ± {1:>4.2f}"\n'.format(rho_moy, delta_rho))
    
    #print('{0:>5.1f}°/{1:>6.2f}"'.format(theta, rho))
    print('         jcd : {0:>4.1f}° / {1:>4.2f}" B{2:>9.4f}'.format(theta_moy, rho_moy, epoque_moy))
    
    ### WDS dernière mesure formatée
    # WDS imprimer dernière mesure (formatée) suivie de l'info complète
    if queryWDS_result != []:
        print('  WDS (Obs2) : {0:>5d}° / {1:>4.2f}" {2:4>d}\n\n'.format(queryWDS_result[0][0]['pa2'], queryWDS_result[0][0]['sep2'], queryWDS_result[0][0]['Obs2']))
        print('Données tirée du Washington Double Star Catalog* Citation à compléter')
        print('-' * 120)
        ### informations complètes du WDS
        queryWDS_result[0].pprint(show_unit=True, max_width=120)
        print('-' * 120)
    else:
        print('  WDS : source introuvable!')

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
    
        # propagation des incertitudes de rho
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
        
        # propagation des incertitudes theta_brut = theta
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
    
def constantes():
    # Baader Planetarium Microguide instrumentations nx (nx Barlow 2x, 5x, etc)
    # Échelles étalonnées (programme 2018-012)
    # échelle Microguide 2x en "/divE_mg2 = 3.01
    # incertitude en "/div
    ### création d'un dictionnaire des échelles [echelle, delta]
    global echelleMG, intEchelle, intDeltaE
    echelleMG = {'Microguide 2x':[3.66, 0.005], 'Microguide 5x':[3.01, 0.005]}
    intEchelle = 0 # index pour obtenir l'échelle de la liste
    intDeltaE  = 1 # index pour obtenir delta échelle de la liste

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

def selection_interactive_fichier_info_et_rep_programme():
    global observatoires, nom_complet_fichierInfo, ch_repertoire_programme_obs
    
    ### Sélectionner répertoire source (par tkinter)
    # lire le fichier observatoires dans le réperoire d'exécution
    observatoires = pd.read_csv(os.getcwd() + '\observatoires.csv')
    #print('Fichier observatoires.csv non trouvé. Sortie programme.')
    #sys.exit()
    
    root = Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()
    
    # sélectionner le fichier des informations de la source
    tempo = askopenfile(mode ='r', filetypes =[('Fichiers «info_système»', '*.csv')], title = 'Sélectionner fichier information système')
    nom_complet_fichierInfo = tempo.name
    
    # sélectionner le répertoires du programme d'observations
    # trouver racine du répertoire système afin de positionner la recherche de répertoire de mesures à cet endroit
    tempo = nom_complet_fichierInfo.split(sep='/')
    racine_repertoire_systeme = tempo[len(tempo)-1].split('_')[0]
    titre = "Sélectionner le répertoire du programme d'observation"
    
    ch_repertoire_programme_obs = askdirectory(initialdir=racine_repertoire_systeme, title = titre, parent=root)

'''
def obtenir_nom_fichier_info_et_rep_mesures(fich):
    global observatoires, nom_complet_fichierInfo, ch_repertoire_programme_obs, liste_fichiers_csv
    # fich contient le nom du fichier d'observations
    # il faut trouver le nom du fichier informations correspondant
    print('traitement de {0}'.format(fich))
    sys.exit()
    ### Sélectionner répertoire source (par tkinter)
    # lire le fichier observatoires dans le réperoire d'exécution
    observatoires = pd.read_csv(os.getcwd() + '\observatoires.csv')
    #print('Fichier observatoires.csv non trouvé. Sortie programme.')
    #sys.exit()
    
    root = Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()
    
    # sélectionner le fichier des informations de la source
    nom_complet_fichierInfo = askopenfile(mode ='r', filetypes =[('Fichiers «info_système»', '*.csv')], title = 'Ouvrir fichier information système')
    
    # sélectionner le répertoires des mesures
    # trouver racine du répertoire système afin de positionner la recherche de répertoire de mesures à cet endroit
    tempo = nom_complet_fichierInfo.name.split(sep='/')
    racine_repertoire_systeme = tempo[len(tempo)-1].split('_')[0]
    titre = 'Sélectionner le répertoire des mesures'
    
    ch_repertoire_programme_obs = askdirectory(initialdir=racine_repertoire_systeme, title = titre, parent=root)
    
    os.chdir(ch_repertoire_programme_obs)
    liste_fichiers_csv = glob.glob('*.csv')
'''


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
    queryWDS_result = ad.recherchewds.rech_wds(informations_df.loc[0, 'id_source'], paire.upper())


# %% PRINCIPAL
if __name__ == "__main__":
    # on est en mode interactif
    bool_mode_interactif = True
    bool_imprEn_tete = False
    bool_imprDetails = False
    bool_imprSommaire = False
    
    constantes()
    inits()
    selection_interactive_fichier_info_et_rep_programme()
    lire_informations_et_observations(nom_complet_fichierInfo, ch_repertoire_programme_obs)
    lire_fichiers_mesures(ch_repertoire_programme_obs)
    
    ### SAISIR INTENSION IMPRESSION EN-TÊTE
    rep = input("Imprimer l'en-tête (o|n)? ").upper()
    if 'O' in rep:
        bool_imprEn_tete = True
    
    ### SAISIR INTENSION IMPRESSION DÉTAILS OBSERVATIONS
    rep = input("Imprimer détails d'observations (o|n)? ").upper()
    if 'O' in rep:
        bool_imprDetails = True
    
    ### SAISIR INTENSION IMPRESSION SOMMAIRE
    rep = input('Imprimer sommaire (o|n)? ').upper()
    if 'O' in rep:
        bool_imprSommaire = True
    
    ### IMPRIMER L'EN-TÊTE du rapport : informations et observations
    if bool_imprEn_tete:
        imprimeEn_tete()
    
    ### calcul (réduction)
    calculeObservations()
    calculeMoyennes()
    
    ### IMPRIMER LES RÉSULTATS DES OBSERVATIONS (SOMMAIRE)
    #
    if bool_imprSommaire:
        imprimeSommaire()

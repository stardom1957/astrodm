# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 16:31:40 2020

@author: dominique
version 10
"""

#%% IMPORTS
import os
import glob
import pandas as pd
import numpy as np
from tkinter import Tk
from tkinter.filedialog import askdirectory
from tkinter.filedialog import askopenfile

import sys
# insérer le chemin suivant dans sys.path pour trouver le package astro_doubles
if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesOutils as do

# %% SAISIE DES DONNÉES MANUELLEMENT < = ALLEZ ICI !!!!
def creer_df_info_obs_avec_dict():
    global informations_df, observations_df
    ### dict info source
    informations_dict = {
      'id_source': ['stfa58'.upper()],
      'id_WDS': ['à venir'],
      'RAJ2000': ['à venir'],
      'DEJ2000': ['à venir'],
      'id_source_alt1': ['"del Cep"'], ###########ATTENTION GARGER " SI NÉCESSAIRE P. E. pour une ','
      'id_source_alt2': ['HIP 110991/110998'],
      'const': ['Cep'],
      'remarques': ['info AVDS #168']
    }
    informations_df = pd.DataFrame(informations_dict)
    
    ### dict observations
    observations_dict = {
       # N=np.nan, si encore observée
       # p. e. [np.nan] seulement observation != np.nan seront considérées à l'analyse
       'N': [np.nan],
       'observatoire': ['Résidence'],
       'observateur': ['Dominique Martel'],
       'obs_prog': ['2021-023'],
       # paire "*" == PPL (Pas de Paire Listée dans WDS)
       'paire': ['"ac"'.upper()], ############## ATTENTION GARDEZ GUILLEMETS
       # transp = np.cast['int8'](n) ou np.nan, si non noté
       'transp': [np.nan],
       # seeing = non noté, si non noté
       'seeing': ['non noté'],
       # temp = np.nan, si non noté
       'temp': [16.1],
       # humid = np.nan, si non notée
       'humid': [82],
       # press_bar = np.nan, si non notée
       'press_bar': [np.nan],
       'obs_debut': ['2021-10-08T20:49:47UTC-4'],
       'obs_fin': ['2021-10-08T20:52:01UTC-4'],
       'telescope': ['Celestron EdgeHD 8'],
       #'instrument': ['Microguide 5x'],
       #'instrument': ['Microguide 2x'],
       'instrument': ['Lucky Imaging'],
       # index_cal_e = index de calibration d'échelle
       # au momemt de l'observation sous la forme '2021-12-07b1'
       'index_cal_e': ['2021-10-08b02'],
       'remarques': ['Premier essai avec LI'],
       # notes toujour 3 car. avec dernier = méthode d'observation
       # voir do.notes_obs_dict
       'notes': ['P  ']
    }
    observations_df = pd.DataFrame(observations_dict)

# %% FONCTIONS
def enregistrer_fichiers():
    ### création des répertoires par récursion
    os.makedirs(ch_rep_mesures, exist_ok=True)
    # mesures\N1 et N2
    os.makedirs(ch_rep_mesures + '\\N1', exist_ok=True)
    os.makedirs(ch_rep_mesures + '\\N2', exist_ok=True)

    # ...N1\b1 bloc1 d'observation N1
    os.makedirs(ch_rep_mesures + '\\N1\\b1', exist_ok=True)


    # ...N1\b1\cal pos et sep
    os.makedirs(ch_rep_mesures + '\\N1\\b1\\cal', exist_ok=True)
    os.makedirs(ch_rep_mesures + '\\N1\\b1\\\pos', exist_ok=True)
    os.makedirs(ch_rep_mesures + '\\N1\\b1\\\sep', exist_ok=True)

    # ...N2\b1 bloc1 d'observation N2
    os.makedirs(ch_rep_mesures + '\\N2\\b1', exist_ok=True)

    # ...N2\cal pos et sep
    os.makedirs(ch_rep_mesures + '\\N2\\b1\\cal', exist_ok=True)
    os.makedirs(ch_rep_mesures + '\\N2\\b1\\pos', exist_ok=True)
    os.makedirs(ch_rep_mesures + '\\N2\\b1\\sep', exist_ok=True)

    # reduc
    os.makedirs(ch_rep_reduc, exist_ok=True)
    # reduc\N1 et N2
    os.makedirs(ch_rep_reduc + '\\N1', exist_ok=True)
    os.makedirs(ch_rep_reduc + '\\N2', exist_ok=True)

    # traitement
    os.makedirs(ch_rep_traitement, exist_ok=True)
    
    ### enregistrement fichier information système
    bool_enregistrer = True
    if os.path.exists(nom_complet_fichier_information_systeme):
        rep = input('Le fichier «{0}» existe déjà ! Écraser ? (o/n) : '.\
                    format(nom_complet_fichier_information_systeme)).upper()
        if 'O' not in  rep:
            bool_enregistrer = False
            print('  Enregistrement annulé !')

    if bool_enregistrer:
        informations_df.to_csv(nom_complet_fichier_information_systeme, index=False, encoding='utf-8')
        print('Fichier information système enregistré.')

    ### enregistrement fichier observations
    bool_enregistrer = True
    if os.path.exists(nom_complet_fichier_observations):
        rep = input('Le fichier «{0}» existe déjà ! Écraser ? (o/n) : '.\
                    format(nom_complet_fichier_observations)).upper()
        if 'O' not in rep:
            bool_enregistrer = False
            print('   Enregistrement annulé !')

    if bool_enregistrer:
        observations_df.to_csv(nom_complet_fichier_observations, index=False, encoding='utf-8')
        print('Fichier observations enregistré.')

    ### toujours enregistrer data (modèles)
    #mesures_sep_df.to_csv(nom_complet_fichier_mesures_rho_modele, index=False, encoding='utf-8')
    #mesures_theta_df.to_csv(nom_complet_fichier_mesures_theta_modele, index=False, encoding='utf-8')
    


def creer_df_data():
    ### dict mesures _sep_Nx.csv ######### ATTENTION NE PAS CHANGER CECI
    global mesures_sep_df, mesures_theta_df
    mesures_sep_dict = {
        'm0': [np.nan],
        'm1': [np.nan]
    }
    mesures_sep_df = pd.DataFrame(mesures_sep_dict)
    
    ### dict mesures _theta_Nx.csv ######### ATTENTION NE PAS CHANGER CECI
    mesures_theta_dict = {
        'theta_brut': [np.nan]
    }
    mesures_theta_df = pd.DataFrame(mesures_theta_dict)
    

def prepare_structure_rep_et_fichiers(src, obs_prog):
    global nom_systeme_compact, nom_rep_progr_obs
    global nom_complet_fichier_information_systeme, nom_complet_fichier_observations
    global nom_complet_fichier_mesures_rho_modele, nom_complet_fichier_mesures_theta_modele
    global ch_rep_mesures, ch_rep_reduc, ch_rep_traitement
    global chemin_rep_racine

    ### PRÉPARATION STRUCTURE RÉPERTOIRES ET FICHIERS
    '''
    chemin complet relatif à chemin_rep_racine
    chaque chemin complet  créé par os.mkdirs, p. e. : STF60\P2021-014\AB\mesures
    p. e. fichier information système : SFT60\SFT60_info_système.csv
    p. e. fichier observations : STF60\P2021-014\AB\mesures\SFT60_observations.csv
    
    où AB est la paire
    '''
    ### chemins des dossiers de base
    # racine = répertoire d'exécution de ce module
    chemin_rep_racine = os.getcwd() + '\\'
    nom_systeme_compact = src.replace(' ', '')
    
    # ici programme comprend paire comme '2021-025\\AB'
    nom_rep_progr_obs = 'P' + obs_prog.replace(' ', '')
    ch_rep_mesures = chemin_rep_racine + nom_systeme_compact + '\\' + nom_rep_progr_obs +\
        '\\mesures\\'

    # dossier de base des réductions 'reduc'
    ch_rep_reduc = chemin_rep_racine + nom_systeme_compact + '\\' + nom_rep_progr_obs +\
        '\\reduc\\'
    
    ch_rep_traitement = chemin_rep_racine + nom_systeme_compact + '\\' + nom_rep_progr_obs +\
        '\\traitement\\'
    
    ### fichiers
    nom_complet_fichier_information_systeme = chemin_rep_racine + nom_systeme_compact +\
        '\\' + nom_systeme_compact + '_info_système.csv'
    
    nom_complet_fichier_observations = chemin_rep_racine + nom_systeme_compact +\
        '\\' + nom_rep_progr_obs + '\\mesures\\' + nom_systeme_compact + '_observations.csv'
    
    '''
    nom_complet_fichier_mesures_rho_modele = ch_rep_mesures +  nom_systeme_compact + '_sep_Nx.csv'
    nom_complet_fichier_mesures_theta_modele = ch_rep_mesures + nom_systeme_compact + '_theta_Nx.csv'
    '''


def selectionner_et_lire_infoSource_et_observations():
    global informations_df, observations_df, Nobs, paire, lstFichiersData
    global bool_informations_df_OK, bool_observations_df_ok
   
    ### Sélectionner répertoire source
    root = Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()
    
    # sélectionner le fichier des informations de la source
    nom_complet_fich_info = askopenfile(mode ='r', filetypes =[('Fichiers «info_système»', '*.csv')],\
     title = 'Sélectionnez le fichier information système')

    # sélectionner le répertoire de la paire mesurée
    # trouver racine du répertoire système afin de positionner la recherche de répertoire de mesures à cet endroit
    racine_repertoire_systeme = os.path.basename(nom_complet_fich_info.name)
    
    titre = "Sélectionnez le répertoire du programme d'observations"
    nom_rep_prog_obs = askdirectory(initialdir=racine_repertoire_systeme, title = titre, parent=root)
    
    #os.chdir(nom_rep_prog_obs)
    lstFichiersData = glob.glob(nom_rep_prog_obs + '\\mesures\\*.csv')
    print('Chemin répertoire des mesures : ', nom_rep_prog_obs)
    print('\nListe des fichiers de données :')
    lstTempo = []
    for i in range(len(lstFichiersData)):
        lstTempo.append(lstFichiersData[i].replace(nom_rep_prog_obs + '\\mesures\\', ''))
    print(lstTempo)
    print('\n')
    del lstTempo
    
    ### LIRE FICHIERS «info_système» et «observations»
    informations_df = pd.read_csv(nom_complet_fich_info)
    
    # trouver le nom du fichier des observations dans lstFichiersData
    for fichier in lstFichiersData:
        if '_observations.csv' in fichier:
            break
    ### obtenir Nobs, no observation et paire observée
    if '_observations.csv' in fichier:
        observations_df = pd.read_csv(fichier, dtype={'N':pd.Int8Dtype(), 'transp':pd.Int8Dtype()})
        #observations_df = pd.read_csv(fichier)
    
        # nombre d'enregistrement dans observations_df
        Nobs = observations_df.loc[:, 'N'].count()
       
        # la paires ne change pas d'une observation à l'autre dans le même programme
        paire = observations_df.loc[0, 'paire'].replace('"', '')
    else:
        print('Fichier observations non trouvé. Sortie programme.')
        sys.exit()
    


# %% Réglages de l'environnement d'exécution
### pandas options d'affichage des tables
pd.set_option('display.expand_frame_repr', True)
pd.set_option('display.colheader_justify', 'right')
pd.set_option('display.max_colwidth', 50)
pd.set_option('display.max_column', 30)
pd.set_option('display.width', 80)


# %% INITIALISATIONS
pass

# %% PRINCIPAL
if __name__ == '__main__':
    # à partir de novembre 2021, on ne crée que des dossiers avec la structure du
    # Lucky Imaging (voir dev\STF60\2021-012\AB comme ex.)
    # voir version 9 pour module opérationnel pour la structure Microguide
    
    ### saisir intention lecture jeu de fichiers
    rep = input("Lire un jeu de fichiers (o|n) ? ").upper()
    bool_lire_fichiers = False
    if 'O' in rep:
        bool_lire_fichiers = True
        selectionner_et_lire_infoSource_et_observations()
        # ajouter colonnes des coord si non présentes (tester sur 'RAJ2000')
        if 'RAJ2000' not in informations_df.columns:
            # insérer RAJ2000 et REJ2000, resp., après id_WDS
            informations_df.insert(2, 'RAJ2000', 'a_venir')
            informations_df.insert(3, 'DEJ2000', 'a_venir')
    else:
        # utiliser les données à partir des dict
        creer_df_info_obs_avec_dict()
    
    ### préparer structure répertoires et fichiers
    pr  = observations_df['paire'][0].replace('"', '')
    src = informations_df.loc[0, 'id_source']

    ### recherche id WDS de la source et inscrire id, ad et dec dans df
    result_rech_WDS = do.rech_wds(src, pr)
    raj2000 = result_rech_WDS[0]['RAJ2000'].item()
    dej2000 = result_rech_WDS[0]['DEJ2000'].item()


    #informations_df.loc[0, 'id_WDS'] = result_rech_WDS[0][0][0]
    informations_df.loc[0, 'id_WDS'] = result_rech_WDS[0]['WDS'].item()
    
    # selon WDS, l'AD et la DEC sont celles de la primaire de la paire pr
    informations_df.loc[0, 'RAJ2000'] = raj2000
    informations_df.loc[0, 'DEJ2000'] = dej2000
    
    ### imprimer résultat recherche complète WDS avec note pour aider la validation
    # avec '*' afin d'obtenir toutes les paires si elles existent
    print('\nInformations WDS :\n')
    do.info_src_wds(src, '*', True)
    
    str_rep_paire = pr
    if '*' in str_rep_paire:
        # PPL : Pas de Paire Listée
        str_rep_paire = 'PPL'
        
    prepare_structure_rep_et_fichiers(src, observations_df.loc[0, 'obs_prog'] + '\\' + str_rep_paire)
    #creer_df_data()
    
    # imprimer informations
    print('\n' + '*' * 15 + ' DataFrame information_df '+ '*' * 15 + ' :\n')
    print('-' * 80)
    print(informations_df)
    print('-' * 80)
    # imprimer observations
    print('\n' + '*' * 15 + " DataFrame observations_df " + '*' * 15 + ' :\n')
    print('-' * 80)
    print(observations_df)
    print('-' * 80)
    
    '''
    print('\nLe chemin complet est :')
    print(ch_rep_mesures)
    '''
    
    ### saisir intention enregistrement sur disque
    print('\nLes fichiers suivants seront enregistrés :')
    print(' ' + nom_complet_fichier_information_systeme)
    print(' ' + nom_complet_fichier_observations)
    #print(' ' + nom_complet_fichier_mesures_rho_modele)
    #print(' ' + nom_complet_fichier_mesures_theta_modele)
    
    rep = input("Enregister les données sur disque (o|n) ? ").upper()
    if 'O' in rep:
        enregistrer_fichiers()
    else:
        print("Pas d'enregistrement.")
    
    print('\n\nINSTRUCTIONS')
    print('Les dataFrames/listes suivants sont disponibles pour modifications :')
    print('  informations_df')
    print('  observations_df')
    print('\n Utilisez Variable Explorer pour modifier les df')
    print('\n Après modifications, exécutez :')
    print("\n informations_df.to_csv(nom_complet_fichier_information_systeme, index=False, encoding='utf-8')")
    print("\n observations_df.to_csv(nom_complet_fichier_observations, index=False, encoding='utf-8')")
    print('  pas enregistrer_fichiers()')
    
        

# -*- coding: utf-8 -*-
"""
Created on Wed Dec  8 21:48:45 2021

@author: dominique
"""
# %% imports
import pandas as pd
#import numpy as np
import sys
from os import path
import math
import re
import os
from tkinter import Tk
from tkinter.filedialog import askdirectory
from tkinter.filedialog import askopenfile
#import math
#import glob
from astropy.time import Time

# insérer le chemin suivant dans sys.path pour trouver le package astrodm
if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesOutils as do


# %% DÉFINITION DES CLASSES
#
# Classe abstraite Acquisition
#
class Acquisition:
    '''
    La classe Acquisition contient les données d'acquisition pour un bloc
    d'observation. Cette classe contient les données communes au trois types
    de mesures (typeMesure) 'pos' et 'sep' et 'ech' utilisées dans les deux types
    de réductions (typeObservation) 'ech' et 'complete'.
    '''
    def __init__(self):
        #
        # Les attributs suivants seront renseignés lors de la lecture des fichiers
        # log d'acquisition et d'environnement correspondants
        #

        # 'temp_to' température du to
        self.strTemp_to = ''

        # date UTC d'acquisition (en assumant que PC d'acquisition réglé sur UTC)
        self.date_utc_acq = ''

        # heure UTC d'acquisition
        self.heure_utc_acq = ''

        # nombre d'images acquises
        self.nbr_images_acq = ''

        # filtre
        self.strIdFiltre=''

        # note
        self.note=''

#
# Classe AcquisitionSeparation
#
class AcquisitionSeparation(Acquisition):
    ''' La classe AcquisitionSeparation étend la classe Acquisition avec ...'''
    def __init__(self):
        super().__init__()
        # type de mesure
        self.typeMesure = 'sep'

        # liste des index de calibration d'échelle
        self.lstIndexCalE = list()

        # nom complet du fichier log d'acquisition (sep)
        self.ncfla = ''
        
        # nom complet du fichier log environnement (sep)
        self.ncfle = ''


#
# Classe AcquisitionPosition
#
class AcquisitionPosition(Acquisition):
    ''' La classe AcquisitionPosition étend la classe Acquisition avec ...'''
    def __init__(self):
        super().__init__()
        # type de mesure
        self.typeMesure = 'pos'

        # nom complet du fichier log d'acquisition (pos)
        self.ncfla = ''
        
        # nom complet du fichier log environnement (pos)
        self.ncfle = ''

        # évaluation du quadrant par l'observateur dans le fichier log environement
        self.eval_Q = ''


#
# Classe AcquisitionEchelle
#
class AcquisitionEchelle(Acquisition):
    ''' La classe AcquisitionEchelle étend la classe Acquisition avec ...'''
    def __init__(self):
        super().__init__()
        # type de mesure
        self.typeMesure = 'ech'

        # nom complet du fichier log d'acquisition (pos)
        self.ncfla = ''
        
        # nom complet du fichier log environnement (pos)
        self.ncfle = ''

        # id du masque utilisé
        self.strIdMasque = ''

        # note
        self.note = ''

        # index de calibration E unique dans ce cas
        # sera déterminé par fonction de sélection interactive des fichiers
        self.indexCalE = ''


#
# classe abstraite Reduction
#
class Reduction:
    '''
    La classe Reduction contient les données de base d'une réduction.
    '''
    def __init__(self):
        # nom complet fichier log réduction (produit par Reduc)
        # sera déterminé par fonction de sélection interactive des fichiers
        self.ncflr = ''

        # mesures brutes dans Pandas dataframe éventuellement
        self.reduc_brute_df = ''

        # séparation moyenne en px
        self.sep_moy_px = ''
        self.sep_moy_px_sigma = ''


#
# classe ReductionEchelle
#
class ReductionEchelle(Reduction):
    '''
    La classe ReductionEchelle contient les données de base d'une réduction d'échelle.
    '''
    def __init__(self):
        super().__init__()

        # distance angulaire Z entre max n=0 et n=1 du patron d'interférence
        self.Z, self.Z_sigma = 0, 0

        # échelle de la caméra et sigma échelle
        self.E, self.E_sigma = 0, 0
            
    # méthode du calcul de Z
    def calcule_Z(self):
        print('Calcule de Z.\n')

    # méthode du calcul de E
    def calcule_E(self):
        print('Calcule de E = self.Z / self.sep_moy_px.\n')


#
# classe ReductionComplete
#
class ReductionComplete(Reduction):
    '''
    La classe ReductionComplete contient les données de base d'une réduction complète.
    '''
    def __init__(self):
        super().__init__()

        # theta lu du log Reduc de sep
        self.strTheta = ''
        self.strTheta_sigma = ''
        
        # theta et sigma theta
        self.theta, self.theta_sygma  = 0, 0

        # Delta Matrix sep et pos
        self.strDelta_matrix_pos = ''
        self.strDelta_matrix_sep = ''



#
# Classe Bloc
#
class Bloc:
    '''  La classe Bloc ...'''
    def __init__(self, noBloc, typeObservation):
        self.bloc = noBloc
        self.typeObservation = typeObservation

        if typeObservation == 'complete':
            self.acquisitionSep = AcquisitionSeparation()
            self.acquisitionPos = AcquisitionPosition()
            self.reduc = ReductionComplete()

        if typeObservation == 'ech':
            self.acquisitionEch = AcquisitionEchelle()
            self.reduc = ReductionEchelle()


#
# Classe Observation
#
class Observation:
    ''' La classe Observations ... 
    noObs :: no de l'observation (N dans les fichiers csv)
    nbrBlocs :: nombre de blocs d'observations
    typeObservation :: 'ech' Échelle, ou 'complete' Complète (typeMesure 'pos' ou séparation 'sep')
    '''

    def __init__(self, noObs, nbrBlocs, typeObservation='ech'):
        self.N = noObs
        self.typeObservation = typeObservation
        self.nbrBlocs = nbrBlocs

        self.lstBlocs = list()
        for b in range(nbrBlocs):
            self.lstBlocs.append(Bloc(b+1, typeObservation))


# %% FONCTIONS

def inits():
    ### pandas options d'affichage des tables
    pd.set_option('display.expand_frame_repr', True)
    pd.set_option('display.colheader_justify', 'right')
    pd.set_option('display.max_colwidth', 50)
    pd.set_option('display.max_column', 30)
    pd.set_option('display.width', 130)
    pd.set_option("precision", 4)
    
    # for tkinter
    global root
    root = Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()
    
    # pour général
    global ch_rep_exec, fich_mesures_brutes
    ch_rep_exec = os.getcwd()
    # fichier des mesures brutes écrit dans chaque dossier reduc
    fich_mesures_brutes = 'mesures_brutes.csv'
    
    # fichiers maîtres
    global nom_fich_m_cal, nom_fich_m_filtres, nom_fich_m_masques
    nom_fich_m_cal = 'master_calibrations_e.csv'
    nom_fich_m_filtres = 'master_filtres_cal.csv'
    nom_fich_m_masques = 'master_masques_cal.csv'

    # type de réduction échelle 'ech' ou séparation (rho) 'complete'
    global type_reduc, t_scale, t_format, NL
    type_reduc = ''
    
    # time scale and format for astropy Time objects
    t_scale = 'utc'
    t_format = 'isot'
    
    # new line
    NL = '\n'

# %% PRINCIPAL
if __name__ == "__main__":
    # on est en mode interactif
    bool_mode_interactif = True
    lst_observations = list()
    
    # simulation d'observation complète avec un dossier qui contient N1 et N2
    #lst_observations.append(Observation(1, 1, 'complete')) # N=1, 1 bloc
    #lst_observations.append(Observation(2, 2, 'complete')) # N=2, 2 blocs

    # simulation d'une observation d'échelle : aucune notion de N et toujours un seul bloc
    lst_observations.append(Observation(1, 1, 'ech')) # N=1, 2 blocs
    

    '''
    ###########################################################
    # ceci permet d'itérer à travers la liste des observations
    ###########################################################
    
    Il serait donc possible de traiter toutes les observations se trouvant dans
    D:/DOCUMENTS/Astronomie/dev/STTA254/P2021-023/AB/N1 et ../N2 en un lot!
    '''

    for obs in lst_observations:
        print('#'*35)
        print('Observation {0} de type «{1}»'.format(obs.N, obs.typeObservation) )
        print('#'*35)
        
        if obs.typeObservation == 'ech':
            for b in range(obs.nbrBlocs):
                print('    le bloc {0} comprend les objets suivants :'.format(obs.lstBlocs[b].bloc))
                for key in obs.lstBlocs[b].__dict__.keys():
                    print("        {0} = {1}".format(key, obs.lstBlocs[b].__dict__[key]))
                    if key == 'acquisitionEch':
                        for key2 in obs.lstBlocs[b].__dict__[key].__dict__.keys():
                            print("{0}{1} = {2}".format(' '*12, key2, obs.lstBlocs[b].__dict__[key].__dict__[key2]))
                    if key == 'reduc':
                        for key2 in obs.lstBlocs[b].__dict__[key].__dict__.keys():
                            print("{0}{1} = {2}".format(' '*12, key2, obs.lstBlocs[b].__dict__[key].__dict__[key2]))
    
            print('\n')
        
        if obs.typeObservation == 'complete':
            for b in range(obs.nbrBlocs):
                print('    le bloc {0} comprend les objets suivants :'.format(obs.lstBlocs[b].bloc))
                for key in obs.lstBlocs[b].__dict__.keys():
                    print("        {0} = {1}".format(key, obs.lstBlocs[b].__dict__[key]))
                    if key == 'acquisitionSep':
                        for key2 in obs.lstBlocs[b].__dict__[key].__dict__.keys():
                            print("{0}{1} = {2}".format(' '*12, key2, obs.lstBlocs[b].__dict__[key].__dict__[key2]))
                    if key == 'acquisitionPos':
                        for key2 in obs.lstBlocs[b].__dict__[key].__dict__.keys():
                            print("{0}{1} = {2}".format(' '*12, key2, obs.lstBlocs[b].__dict__[key].__dict__[key2]))
                    if key == 'reduc':
                        for key2 in obs.lstBlocs[b].__dict__[key].__dict__.keys():
                            print("{0}{1} = {2}".format(' '*12, key2, obs.lstBlocs[b].__dict__[key].__dict__[key2]))
    
            print('\n')
        
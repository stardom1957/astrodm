# -*- coding: utf-8 -*-
"""
Created on Thu Dec 23 23:35:45 2021

Définition des classes de astrodm

version 1

@author: dominique
"""

# %% imports
import pandas as pd
import sys

# %% imports et définition des constantes
#import glob
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
import re
from os import path


# %% DÉFINITIONS
'''
Crée un dictionnaire des codes de notes pour les
observations d'étoiles doubles

Format sur 3 caractères, par ex. 'C L'
Position 1 : code de suivi {X, E, C, P ou T}
Position 2 : libre pour développement futur
Position 3 : code de méthode de mesure {M, L ou A}
'''
notes_obs_dict = {
    'X..': ['Délais dépassé, à reprendre.'],
    'E..': ['Erreur irrécupérable ou résultats incorrects. P. e. mauvaise paire mesurée.'],
    'C..': ["en cours d'observation."],
    'P..': ['en cours de PLANIFICATION.'],
    'T..': ['Terminé. Réduction complète, avec N=2 recommandé. Observations complétées.'],
    '..M': ['mesure par Microguide.'],
    '..L': ['mesure par Lucky Imaging.'],
    '..A': ['mesure par autre méthode, voir fichier _observations.csv.'],
    '...': ['réservé futur développement.']
}

# pour rech WDS (source seulement) formater src avec un espace entre découvreur et no
# alors len(src) = max 7
WDS_SRC_ESPACE_LEN = 1

# longueur fixe du nom de la source pour recherche dans WDS Notes
# c.-à-d. len(découvreur + espaces + no )
WDS_SRC_LEN_NOTES = 7

# fichiers maîtres
#debug global nom_fich_m_cal, nom_fich_m_filtres, nom_fich_m_masques
ch_rep_cal = 'D:/DOCUMENTS/Astronomie/dev/cal_e/'
nom_fich_m_cal = 'master_calibrations_e.csv'
nom_fich_m_filtres = 'master_filtres_cal.csv'
nom_fich_m_masques = 'master_masques_cal.csv'


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
        self.strIdFiltre = ''

        # note
        self.note = ''

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

        # nom complet du fichier log d'acquisition
        self.ncfla = ''
        
        # nom complet du fichier log environnement
        self.ncfle = ''

        # id du masque utilisé
        self.strIdMasque = ''

        # note
        self.note = ''

        # index de calibration E unique dans ce cas, mais sera quand même
        # placé dans un set au momemt de renseigner cet attribut
        # par la fonction de sélection interactive des fichiers
        self.indexCalE = list()


#
# classe abstraite Reduction
#
class Reduction:
    '''
    La classe Reduction contient les données de base d'une réduction.
    '''
    def __init__(self):
        # nom complet fichier log réduction (produit par Reduc)
        # un pour pos et un pour sep
        # sera déterminé par fonction de sélection interactive des fichiers
        self.ncflr_sep = ''
        self.ncflr_pos = ''

        # mesures brutes dans Pandas dataframe éventuellement
        self.reduc_brute_df = ''

        # séparation moyenne en px
        self.sep_moy_px = ''
        self.sep_moy_px_sigma = ''

    def relecture_mes_brutes(self, ncfmb):
        '''
        Lecture des mesures brutes à partir de fich_mesures_brutes dans un df.
    
        Parameters
        ----------
         chemin String ncfmb nom complet fichier mesures brutes
    
        Returns
        -------
         Un Pandas df des mesures brutes
        '''
    
        #debug global reduc_brute_df
        
        # création d'un df à partir du fichier reduc_brute.csv
        try:
            self.reduc_brute_df = pd.read_csv(ncfmb)
        except FileNotFoundError:
            print('\nFichier {0} NON trouvé. Sortie du programme.'.format(ncfmb))
            sys.exit()


#
# classe ReductionEchelle
#
class ReductionEchelle(Reduction):
    '''
    La classe ReductionEchelle contient les données de base d'une réduction d'échelle.
    '''
    def __init__(self):
        super().__init__()
        
        # statistiques descriptives des distances en px

        self.dist_min = 0
        self.dist_max = 0
        self.dist_moy = 0
        self.dist_sigma = 0
        self.n_data = 0

        # LfplusDf, LfplusDf_sigma, Lo et Lo_sigma nécessaires au calcul de Z
        self.LfplusDf, self.LfplusDf_sigma, self.Lo, self.Lo_sigma = 0, 0, 0, 0

        # distance angulaire Z entre max n=0 et n=1 du patron d'interférence
        self.Z, self.Z_sigma = 0, 0

        # échelle de la caméra et sigma échelle
        self.E, self.E_sigma = 0, 0
            
    # méthode du calcul de Z
    def calcule_Z(self, a, b, c, d):
        '''
        À partir des caractéristiques du masque et du filtres qui se trouvent dans les
        info_masque_df et info_filtre_df, calcule Z et Z_sigma.
    
        Parameters
        ----------
         a = LfplusDf
         b = LfplusDf_sigma
         c = Lo
         d = Lo_sigma
    
        Returns
        -------
         rien
        '''
        #debug global LfplusDf, LfplusDf_sigma, Lo, Lo_sigma, Z, Z_sigma

        #debug global info_filtre_df, info_masque_df
    
        # Z = dist ang premier max de l'exp de Young
        print('Calcule de Z.')
        # caractéristiques du masque et du filtre
        LfplusDf = a
        LfplusDf_sigma = b
        Lo = c
        Lo_sigma = d
    
        # distance angulaire Z entre max n=0 et n=1 du patron d'interférence
        self.Z = (Lo / LfplusDf)  * 206264.806  # 206265 env. arcsec par radian
    
        # Propagation des incertitudes
        self.Z_sigma = abs(self.Z) * math.sqrt(math.pow((Lo_sigma/Lo), 2) + math.pow((LfplusDf_sigma/LfplusDf), 2)) 
        print('Z = {0:>4.4f} arcsec ±{1:>4.4f} arcsec\n'.format(self.Z, self.Z_sigma))

    # méthode du calcul de E


    def calcule_E(self):
        '''
        À partir de reduc_brute_df calcule la distance entre chaque point et
        produit les statistiques descriptives des données.
    
        Parameters
        ----------
         aucun
    
        Returns
        -------
        rien
        '''
    
        #debug global dist_min, dist_max, dist_moy, dist_sigma, n_data, E, E_sigma
    
        # ajout distance entre chaque point dans la colonne 'dist'
        self.reduc_brute_df['dist'] = ((self.reduc_brute_df['xB'] - self.reduc_brute_df['xA'])**2 +\
                                       (self.reduc_brute_df['yB'] - self.reduc_brute_df['yA'])**2)**0.5
    
        ### calcul statistiques descriptives des distances
        self.dist_min = self.reduc_brute_df['dist'].min()
        self.dist_max = self.reduc_brute_df['dist'].max()
        self.dist_moy = self.reduc_brute_df['dist'].mean()
        self.dist_sigma = self.reduc_brute_df['dist'].std()
        self.n_data = len(self.reduc_brute_df['dist'].index)
    
        # calcul de l'échelle de la caméra
        self.E = self.Z / self.dist_moy
        
        # propagation des incertitudes de E
        self.E_sigma = abs(self.E) * math.sqrt(math.pow((self.Z_sigma/self.Z), 2) +\
                                               math.pow((self.dist_sigma/self.dist_moy), 2)) 

  

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
        self.strDelta_matrix_sep = ''
        self.strDelta_matrix_pos = ''



#
# Classe Bloc
#
class Bloc:
    '''  La classe Bloc ...'''
    def __init__(self, noBloc, typeObservation):
        self.indexBloc = noBloc
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

    def __init__(self, noObs, typeObservation='ech'):
        self.N = noObs + 1
        self.typeObservation = typeObservation
        self.nbrBlocs = 0

        # ces attributs seulements pour observation 'complete',
        self.nomPaire = ''
        self.programmeObs = ''

        # liste des objets Blocs
        self.lstBlocs = list()
        
    def ajouteBloc(self, nb, to):
        self.lstBlocs.append(Bloc(nb, to))
        self.nbrBlocs += 1
   

#
# Classe Systeme
#
class Systeme:
    '''
    '''
    
    def __init__(self, cheminSysteme):
        # chemin du système
        self.cheminSysteme = cheminSysteme
        
        # nom du système
        self.nomSysteme = path.basename(cheminSysteme)

        # nom complet du fichier info système
        self.ncfinfo_systeme =  cheminSysteme + '/' + self.nomSysteme + '_info_système.csv'
        assert path.exists(self.ncfinfo_systeme), self.ncfinfo_systeme + ' non trouvé.'

        # Pandas df du système
        self.informations_df = pd.read_csv(self.ncfinfo_systeme)

#
# Classe DoubleSessions
#
class DoubleSessions:
    '''
    La classe DoubleSession contient la structure de données entière des
    session d'observations (N=1, 2 ...) et de leurs blocs pour le système
    concerné.
    '''
    def __init__(self):
        pass
    
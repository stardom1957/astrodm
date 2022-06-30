# -*- coding: utf-8 -*-
"""
@author: Dominique Martel

Comprend diverses fonctionnalités pour planifier, réduire les observations
à partir des données d'acquisition d'étoiles doubles et de pré-réduction
produites par le logiciel REDUC (de Florent Losse) et produit également
diverses listes. 
"""

# %% imports
#import glob
import pandas as pd
import math
import sys
#import numpy as np
from astropy import units as u
#from astropy.coordinates import SkyCoord
#from astropy.time import Time, TimezoneInfo, TimeEpochDate, TimeBesselianEpoch
from astropy.time import Time, TimezoneInfo
from datetime import datetime
from astroquery.vizier import Vizier as viz
import re
from os import path
from tkinter import Tk
import os
import glob
import pickle
from astropy.coordinates import SkyCoord

# %% DÉFINITION DES CLASSES
#
# Classe abstraite Acquisition
#
class Acquisition:
    '''
    Contient les données d'acquisition pour un bloc d'observation. Cette classe
    abstraite contient les données communes au trois d'acquisitions :
      (angle de) position 'pos', séparation 'sep' et échelle 'ech' utilisées
    dans les deux types de réductions 'ech' et 'complete'.
    '''
    def __init__(self):
        #
        # Les attributs suivants seront renseignés lors de la lecture des fichiers
        # log d'acquisition et d'environnement correspondants
        #

        # type de msure
        self.typeMesure = ''

        # 'transp' tranparence
        self.transp = ''

        # 'seeing'
        self.seeing = ''

        # 'humid' humidité en %
        self.humid = 0

        # 'press_bar' pression barométrique
        self.press_bar = 0
        
        # 'remarques'
        self.remarques = ''

        # 'temp_to' température du to
        self.temp_to = None

        # date UTC d'acquisition (en assumant que PC d'acquisition réglé sur UTC)
        self.date_utc_acq = ''

        # heure UTC d'acquisition
        self.heure_utc_acq = ''
        
        # objet astropy.time.core.Time
        self.dtime_utc_acq = None

        # nombre d'images acquises
        self.nbr_images_acq = 0

        # filtre
        self.strIdFiltre = ''

        # note
        self.note = ''
        
        # mise au point map
        self.map = 0
        

#
# Classe AcquisitionSeparation
#
class AcquisitionSeparation(Acquisition):
    '''Étend la classe Acquisition pour une acquisition de type 'sep' séparation.'''
    
    def __init__(self, typeMesure):
        """Paramètre positionnel :
            
            typeMesure -- String
        """
        super().__init__()
        # type de mesure
        self.typeMesure = typeMesure

        # nom complet du fichier log d'acquisition (sep)
        self.ncfla = ''
        
        # nom complet du fichier log environnement (sep)
        self.ncfle = ''


#
# Classe AcquisitionPosition
#
class AcquisitionPosition(Acquisition):
    '''Étend la classe Acquisition pour une acquisition de type 'pos' position'''

    def __init__(self, typeMesure):
        """Paramètre positionnel :
            
            typeMesure -- String
        """

        super().__init__()
        # type de mesure
        self.typeMesure = typeMesure

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
    '''Étend la classe Acquisition pour une acquisition de type 'ech' echelle'''

    def __init__(self, typeMesure):
        """
        Paramètre positionnel :
            
            typeMesure -- String
        """

        super().__init__()
        # type de mesure
        self.typeMesure = typeMesure

        # nom complet du fichier log d'acquisition
        self.ncfla = ''
        
        # nom complet du fichier log environnement
        self.ncfle = ''

        # id du masque utilisé
        self.strIdMasque = ''

        # note
        self.note = ''



#
# classe abstraite Reduction
#
class Reduction:
    '''
    La classe (abstraite) Reduction contient les données de base d'une réduction.
    '''
    def __init__(self):
        # nom complet fichier log réduction sep (produit par Reduc) (ncflr_sep)
        # nom complet fichier log réduction pos (produit par Reduc) (ncflr_pos)

        self.ncflr_sep = ''
        self.ncflr_pos = ''
        
        # bool indicateur delta matrix sep et pos valides
        self.deltaMatrixReducValide = False
        
        # validité de l'intervalle de temps entre toutes les mesures d'échelles
        # qui servent pour la même réduction
        #
        self.delaiDepuisAcqEchValide = True

        # validité de l'intervalle de température entre toutes les mesures
        # qui servent pour la même réduction
        #
        self.deltaTemperatureValide = True
        
        # valeur de la map de l'échelle utilisée dans la méthode calcule_rho
        # la valeur indiquée est toujours valide
        self.mapEchelle = 0

        # liste des index de calibration d'échelle
        self.lstIndexCalE = list()

        # Pandas dataframe de mesures brutes
        self.reduc_brute_df = ''

    def relecture_mes_brutes(self, ncfmb):
        '''
        Lecture des mesures brutes à partir de fich_mesures_brutes dans un df.
    
        Paramètre positionnel :
         ncfmb -- String nom complet du fichier des mesures brutes
    
        Retourne
         Un Pandas df des mesures brutes.
        '''
    
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
    """Contient les données de base d'une réduction de type ech échelle."""
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
    def calcule_Z(self, LfplusDf, LfplusDf_sigma, Lo, Lo_sigma):
        '''
        Calcule Z (angle de séparation) en " du maxima de premier ordre du patron
        d'interférence produit par un masque à fentes et un filtre dont les
        caractéristiques se trouvent dans les Pandas dataframes info_masque_df
        et info_filtre_df.
    
        Paramètres positionnels :
        LfplusDf       -- somme largeurs des fentes et distance entre les fentes
        LfplusDf_sigma -- incertitude de LfplusDf
        Lo             -- Longueur d'onde du filtre en m
        Lo_sigma       -- incertitude de Lo
        '''
    
        # Z = dist ang premier max de l'exp de Young
        print('Calcule de Z.')
    
        # distance angulaire Z entre max n=0 et n=1 du patron d'interférence
        self.Z = (Lo / LfplusDf)  * 206264.806  # 206265 arcsec par radian
    
        # Propagation des incertitudes
        self.Z_sigma = abs(self.Z) * math.sqrt(math.pow((Lo_sigma/Lo), 2) + math.pow((LfplusDf_sigma/LfplusDf), 2)) 
        print('Z = {0:>4.4f} arcsec ± {1:>4.4f} arcsec\n'.format(self.Z, self.Z_sigma))


    def calcule_E(self):
        '''
        Calcule l'échelle E de la caméra (arcsec/pixel) en multipliant la
        distance moyenne entre les centroïdes des maxima de premier ordre
        par la valeur de Z (l'angle de séparation) calculée.
                            
        Produit les statistiques descriptives des données qui se trouvent dans
        reduc_brute_df (tableau des distances mesurées).
    
        Parameters
        ----------
         aucun
    
        Returns
        -------
        rien
        '''
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
    '''Contient les données de base d'une réduction complète.'''
    def __init__(self):
        super().__init__()

        # échelle moyenne et incertitude
        self.E_moy, self.E_moy_sigma = 0, 0
        
        # rho et rho_sigma
        self.rho, self.rho_sigma = 0, 0

        # theta et theta_sigma lus du log Reduc de sep
        self.theta,  self.theta_sigma = 0, 0

        # Delta Matrix sep et pos
        self.delta_matrix_sep, self.delta_matrix_pos = 0, 0


    def calcule_rho(self, noN, noB):
        '''
        À partir de reduc_brute_df calcule la distance entre chaque point et
        produit les statistiques descriptives des données.
    
        Paramètres positionnels :
        noN -- int numéro de la session d'observation
        noB -- int numéro du bloc d'observation
        '''
    
        # ajout distance entre chaque point dans la colonne 'dist'
        self.reduc_brute_df['dist'] = ((self.reduc_brute_df['xB'] - self.reduc_brute_df['xA'])**2 +\
                                       (self.reduc_brute_df['yB'] - self.reduc_brute_df['yA'])**2)**0.5
    
        ### calcul statistiques descriptives des distances en pixels
        self.dist_min = self.reduc_brute_df['dist'].min()
        self.dist_max = self.reduc_brute_df['dist'].max()
        self.dist_moy = self.reduc_brute_df['dist'].mean()
        self.n_data = len(self.reduc_brute_df['dist'].index)
        self.dist_sigma = self.reduc_brute_df['dist'].std()
    
        # à partir de self.lstIndexCalE, récupération des échelles et sigma
        E_moy, E_m_sigma_sqr = 0, 0

        # créer un df vide avec même structure que master_calibrations_e_df
        df = pd.DataFrame(data=None, index=None, columns=list(master_calibrations_e_df.keys()))
        # puis récupérer le/les index de calibration dans df
        for idx_cal_e in self.lstIndexCalE:
            df = df.append(master_calibrations_e_df.\
                loc[master_calibrations_e_df.index_cal_e==idx_cal_e])

        
        #######################################
        # Traitement index de calibrations
        #######################################

        # VALIDATIONS OK, on procède
        
        # parcourir df
        # et calculer la moyenne de E et l'incertitude de la moyenne de E
        for idx in df.index:
            E_moy += df.loc[idx, 'E']
            E_m_sigma_sqr += math.pow(df.loc[idx, 'E_sigma'], 2)
        self.E_moy = E_moy / len(df)
        self.E_moy_sigma = math.sqrt(E_m_sigma_sqr)/len(df)
        
        # calcul rho et rho_sigma
        self.rho = self.E_moy * self.dist_moy
        
        # Propagation des incertitudes dans rho_sigma
        self.rho_sigma = abs(self.E_moy * self.dist_moy) *\
            math.sqrt(math.pow((self.E_moy_sigma/self.E_moy), 2) +\
                 math.pow((self.dist_sigma/self.dist_moy), 2)) 


#
# Classe Bloc
#
class Bloc:
    '''
    Un bloc d'observation est un constituant d'un objet Observation.
    
    Si le type d'observation est 'complete', un bloc comprend un objet
    AcquisitionSeparation, un objet AcquisitionPosition et un objet
    ReductionComplete.
    
    Si le type d'observation est 'ech', un bloc comprend un objet
    AcquisitionEchelle et un objet ReductionEchelle.
    '''
    
    def __init__(self, noBloc, typeObservation):
        self.indexBloc = noBloc
        self.tobs = typeObservation

        if typeObservation == 'complete':
            self.sep = AcquisitionSeparation('sep')
            self.pos = AcquisitionPosition('pos')
            self.reduc = ReductionComplete()

        if typeObservation == 'ech':
            self.ech = AcquisitionEchelle('sep')
            self.reduc = ReductionEchelle()

    def validations(self, nsession):
        '''Donne des indications sur la validité du bloc d'observation.
        
        Cette fonction renseigne les attributs suivants :
            reduc.deltaMatrixReducValide :: la valeur de delta_matrix de REDUC
             de pos est la même que celle de sep.
             
            self.reduc.delaiDepuisAcqEchValide :: l'intervalle de temps
             entre les acquisitions d'échelle
             et de sep <= MAX_DELAI_DEPUIS_ACQUISITIONS_ECHELLE.
             
            self.reduc.deltaTemperatureValide :: différence de température
             entre les acquisitions <= MAX_DELTA_TEMPERATURE
        
        Paramètre positionnel :
        nsession -- int numéro de la session
        '''
        resultatOK = True # devient False si erreur fatale
        #######################################################################
        # Validation 1 - existence de l'index de calibration
        # Récupérer les données de tous les index de calibration indiqués
        # dans le bloc d'observation
        #

        # créer un df vide avec même structure que master_calibrations_e_df
        df = pd.DataFrame(data=None, index=None,\
                          columns=list(master_calibrations_e_df.keys()))

        # puis récupérer les informations de chaque index de calibration
        # présent dans self.reduc.lstIndexCalE dans un Pandas df
        for idx_cal_e in self.reduc.lstIndexCalE:
            df = df.append(master_calibrations_e_df.\
                loc[master_calibrations_e_df.index_cal_e==idx_cal_e])
                
        # si df est vide, alors c'est probablement parce que la valeur de
        # l'index ne se situe pas dans master_calibrations_e_df
        
        # fatal si index n'existe pas
        if len(df) == 0:
            inscrire_dans_log("N{0} b{1} : index de calibration non trouvé(s) dans master_calibrations_e_df!".\
                  format(nsession, self.indexBloc))
            inscrire_dans_log("self.reduc.lstIndexCalE=",self.reduc.lstIndexCalE)
            # doit s'arrêter car il est impossible de calibrer l'observation
            resultatOK = False
            return resultatOK

        #######################################################################
        # Validation 2 : map unique pour acquisitions échelle et sep
        #  valider si la/les** acquisition d'échelle dans df ont la même
        #  map que celle de sep du bloc courant
        #  ** S'il y a plus d'un index de calibration dans lstIndexCalE,
        # d'abord bâtir un set avec les valeurs et ajouter celle de sep
        # alors si len du set == 1, map est unique
        
        tempo = set()
        # trouver les map de calibration
        for idx in df.index:
            tempo.add(df.loc[idx, 'map'])
        # ajouter la map de sep
        tempo.add(self.sep.map)
        
        # fatal si non respecté
        # valide ssi un seul élément
        if len(tempo) == 1:
            self.reduc.mapEchelle = tempo.pop()
            del tempo
            # la map est la même partout : indiquer dans le drapeau
        else:
            inscrire_dans_log("N{0} b{1}, cal_E : map non égales!".format(nsession, self.indexBloc),\
                  self.reduc.lstIndexCalE)
            # la map n'est pas la même : on quitte
            resultatOK = False
            return resultatOK

        #######################################
        # Validation 3 : intervalle de temps entre
        # la/les calibration d'échelle et de l'observation en cours.
        # Trouver tous les dt_obs_utc des échelles et celle de sep
        # valider si l'intervalle d'acquisition <= MAX_DELAI_DEPUIS_ACQUISITIONS_ECHELLE
        # utiliser le «truc» des jours Juliens pour chaque date, trier la liste
        # et trouver intervalle entre première et dernière date
        #
        # résultat dans self.reduc.delaiDepuisAcqEchValide
        
        listeDates = list()
        #for i in range(0, df.index.size):
        for idx in df.index:
            dth = str_dt_isot_a_TimeIsot(dt=df.loc[idx,'dt_obs_utc'])
            # ajouter jour julien
            listeDates.append(dth.jd)
            
        # ajouter jd de dtime_utc_acq de sep
        listeDates.append(self.sep.dtime_utc_acq.jd)
        listeDates.sort()
        
        # calculer intervalle entre première et dernière date en min
        # jd * 1440 min/jour
        intervalle = abs(listeDates[0] - listeDates[len(listeDates)-1]) * 1440
        if intervalle > MAX_DELAI_DEPUIS_ACQUISITIONS_ECHELLE:
            inscrire_dans_log('*'*50)
            inscrire_dans_log("AVERTISSEMENT!")
            inscrire_dans_log("N{0} b{1}, cal_E et sep : délai depuis dern. acq échelle > {2} m!".\
                  format(nsession, self.indexBloc, MAX_DELAI_DEPUIS_ACQUISITIONS_ECHELLE))
            inscrire_dans_log("Pour plus de détails, exécutez res.hier()")
            inscrire_dans_log('*'*50)
            self.reduc.delaiDepuisAcqEchValide = False

        ##############################################
        # Validation 4 : intervalle de températures entre toutes les 
        # acquisitions d'un même bloc incluant acquisition d'échelle.
        # Valide si intervalle des temp_to <= MAX_DELTA_TEMPERATURE
        # sinon imprimer une alerte et continuer

        listeTemp = list()
        for idx in df.index:
            listeTemp.append(df.loc[idx,'temp_to'])
        listeTemp.append(self.sep.temp_to)
        listeTemp.sort()
        intervalle = abs(listeTemp[0] - listeTemp[len(listeTemp)-1])

        if intervalle > MAX_DELTA_TEMPERATURE:
            self.reduc.deltaTemperatureValide = False
            inscrire_dans_log('*'*50)
            inscrire_dans_log("AVERTISSEMENT!")
            inscrire_dans_log("  N{0} b{1}, : intervalle de température entre calibration et sep > {2}°!".\
                  format(nsession, self.indexBloc, MAX_DELTA_TEMPERATURE))
            inscrire_dans_log("Pour plus de détails, exécutez res.hier()")
            inscrire_dans_log('*'*50)

        #################################################
        # Validation 5 : delta matrix
        # La valeur de theta est lue dans le log reduc de sep.
        # Dans Reduc de sep, cette valeur est calculée à partir de delta_matrice_sep
        # qui DOIT être copiée par l'usager à partir du Reduc de pos correspondant.
        # Afin de vérifier si cette étape a été faite correctement, on 
        # vérifie si delta_matrice_sep == delta_matrice_pos.
         
        if self.reduc.delta_matrix_sep == self.reduc.delta_matrix_pos:
            self.reduc.deltaMatrixReducValide = True
        else:
            inscrire_dans_log('Observation no. {0}, bloc {1} :'.\
                  format(nsession, self.indexBloc))
            inscrire_dans_log("   Le delta matrix de sep est différent de delta matrix de pos")
            inscrire_dans_log("     delta matrix de sep {0}, delta matrix de pos {1}\n".\
                  format(self.reduc.delta_matrix_sep, self.reduc.delta_matrix_pos))
            inscrire_dans_log("   Ceci peut vouloir dire que la valeur de delta matrix n'a")
            inscrire_dans_log("   pas été transférée de la pré-réduction (REDUC) de pos à")
            inscrire_dans_log("   celle de sep. La réduction va se poursuivre, mais il est")
            inscrire_dans_log("   fort probable que la valeur de theta sera incorrecte!")

        return resultatOK
        

#
# Classe Observation
#
class Observation:
    """Contient la liste des blocs (lstBlocs) d'observation d'une session
    d'observation.
    """

    def __init__(self, noObs, typeObservation):
        """
        Paramètres positionnels :
        noObs           -- no de l'observation (N dans les rapports et structures)
        typeObservation -- 'ech' Échelle, ou 'complete' Complète
        """

        self.N = noObs
        self.tobs = typeObservation
        self.nb = 0

        # ces attributs seulements pour observation 'complete',
        self.cheminN = ''

        # liste des objets Blocs
        self.lstBlocs = list()
        
    def ajouteBloc(self, no_bloc, type_obs):
        self.lstBlocs.append(Bloc(no_bloc, type_obs))
        self.nb += 1
   

#
# Classe Systeme
#
class Systeme:
    """ Structure des informations d'un système d'étoiles doubles ou multiples.
    
        Contient les informations de base d'un système.
    """
    def normalise_attributs_chaines(self):
            # s'assurer  que certains attributs texte soient entourés de "
            tempo = self.informations_df.loc[0,'id_system_alt1']
            if r'"' not in tempo:
                self.informations_df.loc[0,'id_system_alt1'] = r'"' + tempo + r'"'
        
            tempo = self.informations_df.loc[0,'id_system_alt2']
            if r'"' not in tempo:
                self.informations_df.loc[0,'id_system_alt2'] = r'"' + tempo + r'"'
        
            tempo = self.informations_df.loc[0,'remarques']
            if r'"' not in tempo:
                self.informations_df.loc[0,'remarques'] = r'"' + tempo + r'"'

    
    def __init__(self,\
                 chemin_systeme='',
                 nom_systeme_WDS='',
                 id_sys_alt1='',
                 id_sys_alt2='',
                 remarques=''
                 ):
        
        """
        Peut prendre en paramètres soit le chemin d'un dossier contenant un
        fichier csv qui contient les informations du système, soit le nom du
        système avec la série des attributs requis pour le système. Dans tous
        cas, certains attributs sont renseignés par une recherche astroquery
        dans le catalogue WDS et par diverses méthodes des packages
        astropy et astroplan.
        
        Paramètres Keyword :
         (Tous '' par défaut)
         chemin_systeme    -- String nom complet du fichier info_système
         nom_systeme_WDS   -- String id WDS du système (non normalisé) :
           par ex. stfa254 ou stf60
         Dict dict_systeme -- Dict des attributs du système :
           id_src_alt1 -- String nom alternatif 1
           id_src_alt2 -- String nom alternatif 2
         remarques   -- String remarques, notes
        """
        
        if chemin_systeme != '' and nom_systeme_WDS == '' and\
                 id_sys_alt1 == '' and id_sys_alt2 == '' and\
                 remarques == '':

            #
            # création par lecture d'un fichier csv
            #
            
            # nom du système
            self.nom = path.basename(chemin_systeme)

            # nom complet du fichier info système
            self.ncfinfo_systeme = chemin_systeme + '/' + self.nom + '_info_système.csv'
            assert path.exists(self.ncfinfo_systeme),\
                'doublesOutils.Systeme.__init__ :: ' +\
                    self.ncfinfo_systeme + ' non trouvé.'
            
            # chemin du système
            self.rep = chemin_systeme
            
            # lire le fichier _info_système qui contient tous les autres 
            # attributs
            try:
                # Pandas df du système
                self.informations_df = pd.read_csv(self.ncfinfo_systeme)
            except FileNotFoundError:
                print('doubleOutils.Systeme.__init__ :: fichier _info_système non lisible.')
                sys.exit()
            
            return
        
        if chemin_systeme != '' and nom_systeme_WDS != '':
            # création à l'aide des autres paramètres complétée par une 
            # recherche astroquery dans le WDS et par diverses méthodes des
            # packages astropy et astroplan
            #
            # id_sys_alt1, id_sys_alt2 et remarques sont facultatifs
            
            # s'assurer que nom du système est en majuscules
            self.nom = nom_systeme_WDS.replace(' ', '').upper()
            informations_dict = {
              'id_system': self.nom,
              'id_WDS': ['à venir'],
              'RAJ2000': ['à venir'],
              'DEJ2000': ['à venir'],
              'id_system_alt1': ['"' + id_sys_alt1 + '"'],
              'id_system_alt2': ['"' + id_sys_alt2 + '"'],
              'const': ['à venir'],
              # ATTENTION GARGER " SI NÉCESSAIRE P. E. pour une ','
              'remarques': ['"' + remarques + '"']
            }
            self.informations_df = pd.DataFrame(informations_dict)

            # s'assurer  que certains attributs texte soient entourés de "
            self.normalise_attributs_chaines()
            
            # nom complet du (futur) fichier _info_systeme.csv
            self.ncfinfo_systeme = chemin_systeme +\
                '/' + self.nom + '/' + self.nom + '_info_système.csv'

            
            #
            # compléter les attributs du système
            #
            
            # recherche de l'enregistrement de self.nom (nom de découvreur)
            # dans catalog='B/wds/wds' et inscrire id, ra et dec dans df
            result_rech_WDS = rech_wds(self.nom, '*')
            self.informations_df.loc[0, 'id_WDS'] = result_rech_WDS[0]['WDS'].item(0)
            
            # selon WDS, l'AD et la DEC sont celles de la primaire de la paire
            raj2000 = result_rech_WDS[0]['RAJ2000'].item(0)
            dej2000 = result_rech_WDS[0]['DEJ2000'].item(0)
            self.informations_df.loc[0, 'RAJ2000'] = raj2000
            self.informations_df.loc[0, 'DEJ2000'] = dej2000
            
            # trouver la constellation d'après les coordonnées et incrire dans
            # le df
            coordonnees = SkyCoord(ra=raj2000, dec=dej2000, frame='fk5', unit=(u.hourangle, u.deg))
            self.informations_df.loc[0, 'const'] = coordonnees.get_constellation(short_name=True)


#
# Classe DoubleSessions
#
class DoubleSessions:
    """
    Contient toutes les données des session d'observations (N=1, 2, ...), la
    liste des blocs (b=1, 2, ...), pour le système et la paire concernés.
    """
    def __init__(self, typeObs='complete', chProg=''):
        """
        Paramètres Keyword :
         typeObs -- String type d'observation :
           'complete' -- observation complète avec pos et sep
         chProg -- String chemin du dossier du programme d'observation
          (par défault '')
        """
        # nombre de sessions d'observation (N)
        self.nbrN = 0
        
        # N contiendra la liste des objets Observations
        self.N = list()

        if typeObs == 'complete':
            self.tobs = typeObs
            # créer objet Systeme avec fichier _info_système.csv qui se trouve
            # dans le chemin chProg
            self.systeme = Systeme(chemin_systeme=path.dirname(path.dirname(chProg)))

            # nom de la paire
            self.paire = ''
            
            # programme d'observation
            self.prog = path.basename(chProg)
            
            # reductions_des_observations_df contient la liste de tous les blocs
            # d'observations
            # définition des colonnes de observations_df
            
            lstCol = ['obs_prog', 'id_system', 'id_WDS', 'paire',\
             'const', 'N', 'bloc', 'Date_UTC',\
             'obs_epoque_B', 'rho', 'rho_sigma', 'theta',\
             'theta_sigma', 'observatoire', 'observateur',\
             'transp', 'seeing', 'temp_to', 'humid',\
             'press_bar', 'map', 'deltaMatrixReducValide',\
             'delaiDepuisAcqEchValide',\
             'deltaTemperatureValide', 'eval_Q', 'lstIndexCalE',\
             'E_moy', 'filtre'
            ]
            
            # le dataframe reductions_des_observations_df contiendra les observations réduites
            # créer le df vide avec seulement les noms des colonnes définies
            # plus haut
            #
            self.reductions_des_observations_df = pd.DataFrame(list(), columns=lstCol)
            
            # dataframe qui contient les moyennes par sessions (des blocs)
            self.moyennes_par_session_df = None
            
            # groupes_de_sessions_df contient les groupes de sessions qui
            # peuvent être utilisées pour publications et sert à produire
            # resultats_pour_publication_df
            
            # liste des tuples des no de session (N) et Date_UTC
            # et df des groupes de sessions

            self.lst_tup_dates = list()
            lstCol = ['Groupe', 'Dates_UTC', 'delai_entre_N (j)', 'Liste sessions (N)']
            self.groupes_de_sessions_df = pd.DataFrame(list(), columns=lstCol)

            # resultats_pour_publication_df contient une ligne pour chaque
            # groupe de session espacée de moins de MAX_DELAI_ENTRE_OBSERVATIONS.
            # Les valeurs moyennes et autres renseignements pour le rapport
            # des sessions seront renseignés dans self.calculer_pour_publication
            self.resultats_pour_publication_df = None
            
            #
            # moyennes des valeurs pour publication
            #
            #debug self.rho_moy, self.theta_moy, self.epoque_moy = 0, 0, 0
            # debug self.theta_sigma_moy, self.rho_sigma_moy = 0, 0
            
            # date de la dernière observation pour rapport des moyennes
            #debug self.date_obs_n = None

            # date Obs2 dans WDS
            self.wds_Obs2 = ''
            
            # différence en jours entre première et dernière observation
            #debug self.delai_entre_N = 0
            
            # état de la session, inscrire 'L' en position 3 pour 'Lucky imaging'
            # réfère à codes_etat_obs_dict
            # sera renseigné dans calculer_pour_publication
            #debug self.etat = list('  L')


    def creer_reductions_des_observations_df(self):
        """
        Crée le Pandas dataframe reductions_des_observations_df qui contient
        le  détail de toutes les réductions.
        """
        # pour chacun des N (observations)
    
        for obs in self.N:
            #print('Observation no. {0}'.format(obs.N))
            # pour chacun des bloc
            for b in obs.lstBlocs:
                # produire un df avec les données
                # prog_obs, system, id_wds, paire, const, N, b, dt_obs_utc,\
                #    epoque, rho, rho_sigma, pos, pos_sigma
                
                data = [\
                         self.prog,\
                         self.systeme.nom,\
                         'WDS ' + self.systeme.informations_df.loc[0].id_WDS,
                         self.paire,
                         self.systeme.informations_df.loc[0].const,
                         obs.N,\
                         b.indexBloc,\
                         b.sep.dtime_utc_acq.value,\
                         b.sep.dtime_utc_acq.byear,\
                         b.reduc.rho,\
                         b.reduc.rho_sigma,\
                         b.reduc.theta,\
                         b.reduc.theta_sigma,
                         'observatoire',
                         'observateur',
                         # seuls les éléments de l'environnement sep
                         # sont utilisées
                         b.sep.transp,
                         b.sep.seeing,
                         b.sep.temp_to,
                         b.sep.humid,
                         b.sep.press_bar,
                         b.sep.map,
                         b.reduc.deltaMatrixReducValide,
                         b.reduc.delaiDepuisAcqEchValide,
                         b.reduc.deltaTemperatureValide,
                         b.pos.eval_Q,
                         b.reduc.lstIndexCalE,
                         b.reduc.E_moy,
                         'filtre'
                         ]
                self.reductions_des_observations_df.loc[self.reductions_des_observations_df.index.size] = data


    def calculer_pour_publication(self):
        """
        À partir de moyennes_par_session_df, regroupe les observations qui
        respectent Le délai entre la première et la dernière observation
        <= MAX_DELAI_ENTRE_OBSERVATIONS et produit
        resultats_pour_publication_df.

        resultats_pour_publication_df sera utilisé pour le sommaire final des
        observations, aussi bien dans le Jupyter notebook des observations que
        dans le module listeReductions.
        
        Le champ «État» de resultats_pour_publication_df présente un sommaire
        des résultats du programme.
        """
        
        # recherche id WDS de la source et paire pour obtenir Obs2, pa2 et
        # sep2 == année et valeurs dernière observation
        # ces résultats seront incluses dans les repports pour comparaison
        #
        result_rech_WDS = rech_wds(self.systeme.nom, self.paire)
        self.wds_Obs2 = result_rech_WDS[0]['Obs2'].item()
        self.wds_pa2 = result_rech_WDS[0]['pa2'].item()
        self.wds_sep2 = result_rech_WDS[0]['sep2'].item()

        # colonnes de resultats_pour_publication_df
        lstCol_resultats_pour_publication_df = ['prog', 'id_system', 'pr',\
        'con', 'N', 'groupe', 'Dates_UTC', 'delai_entre_N', 'Liste sessions (N)', 'epoque',\
        'pa', 'pa_sig', 'sep', 'sep_sig',\
        'WDS_o2', 'WDS_pa2', 'WDS_sep2',\
        'État']
        
        # créer resultats_pour_publication_df vide
        #
        self.resultats_pour_publication_df =\
            pd.DataFrame(list(), columns=lstCol_resultats_pour_publication_df)

        #
        # produire la liste des tuples (sessions, dates) à partir
        # de moyennes_par_session_df
        #
        for idx in self.moyennes_par_session_df.index:
            self.lst_tup_dates.append((self.moyennes_par_session_df.loc[idx, 'N'],\
                       self.moyennes_par_session_df.loc[idx, 'Date_UTC']))

        if len(self.lst_tup_dates) == 1:
            # il y une seule session, alors
            # créer une liste 'artificielle' de la sorte
            # [(1, '2021-10-12'), (1, '2021-10-12'), 1)]
            # en répétant le tuple
            #
            self.lst_tup_dates.append(self.lst_tup_dates[0])

        # produire la liste des délais sous la forme
        # [(1, '2021-10-12'), (3, '2021-10-17'), 5] où
        # le délai entre session 1 et 3 est de 5 jours
        liste_des_delais_sessions = produire_liste_delais(self.lst_tup_dates)
 
        #
        # produire le dataframes des groupes d'observations dans
        # groupes_de_sessions_df
        # sous la forme
        '''
            Groupe                                         Dates_UTC delai_entre_N (j)  Liste sessions (N)
          0    (1)                          [2021-10-12, 2021-10-14]                 2              [1, 2]
          1    (2)                          [2021-10-17, 2021-10-19]                 2              [3, 4]
          2    (3)                          [2021-10-14, 2021-10-17]                 3              [2, 3]
          3    (4)              [2021-10-12, 2021-10-14, 2021-10-17]                 5           [1, 2, 3]
        '''
        
        if False:
            pass
        else:
            int_groupe = 1
            for groupe in liste_des_delais_sessions:
                delai = groupe[2]
                if delai <= MAX_DELAI_ENTRE_OBSERVATIONS:
                    str_groupe = '(' + str(int_groupe) + ')'
                    dates = list()
                    for idx in range(groupe[0][0], groupe[1][0]+1):
                        dates.append(self.lst_tup_dates[idx-1][1])
                    #dates = groupe[0] + groupe[1]
                    delai = str(groupe[2])
                    sessions = list()
                    for i in range(groupe[0][0], groupe[1][0]+1):
                        sessions.append(i)
                    data = [str_groupe, dates, delai, sessions]
                    # ajouter data à la fin du df ...index.size
                    self.groupes_de_sessions_df.loc[self.groupes_de_sessions_df.index.size] = data
                    int_groupe += 1

        #
        # parcourir groupes_de_sessions_df et calculer les moyennes à partir
        # de self.moyennes_par_session_df
        #
        for index_groupe in self.groupes_de_sessions_df.index:
            str_groupe = self.groupes_de_sessions_df.loc[index_groupe, 'Groupe']
            lst_str_dates =  self.groupes_de_sessions_df.loc[index_groupe, 'Dates_UTC']
            str_delai =  self.groupes_de_sessions_df.loc[index_groupe, 'delai_entre_N (j)']
            lst_int_sessions_du_groupe = self.groupes_de_sessions_df.loc[index_groupe, 'Liste sessions (N)']
            
            # calculer les moyennes des sessions qui se trouvent dans
            # lst_int_sessions_du_groupe
            if len(lst_int_sessions_du_groupe) == 1:
                # le groupe contient une seule observation
                # éviter de calculer la moyenne sur une seule observation
                # juste retourner les valeurs dans self.moyennes_par_session_df
                #
                nbrSessions = 1
                no_de_session = lst_int_sessions_du_groupe[0]
                # trouver l'index de no_de_session dans
                # self.moyennes_par_session_df
                #
                index_de_no_de_session = self.moyennes_par_session_df.\
                  loc[self.moyennes_par_session_df.N==no_de_session].index[0]
                
                rho_moy    = self.moyennes_par_session_df.loc[index_de_no_de_session,'rho_moy']
                rho_sigma_moy = self.moyennes_par_session_df.loc[index_de_no_de_session,'rho_sigma_moy']
                theta_moy  = self.moyennes_par_session_df.loc[index_de_no_de_session,'theta_moy']
                theta_sigma_moy = self.moyennes_par_session_df.loc[index_de_no_de_session,'theta_sigma_moy']
                
                epoque_moy = self.moyennes_par_session_df.loc[index_de_no_de_session,'epoque_moy']
                #Date_UTC = self.moyennes_par_session_df.loc[index_de_no_de_session,'Date_UTC']
                
            else:
                # lst_int_sessions_du_groupe contient la liste exhaustive des
                # sessions d'observations PAS UN INTERVAL!!!
                #
                # parcourir lst_int_sessions_du_groupe et calculer les moyennes
                # avec chaque sessions à partir de self.moyennes_par_session_df
                # par ex. si lst_int_sessions_du_groupe = [1,3, 4], il faut
                # parcourir session 1, 3 et 4 de self.moyennes_par_session_df
                #
                
                nbrSessions = len(lst_int_sessions_du_groupe)
                rho_m, theta_m, epoque_m, rho_sigma_m, theta_sigma_m =\
                    0, 0, 0, 0, 0
                    
                for no_de_session in lst_int_sessions_du_groupe:
                    # trouver l'index de no_de_session dans
                    # self.moyennes_par_session_df
                    #
                    index_de_no_de_session = self.moyennes_par_session_df.\
                      loc[self.moyennes_par_session_df.N==no_de_session].index[0]

                    #        
                    # calculer les sommes = numérateurs des moyennes
                    #
                      
                    rho_m += self.moyennes_par_session_df.loc[index_de_no_de_session,'rho_moy']
                    # propagation des incertitudes rho_sigma
                    rho_sigma_m += math.pow(self.moyennes_par_session_df.loc[index_de_no_de_session,'rho_sigma_moy'],2)
                    
                    theta_m += self.moyennes_par_session_df.loc[index_de_no_de_session,'theta_moy']
                    # propagation des incertitudes theta_sigma
                    theta_sigma_m += math.pow(self.moyennes_par_session_df.loc[index_de_no_de_session,'theta_sigma_moy'],2)
                    
                    epoque_m += self.moyennes_par_session_df.loc[index_de_no_de_session,'epoque_moy']
                    # Date_UTC sera la dernière date lue dans le groupe
                    #dern_obs_utc = self.moyennes_par_session_df.loc[index_de_no_de_session,'Date_UTC']

                #
                # calculer les moyennes et propager les incertitudes
                #
                rho_moy = rho_m / nbrSessions
                theta_moy = theta_m / nbrSessions
                epoque_moy = epoque_m / nbrSessions

                # theta_sigma_moy
                theta_sigma_moy = math.sqrt(theta_sigma_m) / nbrSessions
        
                # rho_sigma_moy
                rho_sigma_moy = math.sqrt(rho_sigma_m) / nbrSessions

        #
        # produire resultats_pour_publication_df avec ces résultats
        #
        # déterminer le code d'état
        #

        # état de la session, inscrire 'L' en position 3 pour 'Lucky imaging'
        # réfère à codes_etat_obs_dict
        # sera renseigné plus loin ...
        etatDuGroupe = list('  L')
        
        if nbrSessions > 1:
            etatDuGroupe[0] = 'T'
            etatDuGroupe[1] = 'O'
        else:
            # dans le cas d'une session avec N==1, il faut voir s'il y a plus
            # de MAX_DELAI_ENTRE_OBSERVATIONS jours depuis la date unique qui
            # se trouve dans lst_str_dates
            maintenant = datetime.now().date().isoformat()
            delai = int(diff_dt(maintenant, lst_str_dates[0]).value)
            if delai > MAX_DELAI_ENTRE_OBSERVATIONS:
                etatDuGroupe[0] = 'T'
                etatDuGroupe[1] = 'A'
                
                
            
        
        # produite une chaîne avec les codes d'état
        #
        strEtat = ''
        for i in range(0, len(etatDuGroupe)):
            strEtat += etatDuGroupe[i]

        data = [
           self.prog,\
           self.systeme.nom,\
           self.paire,\
           self.systeme.informations_df.loc[0,'const'],\
           nbrSessions,\
           str_groupe,\
           lst_str_dates,\
           str_delai,\
           lst_int_sessions_du_groupe,\
           epoque_moy,\
           theta_moy,\
           theta_sigma_moy,\
           rho_moy,\
           rho_sigma_moy,\
           self.wds_Obs2,\
           self.wds_pa2,\
           self.wds_sep2,\
           strEtat
        ]
        self.resultats_pour_publication_df.loc[self.resultats_pour_publication_df.index.size] = data
              
            
            
    def calculer_moyennes_par_session(self):
        """
        À partir de reductions_des_observations_df, calcule les moyennes des
        sessions d'observations (N) du programme d'observations et produit
        le pandas dataframe moyennes_par_session_df. Pour une session, les
        moyennes doivent être calculées à partir des résultats des blocs
        d'observations qui respecte Les critères de validité
        des facteurs environnementaux suivants :
           - mises au point (map) inchangées au cours des acquisitions;
           - les écarts de tempé. <= MAX_DELTA_TEMPERATURE;
           - le délai depuis dern. aqui. d'éch. <= MAX_DELAI_DEPUIS_ACQUISITIONS_ECHELLE
        
        moyennes_par_session_df contient les moyennes calculées
        pour chacune des sessions d'observation valides avec les critères
        de validité.
        
        moyennes_par_session_df sera utilisé pour resultats_pour_publication_df,
        aussi bien dans le Jupyter notebook des observations que
        dans le module listeReductions.
        """
        # créer moyennes_par_session_df vide avec les colonnes suivantes
        lstCol = ['N', 'Date_UTC', 'epoque_moy',\
        'rho_moy', 'rho_sigma_moy', 'theta_moy', 'theta_sigma_moy',
        'deltaTemperatureValide', 'delaiDepuisAcqEchValide',
        'deltaMatrixReducValide'
        ]
        self.moyennes_par_session_df = pd.DataFrame(list(), columns=lstCol)
        
        # extraire la liste des valeurs des N dans tempo
        # de reductions_des_observations_df
        tempo = self.reductions_des_observations_df.loc[:,'N']
        
        # produire le set des no de sessions N
        listeDesSessions = set()
        for idx in tempo.index:
            listeDesSessions.add(tempo[idx])
            
        for session in listeDesSessions:
            # il faut travailler avec les blocs de chaque N de
            # self.reductions_des_observations_df
            # extraire ces blocs dans session_df
            session_df = self.reductions_des_observations_df[self.\
                                   reductions_des_observations_df.N == session]
            if len(session_df) == 1:
                # un seul bloc d'observations, donc on retourne simplement
                # l'enregistrement
                idx = session_df.index[0]
                rho_moy    = session_df.loc[idx,'rho']
                theta_moy  = session_df.loc[idx,'theta']
                epoque_moy = session_df.loc[idx,'obs_epoque_B']
                dern_obs_utc = session_df.loc[idx,'Date_UTC'].split('T')[0]
                theta_sigma_moy = session_df.loc[idx,'theta_sigma']
                rho_sigma_moy = session_df.loc[idx,'rho_sigma']

                valideTemperature = session_df.loc[idx,'deltaTemperatureValide']
                valideInterval = session_df.loc[idx,'delaiDepuisAcqEchValide']
                valideMatrix = session_df.loc[idx,'deltaMatrixReducValide']

            
            else:
                # la session contient plus d'un bloc d'observations
                #        
                # calculer les moyennes
                #
                # if deltaMatrixReducValide, delaiDepuisAcqEchValide
                interval_idx = range(session_df.index[0], session_df.index[1]+1)

                # Vérifier deltaMatrixReducValide, delaiDepuisAcqEchValide
                # et deltaTemperatureValide
                
                # récupérer les valeurs de validité dans des Tupples
                deltaTemperatureValide =\
                    session_df.loc[interval_idx,'deltaTemperatureValide']
                delaiDepuisAcqEchValide =\
                    session_df.loc[interval_idx,'delaiDepuisAcqEchValide']
                deltaMatrixReducValide =\
                    session_df.loc[interval_idx,'deltaMatrixReducValide']

                # combiner chaque Tupples en une valeur booléenne unique
                valideTemperature = True
                for val in deltaTemperatureValide:
                    valideTemperature = valideTemperature and val

                valideInterval = True
                for val in delaiDepuisAcqEchValide:
                    valideInterval = valideInterval and val

                valideMatrix = True
                for val in deltaMatrixReducValide:
                    valideMatrix = valideMatrix and val
                    
                # calculer les moyennes

                rho_moy      = session_df.loc[interval_idx,'rho'].mean()
                theta_moy    = session_df.loc[interval_idx,'theta'].mean()
                epoque_moy   = session_df.loc[interval_idx,'obs_epoque_B'].mean()
                dern_obs_utc = session_df.loc[interval_idx,'Date_UTC']\
                    [session_df.index[1]].split('T')[0]
        
                # propager les incertitudes theta_sigma
                tempo = 0
                for val in session_df.loc[interval_idx,'theta_sigma']:
                    tempo += math.pow(val, 2)
                theta_sigma_moy = math.sqrt(tempo) / len(session_df)
        
                # propager les incertitudes rho_sigma
                tempo = 0
                for val in session_df.loc[interval_idx,'rho_sigma']:
                    tempo += math.pow(val, 2)
                rho_sigma_moy = math.sqrt(tempo) / len(session_df)
            
            #
            # pour la session en cours
            # produire moyennes_par_session_df avec ces résultats
            # y compris les critères de validité
            #
            lstData = [
               session,\
               dern_obs_utc,\
               epoque_moy,\
               rho_moy,\
               rho_sigma_moy,\
               theta_moy,\
               theta_sigma_moy,\
               valideTemperature,\
               valideInterval,\
               valideMatrix
            ]
            self.moyennes_par_session_df.loc[self.moyennes_par_session_df.index.size] = lstData


    def imprimerRapport(self, typeRapport='m'):
        """
        Imprime le rapport selon le type passé en paramètre.
    
        Paramètres Keyword :
         typeRapport -- 'l' champs partiels
         typeRapport -- 'c' données complète des sessions
         typeRapport -- 'm' moyennes des sessions (par défaut)
        """

        pd.set_option('display.expand_frame_repr', True)
        pd.set_option('display.colheader_justify', 'right')
        pd.set_option('display.max_colwidth', 50)
        pd.set_option('display.max_column', 30)
        pd.set_option('display.width', 100)
        pd.set_option("precision", 4)
        i = self.reductions_des_observations_df.index.size


        # 'm' == moyenne de toutes les observati        ns et leurs blocs
        #
        if typeRapport == 'm':
            print(NL)
            print('MOYENNES PAR SESSION')
            print(self.moyennes_par_session_df)
            print(NL)
            print('Sommaire des dates des sessions :')
            print(self.lst_tup_dates)
            print(NL)
            print('CANDIDATS DES REGROUPEMENTS DES SESSIONS POUR PUBLICATION')
            print(self.groupes_de_sessions_df.to_string(index=False))

            print(NL)
            print("MOYENNES DES GROUPES D'OBSERVATIONS (POUR PUBLICATION)")
            print('-'*pd.get_option('display.width'))
            print(self.resultats_pour_publication_df)
            print('-'*pd.get_option('display.width'))
            print(NL)
            for code in codes_etat_obs_dict:
                print(' ', code, codes_etat_obs_dict[code])
        

        # 'l' == liste d'une partie des champs des observations et leurs blocs
        # seulement pour impression, pas de structure de données créée
        if typeRapport == 'l':
            print(NL)
            #debug print('#'*25)
            print("RAPPORT D'OBSERVATION\n")
            print("Système")
            print('-'*100)
            print(self.systeme.informations_df.to_string(index=False))
            #print(self.systeme.informations_df)
            #print(NL)
            print('-'*100)
            print("    Paire : {0}".format(self.paire))
            print("Programme : {0}".format(self.prog))
            print('-'*100)
            
            print("\nCOMPILATION DES BLOCS D'OBSERVATIONS POUR UNE RÉDUCTION COMPLÈTE")
            # pour chacun des N (observations)
            # on désire imprimer les champs suivants (et dans cet ordre) :
            lstChamps = [\
                         'N',\
                         'bloc',\
                         'Date_UTC',\
                         'obs_epoque_B',\
                         'theta',\
                         'theta_sigma',\
                         'rho',\
                         'rho_sigma',\
                         'transp',\
                         'seeing',\
                         'temp_to',\
                         'humid',\
                         'press_bar',\
                         'map',\
                         'lstIndexCalE',\
                         'E_moy',\
                         'eval_Q',\
                         'delaiDepuisAcqEchValide',\
                         'deltaTemperatureValide',\
                         ]
            print(self.reductions_des_observations_df.loc[range(0,i), lstChamps].to_string(\
                index=False,\
                max_colwidth=35,
                line_width=100,
                justify='right'
                ))
            #print(self.reductions_des_observations_df.loc[range(0,i), lstChamps])
            
        # 'c' == toutes les données de toutes les observations et leurs blocs
        # seulement pour impression, pas de structure de données créée
        if typeRapport == 'c':
            print(NL)
            print("RÉDUCTION COMPLÈTE")
            
            # en-tête des sessions
            print('-'*100)
            print(self.systeme.informations_df.to_string(index=False))
            print('-'*100)
            print("    Paire : {0}".format(self.paire))
            print("Programme : {0}".format(self.prog))
            print('\n')
            print("DÉTAILS DES BLOCS D'OBSERVATIONS")
            print('-'*100)
            print(self.reductions_des_observations_df)

            
    def hier(self, sortie='terminal'):
        """
        Produit (Print) la hiérarchie complète de l'objet DoubleSessions (self)
    
        Paramètre Keyword :
         sortie -- String 'terminal' :
          par défaut sortie au terminal
         sortie -- String 'fichier'
          Sortie dans fichier ./out.txt (écrasement contenu si fichier présent)
        """

        if sortie.upper() == 'FICHIER':
            # sortie vers fichier out.txt dans rép d'exécution
            ancien_stdout = sys.stdout
            f = open('out.txt', 'w')
            sys.stdout = f

        print('-'*102)
        #debug print('{0} :'.format(self.systeme.nom))
        print(self.systeme.informations_df)
        print('-'*102)
        
        # puisqu'ils ne change pas durant les observations, tirer typeObservation,
        # et le nom de la paire de la première observation de la liste
        if self.N[0].tobs == 'complete':
            print(' Paire     : {0}'.format(self.paire))
            print(' Programme : {0}\n'.format(self.prog))
        
        print(NL)
        print('-'*127)
        print('MOYENNES DES OBSERVATIONS')
        print(self.resultats_pour_publication_df)
        print('\r')
        
        for obs in self.N:
            print('#'*64)
            print('Observation no {0} de type «{1}», contenant {2} bloc{3}'.format(\
                         obs.N, obs.tobs, obs.nb, 's' if obs.nb > 1 else '') )
            print('Chemin {0} : '.format(obs.cheminN))
            print('#'*64)
            if obs.tobs == 'ech':
                for b in range(obs.nb):
                    print('    ' + '#' * 14)
                    print('  bloc {0}'.format(obs.lstBlocs[b].indexBloc+1))
                    print('    ' + '#' * 14)
                    for key in obs.lstBlocs[b].__dict__.keys():
                        print("        {0} = {1}".format(key, obs.lstBlocs[b].__dict__[key]))
                        if key == 'ech':
                            for key2 in obs.lstBlocs[b].__dict__[key].__dict__.keys():
                                print("{0}{1} = {2}".format(' '*12, key2, obs.lstBlocs[b].__dict__[key].__dict__[key2]))
                        if key == 'reduc':
                            for key2 in obs.lstBlocs[b].__dict__[key].__dict__.keys():
                                print("{0}{1} = {2}".format(' '*12, key2, obs.lstBlocs[b].__dict__[key].__dict__[key2]))
        
                print('\r')
            
            if obs.tobs == 'complete':
                for b in range(obs.nb):
                    print(NL)
                    print('        ' + '#' * 14)
                    print('         Obs {0}, bloc {1}'.format(obs.N, obs.lstBlocs[b].indexBloc))
                    print('        ' + '#' * 14)
                    print('\r')
                    for key in obs.lstBlocs[b].__dict__.keys():
                        print("        {0} = {1}".format(key, obs.lstBlocs[b].__dict__[key]))
                        if key == 'sep':
                            for key2 in obs.lstBlocs[b].__dict__[key].__dict__.keys():
                                print("{0}{1} = {2}".format(' '*12, key2, obs.lstBlocs[b].__dict__[key].__dict__[key2]))
                        if key == 'pos':
                            for key2 in obs.lstBlocs[b].__dict__[key].__dict__.keys():
                                print("{0}{1} = {2}".format(' '*12, key2, obs.lstBlocs[b].__dict__[key].__dict__[key2]))
                        if key == 'reduc':
                            for key2 in obs.lstBlocs[b].__dict__[key].__dict__.keys():
                                if 'reduc_brute_df' in key2:
                                    print('reduc_brute_df :')
                                    print(obs.lstBlocs[b].__dict__[key].__dict__[key2])
                                else:
                                    print("{0}{1} = {2}".format(' '*12, key2, obs.lstBlocs[b].__dict__[key].__dict__[key2]))
                                
                print('\r')
                
        if sortie.upper() == 'FICHIER':
            f.close()
            sys.stdout = ancien_stdout


            
# %% FONCTIONS
def version():
    print(__name__ + ' version ' + str(no_version) + ', février 2022.')

def inscrire_dans_log(strinscription):
    lst_log_post_reduction.append(strinscription)

def ecrire_log_sur_disque(ncflog=''):
    with open(ncflog, 'w') as f:
        # écrire le contenu du log
        for ligne in range(len(lst_log_post_reduction)):
            f.write(lst_log_post_reduction[ligne])
            f.write(NL)
    f.close()

def produire_liste_delais(liste_tup_dates):
    """
    Parameters
    ----------
    lst_dates : TYPE
        DESCRIPTION.

    Returns
    -------
     lst_des_delais

    """
    # trier la liste des tuples sur la date (index 1)
    liste_tup_dates.sort(key=lambda tup: tup[1], reverse=False)
    lst_intervalles = list()
    fin = len(liste_tup_dates) - 1
    for r in range(0, fin):
        debut = r
        fin = debut + 1
        while fin < len(liste_tup_dates):
            delai = int(diff_dt(liste_tup_dates[debut][1], liste_tup_dates[fin][1]).value)
            if delai != None:
                lst_intervalles.append((debut, fin, delai))
            fin += 1
        
    # créer une nouvelle liste des tuples avec le delai entre chaque couple
    tempo = list()
    for couple in lst_intervalles:
        date1 = liste_tup_dates[couple[0]]
        date2 = liste_tup_dates[couple[1]]
        #delai = abs(date2[1] - date1[1])
        delai = int(diff_dt(date2[1], date1[1]).value)
        tempo.append([date1, date2, delai])
        
    # retourner liste triée sur délai et trouver le miminum
    tempo.sort(key=lambda tup: tup[2], reverse=False)
        
    return tempo


def produire_systag():
    """
    Retourne un systag (système tag), c.-à-d. la date du système au format iso
    """
    return datetime.now().isoformat().split('.')[0].replace(':','')

def post_reduction(type_obs='complete', ch_prog=''):
    """
    Effectue la post-réduction des données du chemin passé en paramètre selon le
    type d'observation. Retourne un objet Observations pour une observation de
    type 'ech' ou un objet DoubleSessions pour une observation de type
    'complete'.
    
    Retourne None en cas d'erreur

    Paramètres keywords :
    type_obs -- String :
       'ech'         -- réduction d'échelle
       'complete'    -- réduction complète (par défaut)
    ch_prog -- String chemin du dossier du programme d'observation
    """

    ################
    # Tronc commun #
    ################
    
    # fichier log de réduction et liste des lignes du log
    #
    ncfichier_log_post_reduction = ch_prog + '/post-réduction.log'

    # inscrire systag dans lst_log_post_reduction
    inscrire_dans_log(produire_systag())

    # lire le fichier observatoires dans un df
    # lire les fichiers de support (maîtres de calibrations, etc)
    # et placer dans master_calibrations_e_df, master_filtres_cal_df, master_masques_cal_df
    #
    resultatOK = lire_fichiers_support(type_obs, ch_prog)
    if not resultatOK:
        ecrire_log_sur_disque(ncflog=ncfichier_log_post_reduction)
        # retourner None en cas d'erreur fatale
        return None
    
    resultatOK = lire_fichier_observatoires()
    if not resultatOK:
        ecrire_log_sur_disque(ncflog=ncfichier_log_post_reduction)
        # retourner None en cas d'erreur fatale
        return None


    ######################
    # Réduction complète #
    ######################

    if type_obs == 'complete':
        # Dans ce cas, ch_prog doit être dossier du type P2021-023 et avoir
        # au moins un N avec au moins un bloc d'observation. On doit bâtir un
        # objet doublesoutuils.DoubleSessions.
        #

        ###################################################
        # créer l'objet sessions
        ###################################################
        # Dans l'objet sessions, l'objet Systeme sera créé à partir du chemin du système.
        # Remonter au dossier du système à partir du dossier de ch_prog
        # par «STTA254» dans D:\DOCUMENTS\Astronomie\...\STTA254\AB\P2021-023
        sessions = DoubleSessions(typeObs=type_obs, chProg=ch_prog)
            
        # nom de la paire dans sessions
        sessions.paire = path.basename(path.dirname(ch_prog))

        # créer la liste des observations de sessions selon type_obs
        # le nombre de N sera placé dans sessions.nbrN
        sessions.N,  sessions.nbrN = creeLstObjObservations(type_obs,\
                               ch_prog, sessions.systeme.nom)

        if sessions.N is None:
            ecrire_log_sur_disque(ncflog=ncfichier_log_post_reduction)
            # retourner None en cas d'erreur fatale
            return None
        
        ######################################################################
        # boucle de réduction complète pour toutes les blocs d'observations  #
        ######################################################################

        for obs in sessions.N:
            for bloc in obs.lstBlocs:
                # lire et extraire données du log d'acquisition et
                # d'environnement sep et pos
                extraire_Log_acq_env(obs, bloc.indexBloc, 'sep')
                extraire_mesure_brutes_logReduc(obs, bloc.indexBloc, 'sep')
                extraire_Log_acq_env(obs, bloc.indexBloc, 'pos')
                extraire_mesure_brutes_logReduc(obs, bloc.indexBloc, 'pos')
                
                #################################################
                #                 Réduction de sep
                #################################################

                # relecture du fichier des mesures brutes sep dans un dataframe
                # Pandas
                bloc.reduc.relecture_mes_brutes(path.dirname(bloc.reduc.ncflr_sep) +\
                                              '/' + fich_mesures_brutes)
                ####################################
                # validations générales pour sep
                # sortir si non valide
                if not bloc.validations(obs.N):
                    ecrire_log_sur_disque(ncflog=ncfichier_log_post_reduction)
                    return None

                ####################################
                # Calculs rho
                # NOTE : la valeur de thêta est dans la réduction de pos
                bloc.reduc.calcule_rho(obs.N, bloc.indexBloc)

                
        
        # création de l'objet DoubleSessions.reductions_des_observations_df
        sessions.creer_reductions_des_observations_df()
        
        # calcule les moyennes par session d'observations
        sessions.calculer_moyennes_par_session()
        
        # production des valeurs moyennes des sessions pour rho, theta,
        # epoque avec la propagation des incertitudes
        #
        # ce sont les résultats qui sont succeptibles d'être publiées
        #
        sessions.calculer_pour_publication()
        
        # sauvegarder l'objet sessions dans le dossier dU PROGRAMME de la paire
        tempo = ch_prog + '/' + sessions.systeme.nom + '_' +\
                   sessions.paire + '_' + sessions.prog  + '_sessions.obj'
        filehandler = open(tempo, 'wb')
        pickle.dump(sessions, filehandler)
        filehandler.close()
        
        inscrire_dans_log('\nTraitement terminé. Sessions enregistrées dans :')
        inscrire_dans_log(" ... «{0}»".format(tempo))

        inscrire_dans_log("Réduction complétée.")
        ecrire_log_sur_disque(ncflog=ncfichier_log_post_reduction)
        return sessions

    ###############################
    # Réduction D'échelle
    ###############################

    if type_obs == 'ech':
        # créer la liste des observations selon type_obs
        # créer l'objet sessions
        # (pas d'objet Systeme)

        lstObservations, n = creeLstObjObservations(type_obs, ch_prog)
        # toujours n == 0 dans ce cas

        if lstObservations is None:
            ecrire_log_sur_disque(ncflog=ncfichier_log_post_reduction)
            # retourner None en cas d'erreur fatale
            return None

        # Il n'y a pas de boucle puisqu'il n'y a pas de N et la notion de bloc
        # est intégrée dans le nom de dossier d'acquisition (par ex. 2020-10-08b01).
        # Extraire les données du log d'acquisition et d'environnement, puis
        # comme pour le type de mesure 'sep', extraire et exporter
        # les mesures brutes à partir du log de REDUC  dans un csv
        
        observation = lstObservations[0]
        extraire_Log_acq_env(observation, 1, 'sep')
        extraire_mesure_brutes_logReduc(observation, 1, 'sep')
        
        # lecture des mesures brutes dans un dataframe Pandas
        observation.lstBlocs[0].reduc.relecture_mes_brutes(path.dirname(observation.lstBlocs[0].reduc.ncflr_sep) +\
                                              '/' + fich_mesures_brutes)
        
        # passer LfplusDf, LfplusDf_sigma, Lo et Lo_sigma pour le calcul de Z
        observation.lstBlocs[0].reduc.calcule_Z(\
           observation.lstBlocs[0].reduc.LfplusDf,\
           observation.lstBlocs[0].reduc.LfplusDf_sigma,\
           observation.lstBlocs[0].reduc.Lo,\
           observation.lstBlocs[0].reduc.Lo_sigma\
        )
        observation.lstBlocs[0].reduc.calcule_E()
        imprime_rapport_E(observation)
        maj_master_calibrations(observation)
        
        # terminer le log et écrire sur disque
        inscrire_dans_log("Réduction terminée.")
        ecrire_log_sur_disque(ncflog=ncfichier_log_post_reduction)
        return observation


def convertToFloat(strVal):
    try:
        return float(strVal)
    except ValueError:
        print("{0} --> conversion à float impossible.".format(strVal))
        sys.exit()


def trouverLogReduc(ch):
    """
    Retourne le nom complet du fichier log de réduction (REDUC) RLog_*.txt 
    si présent dans le chemin passé en paramètre une chaîne vide sinon.

    Paramètre positionnel :
    ch -- String chemin du dossier d'où commencer la recherche.
    """

    for root, dirs, files in os.walk(ch):
        for name in files:
            if os.path.isfile(os.path.join(root, name)):
                if 'RLog_' in name:
                    return name
    return None


def trouverLogsAetE(chemin, nomSysteme):
    """
    Parcourt chemin et retourne ncfla et ncfle contenant respectivement le nom
    du fichier log d'acquisition (txt) et le nom du fichier environnement.txt
    présents dans chemin.
    
    Puisque le nom du fichier log d'acquisition est à la discrétion de
    l'observateur, la validité de celui-ci est vérifiée par la présence de la
    chaîne 'FireCapture' sur la première ligne du premier fichier txt trouvé
    autre que «environnement.txt».

    Paramètres positionnels :
    chemin     -- String chemin complet à parcourir
    nomSysteme --  String nom du système (ex. 'STTA254')
    """

    fla, fle = None, None
    # trouver et vérifier la validité des fichiers
    lstFichiersTxt = glob.glob(chemin + '/*.txt')
    for f in lstFichiersTxt:
        if 'environnement' in f:
            fle = f
        else:
            # lire la première ligne de f et voir
            # si 'FireCapture' se trouve sur la première ligne
            try:
                with open(f) as fich:
                    line = next(fich).strip()
                    if 'FireCapture' in line:
                        fla = f
                fich.close()
                #break
            except StopIteration:
                pass
    return (fla, fle)


def liste_blocs(ch):
    """
    Parcourt le chemin passé en paramètre et retourne la liste (Liste) des
    chemins des rép des bloc d'observations (c.-à-d. les répertoires b01, b02,
    ..., présents dans le chemin).

    Paramètre positionnel :
    ch -- String chemin complet à parcourir

    """
    return glob.glob(ch + '/b*') 


def creeLstObjObservations(typeObs, cheminProgramme, nomSysteme=None):
    """
    Crée l'objet Observations selon le type d'observation passé en paramètre
    en parcourant cheminProgramme et retourne un Tupple contenant la liste
    (List) des objets Observation et un int du nombre d'observations (sessions).
    Retourne None, 0 si erreur.

    Paramètres positionnels :
     typeObs -- String type d'observation ('ech' ou 'complete')
     cheminProgramme -- String chemin complet du programme d'observatipn

    Paramètre Keyword :
     nomSysteme -- String nom du système (par défaut None
                                          si observation d'échelle)
    """
    
    # liste des sessions d'observations
    lstSessions = list()
    
    if typeObs == 'ech':
        #########################################
        # il s'agit d'une observation d'échelle
        #########################################

        '''
        Ce type d'observation ne comprend pas de dossiers N*. Il s'agit plutôt
        d'un dossier du type 2021-10-08b01 qui représente un seul bloc
        d'observation d'échelle. Il faut donc créer un objet Observation
        avec N=1 et ensuite créer l'unique bloc de typeObservation='ech'
        '''
        # trouver le nom complet fichier log réduction (ncflr)
        lst_ncflr = glob.glob(cheminProgramme + '/reduc/RLog_*.txt')

        if len(lst_ncflr) != 1:
            # erreur fatale, il n'y a pas eu réduction d'échelle, puisque ncflr absent
            tampon = "doublesoutils.creeLstObjObservations :: log de reduc absent dans " + cheminProgramme + '/reduc'
            inscrire_dans_log(tampon)
            return None, 0

        # nous avons un log reduc
        # rechercher le nom de l'index de calibration dans cheminProgramme
        # pattern de recherche pour la forme yyyy-mm-jjbnn (ex. 2021-11-08b02)
        str_re_pat = r'([0-9]{4}\-[0-9]{2}\-[0-9]{2}b[0-9]{2})'
        obj_pat = re.compile(str_re_pat)
        obj_match = obj_pat.search(cheminProgramme)
        
        if obj_match is None:
            # erreur fatale, le nom du dossier ne respecte pas le format
            # pour les index de calibration
            tampon = "doublesoutils.creeLstObjObservations :: dans le chemin «" + cheminProgramme + '» :'
            inscrire_dans_log(tampon)
            tampon =  "... «{0}» n'est pas un nom d'index de calibration valide!".format(path.basename(cheminProgramme))
            inscrire_dans_log(tampon)
            return None, 0

        # nous avons un nom d'index de calibration valide
        #
        # trouver tous les *.txt dans cheminProgramme qui doivent comprendre
        # les logs d'acquisition et d'environnement (environnement.txt)
        lstFichiersTxt = glob.glob(cheminProgramme + '/*.txt')

        # rechercher ncfle et ncfla dans lstFichiersTxt
        # ncfle = nom complet fichier log environnement
        # ncfla = nom complet fichier log acquisition
        #
        ncfle, ncfla = None, None
        for f in lstFichiersTxt:
            if 'environnement' in f:
                ncfle = f
            else:
                # lire la première ligne de f et évaluer
                try:
                    with open(f) as fich:
                        line = next(fich).strip()
                        if 'FireCapture' in line:
                            ncfla = f
                    fich.close()
                    #debug break
                except StopIteration:
                    pass

        if ncfle is None:
            # erreur fatale
            tampon = "doublesoutils.creeLstObjObservations :: Erreur fichier log environnement manquant."
            inscrire_dans_log(tampon)
            return None, 0
        
        if ncfla is None:
            # erreur fatale
            tampon = "doublesoutils.creeLstObjObservations :: Erreur fichier log acquisition manquant."
            inscrire_dans_log(tampon)
            return None, 0

        # tout va bien
        # créer la liste d'observation avec un seul objet Observation
        lstSessions.append(Observation(1, 'ech')) # N=1

        # ajouter un seul bloc à cet objet Observation
        lstSessions[0].ajouteBloc(0, 'ech') # nbrBlocs = noBloc = 1
        
        # incrire ncfla et ncfle dans le bloc
        lstSessions[0].lstBlocs[0].ech.ncfle = ncfle
        lstSessions[0].lstBlocs[0].ech.ncfla = ncfla
        
        # placer l'index de calibration dans l'objet reduc de l'objet Observation,
        # bloc 1, (objet AcquisitionEchelle)
        lstSessions[0].lstBlocs[0].reduc.lstIndexCalE.append(obj_match.group(0))

        # inscrire nom complet fichier log réduction (ncflr)
        lstSessions[0].lstBlocs[0].reduc.ncflr_sep = lst_ncflr[0]
        return lstSessions, 0
        

    else:
        #
        # type_observation = 'complete'
        #
        
        # trouver tous les répertoires Nx dans cheminProgramme
        lstDesRepN = glob.glob(cheminProgramme + '/N*')
        nombreDeN = 0
        
        if len(lstDesRepN) == 0:
            # erreur fatale, il n'y a aucune session N
            tampon = "doublesoutils.creeLstObjObservations :: pas de session (N) dans " + cheminProgramme
            inscrire_dans_log(tampon)
            return None, 0
        
        # parcourir les dossiers de session N*
        for ch_rep_session_N in lstDesRepN:
            '''
            Ce type d'observation comprend un certain nombre de dossiers N* avec possiblement plusieurs
            blocs d'observation sep et pos.
            '''

            # information de base de la session, programme, système, paire et blocs d'observations
            # identifier d'abord le no de la session Nx
            tempo = path.basename(ch_rep_session_N)
            # N numéro effectif de l'obsersation (deviendra label 'N' dans _observations.csv)
            obs_N = int(tempo.strip('N'))
            
            # construire la liste des rép blocs d'observations bx, x=1, ...
            listeRepBlocs = liste_blocs(ch_rep_session_N)
                            # créer l'observation
                            
            # vérifier s'il existe des blocs
            if len(listeRepBlocs) == 0:
                # erreur fatale, il n'y a aucun bloc
                tampon = "doublesoutils.creeLstObjObservations :: pas de bloc dans " + cheminProgramme
                inscrire_dans_log(tampon)
                return None, 0
    
            # traiter tous les blocs
            #
            lstSessions.append(Observation(obs_N, 'complete'))

            # chemin du répertoire Nx
            lstSessions[nombreDeN].cheminN = ch_rep_session_N
            # nom du programme d'observations tiré du chemin du programme
            #debug obs_prog = path.basename(path.dirname(cheminProgramme))
            #debug lstSessions[nombreDeN].prog = path.basename(cheminProgramme)

            for repBlocCourant in listeRepBlocs:
                # récupérer le no du bloc
                #debug print("Traitement de " + repBlocCourant)
                noBlocCourant = int(path.basename(repBlocCourant).split('b')[1])

                ################################
                # préparation traitement de sep
                ################################
                # déterminer le log d'acquisition et environnement
                tempo = repBlocCourant + '/sep/'

                ncfla_sep, ncfle_sep = trouverLogsAetE(tempo, nomSysteme)
                if ncfle_sep is None:
                    # erreur fatale
                    tampon = "doublesoutils.creeLstObjObservations :: Erreur fichier log environnement manquant."
                    inscrire_dans_log(tampon)
                    tampon = "... {0}".format(tempo)
                    inscrire_dans_log(tampon)
                    return None, 0
                
                if ncfla_sep is None:
                    # erreur fatale
                    tampon = "doublesoutils.creeLstObjObservations :: Erreur fichier log acquisition manquant."
                    inscrire_dans_log(tampon)
                    tampon = "... {0}".format(tempo)
                    inscrire_dans_log(tampon)
                    return None, 0

                # trouver log de réduction de sep
                ncflr_sep = trouverLogReduc(repBlocCourant + '/sep/reduc')

                if ncflr_sep is None:
                    # erreur fatale
                    tampon = "doublesoutils.creeLstObjObservations :: Erreur fichier log REDUC manquant."
                    inscrire_dans_log(tampon)
                    tampon = "... {0}".format(repBlocCourant + '/sep/reduc')
                    inscrire_dans_log(tampon)
                    return None, 0

                ################################
                # préparation traitement de pos
                ################################
                # déterminer le log d'acquisition et environnement pos
                tempo = repBlocCourant + '/pos/'
                ncfla_pos, ncfle_pos = trouverLogsAetE(tempo, nomSysteme)
                if ncfle_pos is None:
                    # erreur fatale
                    tampon = "doublesoutils.creeLstObjObservations :: Erreur fichier log environnement manquant."
                    inscrire_dans_log(tampon)
                    tampon = "... {0}".format(tempo)
                    inscrire_dans_log(tampon)
                    return None, 0
                
                if ncfla_pos is None:
                    # erreur fatale
                    tampon = "doublesoutils.creeLstObjObservations :: Erreur fichier log acquisition manquant."
                    inscrire_dans_log(tampon)
                    tampon = "... {0}".format(tempo)
                    inscrire_dans_log(tampon)
                    return None, 0

                # trouver log de réduction de pos
                ncflr_pos = trouverLogReduc(repBlocCourant + '/pos/reduc')

                if ncflr_pos is None:
                    # erreur fatale
                    tampon = "doublesoutils.creeLstObjObservations :: Erreur fichier log REDUC manquant."
                    inscrire_dans_log(tampon)
                    tampon = "... {0}".format(repBlocCourant + '/pos/reduc')
                    inscrire_dans_log(tampon)
                    return None, 0

                # ajouter le bloc courant dans l'observation courante et
                # inscrire ncfla_sep, ncfle_sep et ncflr_sep
                # inscrire ncfla_pos, ncfle_pos et ncflr_pos
                lstSessions[nombreDeN].ajouteBloc(noBlocCourant, 'complete') # nbrBlocs = noBloc = 1
 
                # sep
                lstSessions[nombreDeN].lstBlocs[noBlocCourant-1].sep.ncfla =  ncfla_sep
                lstSessions[nombreDeN].lstBlocs[noBlocCourant-1].sep.ncfle =  ncfle_sep
                lstSessions[nombreDeN].lstBlocs[noBlocCourant-1].reduc.ncflr_sep =\
                    repBlocCourant + '/sep/reduc/' + ncflr_sep

                # pos
                lstSessions[nombreDeN].lstBlocs[noBlocCourant-1].pos.ncfla =  ncfla_pos
                lstSessions[nombreDeN].lstBlocs[noBlocCourant-1].pos.ncfle =  ncfle_pos
                lstSessions[nombreDeN].lstBlocs[noBlocCourant-1].reduc.ncflr_pos =\
                    repBlocCourant + '/pos/reduc/' + ncflr_pos
                
            nombreDeN += 1
        return lstSessions, nombreDeN


def extraire_Log_acq_env(obs, no_bloc, typeMesure):
    """
    Pour le no_bloc courant, repère les fichiers log d'acquisition et log de
    réduction et récupère diverses données dépendant du type de réduction
    ('ech' ou 'complete') et du types de mesure ('ech', 'sep' ou 'pos').
    Également, le fichier« environnement.txt» est lu et traité.

    S'il sagit d'une réduction d'échelle ('ech'), on en profite pour récupérer id_masque
    et id_filtre qui se trouvent dans environnement.txt.
    
    Les données sont colligées dans les objets Acquisition appropriés de l'objet Observation
    passé en paramètre.
    
    Note : dans le cas d'une réduction d'échelle ('ech') le type de mesure (.typeMesure) est
    toujours 'sep', N==1 et no_bloc==1.

    Paramètres positionnels :
    obs -- objet Observation
    no_bloc -- int no du no_bloc traité
    typeMesure -- String 'pos' ou 'sep'
    """

    # fle = nom complet du fichier log environnement
    if obs.tobs == 'ech':
        fle = obs.lstBlocs[no_bloc-1].ech.ncfle

    if obs.tobs == 'complete':
        if typeMesure == 'pos':
            fle = obs.lstBlocs[no_bloc-1].pos.ncfle
        if typeMesure == 'sep':
            fle = obs.lstBlocs[no_bloc-1].sep.ncfle
    with open(fle) as f:
        lignesLues = f.readlines()
    f.close()

    ################################################
    # extraction des données du log d'environnement
    ################################################

    for ligne in lignesLues:
        if obs.tobs == 'ech':
            # id_masque
            ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
            if 'masque=' in ligneForm:
                obs.lstBlocs[no_bloc-1].ech.strIdMasque = (ligneForm.split('=')[1])

            # note d'acquisition dans sep
            if ('note=' in ligne) or ('note =' in ligne):
                tempo = (ligne.split('=')[1]).rstrip('\n')
                obs.lstBlocs[no_bloc-1].ech.note = tempo

            # id_filtre
            ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
            if 'filtre=' in ligneForm:
                obs.lstBlocs[no_bloc-1].ech.strIdFiltre = (ligneForm.split('=')[1])

            # 'map' mise au point
            ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
            if 'map=' in ligneForm:
                try:
                    obs.lstBlocs[no_bloc-1].ech.map = int((ligneForm.split('=')[1]))
                except ValueError:
                    print('N{0}, b{1} ech : map doit être int!'.format(obs.N, no_bloc.indexBloc))
                    sys.exit()

            # 'temp_to' température du to
            ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
            if 'temp_to=' in ligneForm:
                obs.lstBlocs[no_bloc-1].ech.temp_to = convertToFloat((ligneForm.split('=')[1]))

        if obs.tobs == 'complete':
            if typeMesure == 'sep':
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                # extraire le/les index de calibration
                if 'index_cal_e=' in ligneForm:
                    tempo = ligneForm.split('=')[1]
                    if tempo != '':
                        obs.lstBlocs[no_bloc-1].reduc.lstIndexCalE = tempo.split(',')
                    else:
                        print("N{0}, b{1}, sep : index_cal_e est absent!".format(obs.N, no_bloc))
                        print("Exécutez sessions.hier() pour diagnostic.")
                        sys.exit()

                # 'map' mise au point
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'map=' in ligneForm:
                    try:
                        obs.lstBlocs[no_bloc-1].sep.map = int((ligneForm.split('=')[1]))
                    except ValueError:
                        print('N{0}, b{1} sep : map doit être int!'.format(obs.N, no_bloc.indexBloc))
                        sys.exit()

                # 'temp_to' température du to
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'temp_to=' in ligneForm:
                    obs.lstBlocs[no_bloc-1].sep.temp_to = convertToFloat((ligneForm.split('=')[1]))

                # 'transp' transparance
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'transp=' in ligneForm:
                    obs.lstBlocs[no_bloc-1].sep.transp = convertToFloat((ligneForm.split('=')[1]))

                # 'humid'
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'humid=' in ligneForm:
                    obs.lstBlocs[no_bloc-1].sep.humid = convertToFloat((ligneForm.split('=')[1]))

                # 'press_bar' pression barométrique
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'press_bar=' in ligneForm:
                    obs.lstBlocs[no_bloc-1].sep.press_bar = convertToFloat((ligneForm.split('=')[1]))

                # seeing
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'seeing=' in ligneForm:
                    obs.lstBlocs[no_bloc-1].sep.seeing = (ligneForm.split('=')[1])

                # id_filtre
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'filtre=' in ligneForm:
                    obs.lstBlocs[no_bloc-1].sep.strIdFiltre = (ligneForm.split('=')[1])

            if typeMesure == 'pos':
                ligneForm = ligne.replace(' ', '').rstrip('\n')
                # le log d'environnement de pos contient l'évaluation du quadrant de pos
                if 'eval_quadrant=' in ligneForm.lower():
                    obs.lstBlocs[no_bloc-1].pos.eval_Q = (ligneForm.split('=')[1]).upper()

                # 'map' mise au point
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'map=' in ligneForm:
                    try:
                        obs.lstBlocs[no_bloc-1].pos.map = int((ligneForm.split('=')[1]))
                    except ValueError:
                        print('N{0}, b{1} pos : map doit être int!'.format(obs.N, no_bloc.indexBloc))
                        sys.exit()

                # 'temp_to' température du to
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'temp_to=' in ligneForm:
                    obs.lstBlocs[no_bloc-1].pos.temp_to = convertToFloat((ligneForm.split('=')[1]))

                # 'transp' transparance
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'transp=' in ligneForm:
                    obs.lstBlocs[no_bloc-1].pos.transp = convertToFloat((ligneForm.split('=')[1]))

                # 'humid'
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'humid=' in ligneForm:
                    obs.lstBlocs[no_bloc-1].pos.humid = convertToFloat((ligneForm.split('=')[1]))

                # 'press_bar' pression barométrique
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'press_bar=' in ligneForm:
                    obs.lstBlocs[no_bloc-1].pos.press_bar = convertToFloat((ligneForm.split('=')[1]))

                # seeing
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'seeing=' in ligneForm:
                    obs.lstBlocs[no_bloc-1].pos.seeing = (ligneForm.split('=')[1])

                # id_filtre
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'filtre=' in ligneForm:
                    obs.lstBlocs[no_bloc-1].pos.strIdFiltre = (ligneForm.split('=')[1])
                
            # note d'environnement sep | pos
            if ('note=' in ligne) or ('note =' in ligne):
                tempo = (ligne.split('=')[1]).rstrip('\n')
                if typeMesure == 'sep':
                    obs.lstBlocs[no_bloc-1].sep.note = tempo
                if typeMesure == 'pos':
                    obs.lstBlocs[no_bloc-1].pos.note = tempo

            # remarques d'environnement sep | pos
            if ('remarques=' in ligne) or ('remarques =' in ligne):
                tempo = (ligne.split('=')[1]).rstrip('\n')
                if typeMesure == 'sep':
                    obs.lstBlocs[no_bloc-1].sep.remarques = tempo
                if typeMesure == 'pos':
                    obs.lstBlocs[no_bloc-1].pos.remarques = tempo
    
    ###########################################################
    # extraction des données dans le log d'acquisition
    ###########################################################
    #  fla = nom complet fichier log acquisition (FC)

    if obs.tobs == 'ech':
        # no_bloc == 0 toujours
        fla = obs.lstBlocs[0].ech.ncfla
        with open(fla) as f:
            lignesLues = f.readlines()
        f.close()

        for ligne in lignesLues:
            # date UTC d'acquisition (en assumant que PC d'acquisition réglé sur UTC)
            if 'Date=' in ligne:
                obs.lstBlocs[0].ech.date_utc_acq = (ligne.split('=')[1]).rstrip('\n')
        
            # heure UTC d'acquisition
            if 'Mid(UT)=' in ligne:
                obs.lstBlocs[0].ech.heure_utc_acq = (ligne.split('=')[1]).rstrip('\n')

            # nombre d'images acquises
            if 'Limit=' in ligne:
                tempo = (ligne.split('=')[1]).rstrip('\n')
                if 'Frames' in tempo:
                    obs.lstBlocs[0].ech.nbr_images_acq = tempo.split(' ')[0]
                elif 'Seconds' in tempo:
                    obs.lstBlocs[0].ech.nbr_images_acq = 'interval de ' + tempo.split(' ')[0] + ' s'


    if obs.tobs == 'complete':
        b = no_bloc - 1
        if typeMesure == 'pos':
            fla = obs.lstBlocs[b].pos.ncfla
            with open(fla) as f:
                lignesLues = f.readlines()
            f.close()

            for ligne in lignesLues:
                # date UTC d'acquisition (en assumant que PC d'acquisition réglé sur UTC)
                if 'Date=' in ligne:
                    obs.lstBlocs[b].pos.date_utc_acq = (ligne.split('=')[1]).rstrip('\n')
            
                # heure UTC d'acquisition
                if 'Mid(UT)=' in ligne:
                    obs.lstBlocs[b].pos.heure_utc_acq = (ligne.split('=')[1]).rstrip('\n')
        
                # nombre d'images acquises
                if 'Limit=' in ligne:
                    tempo = (ligne.split('=')[1]).rstrip('\n')
                    if 'Frames' in tempo:
                        obs.lstBlocs[b].pos.nbr_images_acq = tempo.split(' ')[0]
                    elif 'Seconds' in tempo:
                        obs.lstBlocs[b].pos.nbr_images_acq = 'interval de ' + tempo.split(' ')[0] + ' s'

        if typeMesure == 'sep':
            fla = obs.lstBlocs[b].sep.ncfla
            with open(fla) as f:
                lignesLues = f.readlines()
            f.close()
    
            for ligne in lignesLues:
                # date UTC d'acquisition (en assumant que PC d'acquisition réglé sur UTC)
                if 'Date=' in ligne:
                    obs.lstBlocs[b].sep.date_utc_acq = (ligne.split('=')[1]).rstrip('\n')
            
                # heure UTC d'acquisition
                if 'Mid(UT)=' in ligne:
                    obs.lstBlocs[b].sep.heure_utc_acq = (ligne.split('=')[1]).rstrip('\n')
        
                # nombre d'images acquises
                if 'Limit=' in ligne:
                    tempo = (ligne.split('=')[1]).rstrip('\n')
                    if 'Frames' in tempo:
                        obs.lstBlocs[b].sep.nbr_images_acq = tempo.split(' ')[0]
                    elif 'Seconds' in tempo:
                        obs.lstBlocs[b].sep.nbr_images_acq = 'interval de ' + tempo.split(' ')[0] + ' s'

    ###################################################################################
    # VALIDATIONS
    # vérifier si toutes les variables communes «importantes» contiennent des données
    ###################################################################################

    # s'il s'agit d'une réduction d'échelle
    #  rechercher les informations de id_masque dans master_masques_cal_df
    if obs.tobs == 'ech':
        global info_filtre_df, info_masque_df

        #info_masque_df = master_masques_cal_df.loc[master_masques_cal_df.id_masque==id_masque]
        info_masque_df = master_masques_cal_df.loc[master_masques_cal_df.id_masque==\
                                                   obs.lstBlocs[0].ech.strIdMasque]
        assert info_masque_df.index.size == 1, "Erreur, zéro ou plus d'une occurence de " + \
            obs.lstBlocs[0].ech.strIdMasque + ' dans master_masques_cal.csv'
    
        # rechercher les informations de id_filtre dans master_filtres_cal_df
        info_filtre_df = master_filtres_cal_df.loc[master_filtres_cal_df.id_filtre==\
                                                   obs.lstBlocs[0].ech.strIdFiltre]
        
        # placer LfplusDf, LfplusDf_sigma, Lo et Lo_sigma dans reduc
        obs.lstBlocs[0].reduc.LfplusDf = info_masque_df.loc[0, 'LfplusDf']
        obs.lstBlocs[0].reduc.LfplusDf_sigma = info_masque_df.loc[0, 'LfplusDf_sigma']
        obs.lstBlocs[0].reduc.Lo = info_filtre_df.loc[0,'Lo']
        obs.lstBlocs[0].reduc.Lo_sigma = info_filtre_df.loc[0,'Lo_sigma']
        
        assert info_filtre_df.index.size == 1, "ech : Erreur, zéro ou plus d'une occurence de " + \
            obs.lstBlocs[0].ech.strIdFiltre + ' dans master_filtre_cal.csv'
        assert obs.lstBlocs[0].ech.temp_to != None, 'environnement ech temp_to requis'
        assert obs.lstBlocs[0].ech.map != 0, 'environnement ech map requise!'

        # validation date et heure d'acquisition UTC
        d = obs.lstBlocs[0].ech.date_utc_acq
        h = obs.lstBlocs[0].ech.heure_utc_acq
        assert d != '', 'acq ech date_utc_acq requise'
        assert h != '', 'acq ech heure_utc_acq requise'

        # inscrire dt utc iso observation dans ...ech.dtime_utc_acq
        obs.lstBlocs[0].ech.dtime_utc_acq = str_dt_isot_a_TimeIsot(date=d, heure=h)
        assert obs.lstBlocs[0].ech.nbr_images_acq != 0,\
            'acq ech nombre images ou secondes acquises requis'

    if obs.tobs == 'complete':
        b = no_bloc - 1
        if typeMesure == 'sep':
            assert obs.lstBlocs[b].sep.temp_to != None, 'environnement sep temp_to requis'
            assert obs.lstBlocs[b].sep.map != 0, 'environnement sep map requise!'

            # validation date et heure d'acquisition UTC
            d = obs.lstBlocs[b].sep.date_utc_acq
            h = obs.lstBlocs[b].sep.heure_utc_acq
            assert d != '', 'acq sep date_utc_acq requise'
            assert h != '', 'acq sep heure_utc_acq requise'
            
            # inscrire dt utc iso observation dans ...ech.dtime_utc_acq
            obs.lstBlocs[b].sep.dtime_utc_acq = str_dt_isot_a_TimeIsot(date=d, heure=h)

            assert obs.lstBlocs[b].sep.nbr_images_acq != 0, 'acq sep nombre images ou secondes acquises requis'
        
            # vérifier qu'il y a au moins un index de calibration d'échelle
            assert len(obs.lstBlocs[b].reduc.lstIndexCalE) !=0,\
                "Le fichier «" + obs.lstBlocs[b].sep.ncfle +\
                    "» ne contient pas d'index de calibration d'échelle!"

        if typeMesure == 'pos':
            assert obs.lstBlocs[b].pos.temp_to != None, 'N{0}, b{1} pos : environnement pos temp_to requis'.format(obs.N, b)
            assert obs.lstBlocs[b].pos.map != 0, 'N{0}, b{1} pos : environnement pos map requise!'.format(obs.N, b)

            # validation date et heure d'acquisition UTC
            d = obs.lstBlocs[b].pos.date_utc_acq
            h = obs.lstBlocs[b].pos.heure_utc_acq
            assert  d != '', 'N{0}, b{1} pos : acq pos date_utc_acq requise'.format(obs.N, b)
            assert h != '', 'N{0}, b{1} pos : acq pos heure_utc_acq requise'.format(obs.N, b)
            # inscrire dt utc iso observation dans ...ech.dtime_utc_acq
            obs.lstBlocs[b].pos.dtime_utc_acq = str_dt_isot_a_TimeIsot(date=d, heure=h)

            assert obs.lstBlocs[b].pos.nbr_images_acq != 0,\
                'N{0}, b{1} pos : acq pos nombre images ou secondes acquises requis'.format(obs.N, b)
            assert obs.lstBlocs[b].pos.eval_Q != '',\
                "N{0}, b{1} pos : environnement pos valeur de eval_Q requise!".format(obs.N, b)
    

def extraire_mesure_brutes_logReduc(obs, noBloc, typeMesure):
    """
    Pour le bloc courant, repère le fichier Rlog*.txt produit par reduc et
    écrit les mesures brutes de la réduction dans un nouveau fichier csv.

    Les données sont colligées dans les objets Reduction appropriés de l'objet
    Observation (obs) passé en paramètre.
    
    Note : dans le cas d'une réduction d'échelle ('ech') les paramètres sont
    toujours «objet obs», 1, 1.

    Paramètres positionnels :
     obs        -- objet Observation
     noBloc     -- int no du bloc traité
     typeMesure -- String 'pos' ou 'sep'
    """
    
    ############################################################################
    # préparation du patron RE pour la recherche des nombres en point flottant
    # compilation par re
    str_patron_nombres = r'[0-9.]+'
    pn = re.compile(str_patron_nombres)

    # lecture du fichier log de REDUC approprié pour le type d'observation et mesure
    if (obs.tobs == 'ech') or (obs.tobs == 'complete' and typeMesure == 'sep'):
        ncflr = obs.lstBlocs[noBloc-1].reduc.ncflr_sep
    else:
        ncflr = obs.lstBlocs[noBloc-1].reduc.ncflr_pos

    with open(ncflr) as f:
        lignesLues = f.readlines()
    f.close()
        
    nbrLignes_totales = len(lignesLues)
    
    nligne = 0
    # no de la première ligne de mesures brutes à extraire
    nligne_depart_data = 0

    for ligne in lignesLues:
        if obs.tobs == 'complete' and typeMesure == 'sep':
            # bien que la réduction est pour sep, en réalité theta (pos) se trouve dans le RLog de sep
            # au lieu de celui de pos
            if 'theta =' in ligne:
                #récupérer theta et theta_sigma (p. e. theta =   108.9  (sigma:0.06  Med:108.9))
                tempo = ligne.split('=')[1]
                strTousLesNombres = pn.findall(tempo)
                
                
                obs.lstBlocs[noBloc-1].reduc.theta = convertToFloat(strTousLesNombres[0])
                obs.lstBlocs[noBloc-1].reduc.theta_sigma = convertToFloat(strTousLesNombres[1])

            # récupérer également Delta Matrix pour comparer éventuellement avec celui de pos correspondant
            if 'Delta Matrix :' in ligne:
                obs.lstBlocs[noBloc-1].reduc.delta_matrix_sep =\
                    convertToFloat((ligne.split(':')[1].strip(' ')).rstrip('\n'))

        if obs.tobs == 'complete' and typeMesure == 'pos':
            # juste récupérer delta matrice pour comparer avec celle qu'on trouverra
            # dans le log d'acquisition de sep corresponant au même bloc
            if 'Delta Matrix :' in ligne:
                obs.lstBlocs[noBloc-1].reduc.delta_matrix_pos =\
                    convertToFloat((ligne.split(':')[1].strip(' ')).rstrip('\n'))

        # trouver le no de lignes de la chaîne 'Raw Data' dans lignesLues
        if obs.tobs == 'ech' or (obs.tobs == 'complete' and typeMesure == 'sep'):
            if 'Raw Data' in ligne:
                # les données commencent trois lignes plus bas
                nligne_depart_data = nligne + 3
                break
        nligne += 1
    
    # extraction des données brutes de séparation en px à partir de nligne_depart_data
    if typeMesure == 'sep':
        # nligne_depart_data
        # liste servant de tampon de ligne pour les lignes qui iront dans reduc_brut.csv
        reduc_brut_lst = []
        for li in range(nligne_depart_data, nbrLignes_totales):
            # recherche des nombres présent dans ligne courante
            strTousLesNombres = pn.findall(lignesLues[li])
    
            # placer match 0, 1, 3 et 4 correspondants à xA, yA, xB, yB dans tampon de ligne
            reduc_brut_lst += {strTousLesNombres[0] + ', ' + strTousLesNombres[1] + ', ' + strTousLesNombres[3] + ', '\
                                  + strTousLesNombres[4]}
    
        # écrire le tampon de lignes dans reduc_brut.csv
        entete_csv = 'xA,yA,xB,yB'
        with open(path.dirname(ncflr) + '/' + fich_mesures_brutes, 'w') as f:
            # écrire l'en-tête
            f.write(entete_csv + NL)
    
            # écrire les valeurs
            for line in reduc_brut_lst:
                for val in line:
                    f.write(val)
                f.write(NL)
        f.close()
    

def maj_master_calibrations(data):
    """
    Met à jour l'enregistrement lié à l'index de calibration présent dans data
    passé en paramètre dans le fichier maître des calibrations «master_calibrations_e.csv».
        
    Il ne peut exister qu'un seul enregistrement lié à l'index de calibration
    dans le fichier «master_calibrations_e.csv». Si l'index de calibration
    courant existe déjà dans «master_calibrations_e.csv», alors on assume
    que l'usager désire effectuer une nouvelle réduction avec un nouveau jeu
    de données produit par REDUC. 
    
    Dans ce cas, il faut présenter l'usager avec les résultats de la présente
    réduction en même temps que celle trouvée dans «master_calibrations_e.csv»
    pour le même index de calibration. L'usager devra alors décider laquelle
    des deux réductions il désire conserver.

    Paramètre positionnel
     data -- objet AcquisitionEchelle
    """
    
    # vérifier si index_cal_e existe dans master_calibrations_e_df
    # si c'est le cas, demander à l'us de remplacer ou annuler
    
    # trouver le nombre d'occurences de index_cal_e dans master_calibrations_e_df et agir en conséquence
    df = master_calibrations_e_df.loc[master_calibrations_e_df.index_cal_e==\
                                      data.lstBlocs[0].reduc.lstIndexCalE[0]]
    
    # préparer le nouvel enregistrement de master_calibrations_cal_df dans une liste
    enr_lst = [data.lstBlocs[0].reduc.lstIndexCalE[0],\
               data.lstBlocs[0].ech.dtime_utc_acq.value,\
               data.lstBlocs[0].ech.temp_to,\
               data.lstBlocs[0].ech.map,\
               data.lstBlocs[0].reduc.E,\
               data.lstBlocs[0].reduc.E_sigma, 'f',\
               data.lstBlocs[0].ech.strIdMasque,\
               data.lstBlocs[0].ech.strIdFiltre,\
               data.lstBlocs[0].ech.note\
              ]

    if df.index.size == 0:
        # ok pas d'occurence on demande si on écrit les infos
        print(enr_lst)
        tempo = data.lstBlocs[0].reduc.lstIndexCalE[0].split('\\')
        
        reponse = input('... Inscrire données précédentes de {0} dans {1} (o|n)? '\
                        .format(data.lstBlocs[0].reduc.lstIndexCalE[0],\
                        tempo[len(tempo)-1])).upper()

        if reponse.upper() == 'O':
            master_calibrations_e_df.loc[master_calibrations_e_df.index.size+1] = enr_lst
            # trier le df sur index_cal_e
            master_calibrations_e_df.sort_values(by='index_cal_e', ignore_index=True, inplace=True)

            # liste le df résultant
            print(master_calibrations_e_df)
            
            # exportation dans nom_complet_fich_maitre_cal
            master_calibrations_e_df.to_csv(nom_complet_fich_maitre_cal, index=False)
            print("Écriture de {0} terminée!".format(nom_complet_fich_maitre_cal))
        else:
            print(NL + 'Données non inscrites!')

    elif df.index.size == 1:
        # d'abord transformer df en une chaîne simillaire à enr
        df_en_str =  df.loc[df.index, 'index_cal_e'].item() + ', '
        df_en_str += df.loc[df.index, 'dt_obs_utc'].item() + ', '
        df_en_str += str(df.loc[df.index, 'temp_to'].item()) + ', '
        df_en_str += str(df.loc[df.index, 'map'].item()) + ', '
        df_en_str += str(df.loc[df.index, 'E'].item()) + ', '
        df_en_str += str(df.loc[df.index, 'E_sigma'].item()) + ', '
        df_en_str += df.loc[df.index, 'type_cal'].item() + ', '
        df_en_str += df.loc[df.index, 'id_masque'].item() + ', '
        df_en_str += df.loc[df.index, 'id_filtre'].item() + ', '
        df_en_str += df.loc[df.index, 'note'].item()


        # on doit présenter le résultat et demander si on écrase ou si on annule
        print('\n Réduction terminée')
        print('A : trouvé dans master_calibrations_e.csv,')
        print('B : présente réduction :\n')
        
        # préparer la liste des noms des colonnes (pour affichage seulement)
        c_lst = ''
        for nc in df.columns:
            c_lst += nc + ', '
        print('      ' + c_lst.rstrip(', '))
        print('A : ' + df_en_str)
        print('B : {0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}, {9}\n'.format(*enr_lst))
        
        print('Garder A (a), ')
        print('Garder B (b), ')
        print('Annuler  (x), ')
        reponse = input('? (a|b|x) : ').upper()
        
        if reponse == 'A':
            print('garder A :: fichier non modifié.\nFin du programme.')
            tampon = "aucun changement p/r à la réduction précédente"
            inscrire_dans_log(tampon)
            
        elif reponse == 'B':
            # on enlève df de master_calibrations_e_df et on ajoute enr_lst
            print('garder B')
            idx_a_enlever = df.index
            master_calibrations_e_df.drop(idx_a_enlever, inplace=True)
            master_calibrations_e_df.loc[master_calibrations_e_df.index.size+1] = enr_lst

            # trier le df sur index_cal_e
            master_calibrations_e_df.sort_values(by='index_cal_e', ignore_index=True, inplace=True)

            # liste le df résultant
            print(master_calibrations_e_df)
            
            # exportation dans nom_complet_fich_maitre_cal
            master_calibrations_e_df.to_csv(nom_complet_fich_maitre_cal, index=False)
            tampon = "Écriture de {0} terminée!".format(nom_complet_fich_maitre_cal)
            print(tampon)
            inscrire_dans_log(tampon)

        else:
            print("Annulé par l'usager. Au revoir!")
            tampon = "aucun changement p/r à la réduction précédente"
            inscrire_dans_log(tampon)


    # si plus d'une occurence, alors on arrête tout et on laisse l'us corriger la situation    
    else:
        tampon = "ERREUR, plus d'une occurence de " + data.lstBlocs[0].reduc.lstIndexCalE[0] +\
              " sortie du programme."
        print(tampon)
        inscrire_dans_log(tampon)
        tampon = "Veuillez corriger la situation dans master_calibrations_e.csv!"
        inscrire_dans_log(tampon)

    
def imprime_rapport_E(obs):
    """Imprime rapport. """
    
    print("  RÉDUCTION POUR CALIBRATION D'ÉCHELLE")
    #l = len('Index de calibration : {0}\n'.format(index_cal_e))
    l = len('Index de calibration : {0}\n'.format(obs.lstBlocs[0].reduc.lstIndexCalE[0]))
    print('#' * (l+3))
    print('# Index de calibration : {0} #'.format(obs.lstBlocs[0].reduc.lstIndexCalE[0]))
    print('#' * (l+3))
    print(NL)

    l = 50
    print('COORDONNÉES DES CENTROÏDES ET DISTANCES (px)'.center(l))
    print('-' * l)
    print(obs.lstBlocs[0].reduc.reduc_brute_df)
    
    l = 37
    print(NL * 2)
    print('STATISTIQUES DESCRIPTIVES'.center(l))
    print('-' * l)
    print('                dist_min : {0:>7.3f} px'.format(obs.lstBlocs[0].reduc.dist_min))
    print('                dist_max : {0:>7.3f} px'.format(obs.lstBlocs[0].reduc.dist_max))
    print('                dist_moy : {0:>7.3f} px'.format(obs.lstBlocs[0].reduc.dist_moy))
    print('              écart type : {0:>7.3f} px'.format(obs.lstBlocs[0].reduc.dist_sigma))
    print("nombre d'images retenues : {0:>2d} sur {1:s}\n".format(obs.lstBlocs[0].reduc.n_data,\
                                                                  obs.lstBlocs[0].ech.nbr_images_acq))
    
    print('E = {0:>4.4f} "/pix ± {1:>4.4f} "/pix'.format(obs.lstBlocs[0].reduc.E, obs.lstBlocs[0].reduc.E_sigma))

    
def diff_dt(dt1, dt2):
    """
    Retourne un objet astropy.time.TimeDelta de la différence absolue
    (intervalle) entre dt1 et dt2 en J.jj.

    Paramètres positionnels :
     dt1 -- objet astropy.time.core.Time dt1, la première date
     dt2 -- objet astropy.time.core.Time dt2, la seconde date
     
     où;
     
     dt1 -- String première date au format isot, ex. '2022-02-07T12:35:45.235'
     dt2 -- String seconde date au format isot, ex. '2022-02-07T12:35:45.235'
    """
    if type(dt2) == str and type(dt1) == str:
        return abs(str_dt_isot_a_TimeIsot(dt=dt2) - str_dt_isot_a_TimeIsot(dt=dt1))
    else:
        return abs(dt2 - dt1)


def str_dh_a_str_isot(d, h):
    """
    Retourne une chaîne Time au format isot de astropy avec d et h, p. ex.
    «2021-10-08T22:22:31.258». Toutes les dates en UTC.

    Paramètres positionnels :
     d -- String date au format yyyymmdd, ex. 20220207
     h -- String h heure au format hhmmss.sss, ex. 222855.248
    """

    assert d.isdigit(), 'seulement des car chiffres dans la date'
    if '.' in h:
        tempo = h.split('.')
        assert tempo[0].isdigit() and tempo[1].isdigit(), "seulement des car chiffres dans l'heure"
    else:
        assert h.isdigit(), "seulement des car chiffres dans l'heure"
    
    return d[0:4] + '-' + d[4:6] + '-' + d[6:8] +\
        'T' + h[0:2] + ':' + h[2:4] + ':' + h[4:]


def str_dt_isot_a_TimeIsot(date='', heure='', dt=None):
    """
    Convertit date et heure UTC au format Time isot UTC et retourne un objet
    astropy.time.core.Time.

    Paramètres Keyword :
     date -- String date au format 'aaaammjj' (par défaut '')
     heure -- String heure au format 'hhmmss.sss' (par défaut '')
     dt -- String dt isot (par défaut None)
    """

    if dt == None:
        return Time(str_dh_a_str_isot(date, heure), format=t_format, scale=t_scale)
    else:
        return Time(dt, format=t_format, scale=t_scale)



def UTCaHeureLocale(dhl):
    """
    Retourne la représentation datetime UTC aware de String dhl.

    Paramètre positionnel :
     dhl -- String date au format iso par ex. '2020-11-08T23:48:00UTC-4'
    """
    
    decallageUTCdhl = dhl.rsplit('UTC')[1]
    if decallageUTCdhl == '':
        decallageUTCdhl = 0
    else:
        decallageUTCdhl = int(decallageUTCdhl)
    
    utc_dhl = TimezoneInfo(utc_offset=decallageUTCdhl*u.hour)
    ### enlever le UTC de la date
    tempo = dhl.split('U')[0]

    ### convertir la date et heure en int (en utilisant list comprehension)
    lst_int_dhl = [int(i) for i in tempo.split('T')[0].split('-')]
    lst_int_heure_dhl = [i for i in tempo.split('T')[1].split(':')]
    a = lst_int_dhl[0]
    m = lst_int_dhl[1]
    j = lst_int_dhl[2]
    h = int(lst_int_heure_dhl[0])
    mi = int(lst_int_heure_dhl[1])
    # secondes et microsecondes ms
    s = int(lst_int_heure_dhl[2].split('.')[0])
    ms = int(lst_int_heure_dhl[2].split('.')[1])
    
    ### créer un datetime qui contient l'information de fuseau horaire
    # datetime(year, month, day[, hour[, minute[, second[, microsecond[,tzinfo]]]]])
    return datetime(a, m, j, h, mi, s, ms, tzinfo=utc_dhl)

def lire_fichier_observatoires():
    boolResultatOK = True
    try:
        observatoires_df =  pd.read_csv('D:/DOCUMENTS/Astronomie/dev/astrodm/observatoires.csv')
    except FileNotFoundError:
        tampon = 'doubleOutils.lire_fichier_observatoires :: fichier observatoires.csv non trouvé.'
        inscrire_dans_log(tampon)
        boolResultatOK = False
    return boolResultatOK



def lire_fichiers_support(typeObservation, chemin_prog):
    """
    Lecture des fichiers maîtres de calibration,
    lecture fichiers filtres et masques si typeObservation 'ech',
    lecture fichier des observatoires
    
    retourne False
    
    Paramètres positionnels :
     typeObservation -- String type observation :
         'ech' échelle
         'complete' complète
     chemin_prog -- String chemin du programme
    """

    global master_calibrations_e_df, master_filtres_cal_df, master_masques_cal_df

    global nom_complet_fich_maitre_cal
    global ch_rep_cal
    
    # pour le résultat et le log
    global boolResultatOK
    boolResultatOK = True
    
    # localisation des fichiers de supports
    if typeObservation == 'complete':
        ch_rep_cal = path.dirname(path.dirname(path.dirname(chemin_prog))) + '/cal_e/'
    else:
        ch_rep_cal = path.dirname(chemin_prog) + '/'
        
    
    # lire le fichier maître des calibrations
    nom_complet_fich_maitre_cal = ch_rep_cal + nom_fich_m_cal
    try:
        master_calibrations_e_df = pd.read_csv(nom_complet_fich_maitre_cal)
        # faire une copie dans nom_complet_fich_maitre_cal + '.bak'
        master_calibrations_e_df.to_csv(nom_complet_fich_maitre_cal + '.bak', index=False)
        
    except FileNotFoundError:
        tampon = 'doubleoutils.lire_fichiers_support :: fichier {0} NON trouvé.'.format(nom_complet_fich_maitre_cal)
        inscrire_dans_log(lstLog=lst_log_post_reduction, strInscription=tampon)
        boolResultatOK = False
    
    if typeObservation == 'ech':
        # lire les deux fichiers master filtres et masques dans des df
        fich_mfiltres = ch_rep_cal + nom_fich_m_filtres
        fich_mmasques = ch_rep_cal + nom_fich_m_masques

        try:
            master_filtres_cal_df = pd.read_csv(fich_mfiltres)
            
        except FileNotFoundError:
            tampon = 'doubleoutils.lire_fichiers_support :: Fichier {0} NON trouvé.'.format(fich_mfiltres)
            inscrire_dans_log(lstLog=lst_log_post_reduction, strInscription=tampon)
            boolResultatOK = False
            

        try:
            master_masques_cal_df = pd.read_csv(fich_mmasques)
            
        except FileNotFoundError:
            tampon = 'doubleoutils.lire_fichiers_support :: Fichier {0} NON trouvé.'.format(fich_mmasques)
            inscrire_dans_log(lstLog=lst_log_post_reduction, strInscription=tampon)
            boolResultatOK = False

    return boolResultatOK


def valide_nom_systeme(chaine):
    """
    Valide silencieusement si chaine est un nom de système et existe bien dans
    le WDS et retourne tupple True | False et résultats de la recherche WDS | None.

    Paramètre positionnel :
     chaine -- String chaine à valider.
    """

    if len(chaine) > 7:
        return False, None

    # recherche du discoverer
    str_re_pat = r'^[a-z]+'
    obj_pat = re.compile(str_re_pat)
    obj_match = obj_pat.match(chaine)
    
    str_id_disc = obj_match.group(0)
    if str_id_disc == '' or len(str_id_disc) > 4:
        return False, None

    #print("str_id_disc= '" + str_id_disc + "'")

    # recherche du no de système
    str_re_pat = r'[0-9*]+'
    obj_pat = re.compile(str_re_pat)
    
    obj_match = obj_pat.search(chaine)
    str_no_sys = obj_match.group(0)
    if str_no_sys == '' or len(str_no_sys) > 5:
        return False, None

    # valide si le système existe dans le WDS
    result_rech_WDS = rech_wds(chaine, '*')
    if len(result_rech_WDS) != 0:
        return True, result_rech_WDS
    else:
        return False, None


def norm_WDS_src(source):
    """
    Retourne un String avec nom de la source normalisée au normes WDS,
    c.-à-d. avec un seul espace entre découvreur (3 ou 4 lettres) et
    no (1 à 4 chiffres) ssi len(source) < 7.

    Paramètre positionnel :
     source -- String La désignation de découvreur du système recherché.
    """

    src = source.upper()
    #print("src= '" + src + "'")

    # RE écrite dans un raw string pour éviter '\' --> '\\'
    # recherche du discoverer
    str_re_pat = r'[A-Z]+'
    obj_pat = re.compile(str_re_pat)
    obj_match = obj_pat.match(src)
    str_id_disc = obj_match.group(0)

    #print("str_id_disc= '" + str_id_disc + "'")

    # recherche du no de système
    str_re_pat = r'[0-9*]+'
    obj_pat = re.compile(str_re_pat)
    obj_match = obj_pat.search(src)

    try:
        str_no_sys = obj_match.group(0)
        #print("str_no_sys= '" + str_no_sys + "'")

    except AttributeError:
        print('no match pour no système')


    # normalisation avec WDS_SRC_ESPACE_LEN espace(s) entre les deux
    # si < 7
    if len(str_id_disc) + len(str_no_sys) < 7:
        return(str_id_disc + ' ' * WDS_SRC_ESPACE_LEN + str_no_sys)
    else:
        return(str_id_disc + str_no_sys)


def norm_WDS_src_notes(source):
    """
    Normalise source sur 7 caractères.

    Paramètres
    ----------
    source : TYPE String
        La désignation de découvreur du système recherché.

    Retourne
    --------
    String désignation normalisée sur WDS_SRC_LEN_NOTES.

    """

    src = source.upper()
    #print("src= '" + src + "'")

    # RE écrite dans un raw string pour éviter '\' --> '\\'
    # recherche du discoverer
    str_re_pat = r'[A-Z]+'
    obj_pat = re.compile(str_re_pat)
    obj_match = obj_pat.match(src)
    str_id_disc = obj_match.group(0)

    #print("str_id_disc= '" + str_id_disc + "'")

    # recherche du no de système
    str_re_pat = r'[0-9]+'
    obj_pat = re.compile(str_re_pat)
    obj_match = obj_pat.search(src)

    try:
        str_no_sys = obj_match.group(0)
        #print("str_no_sys= '" + str_no_sys + "'")

    except AttributeError:
        print('no match pour no système')


    # normalisation sur 7 car

    nbr_espaces = WDS_SRC_LEN_NOTES - len(str_id_disc) - len(str_no_sys)
    #print('nbr_espaces= ', nbr_espaces)

    return(str_id_disc + ' ' * nbr_espaces + str_no_sys)

def rech_wds(src, paire):
    """Recherche les informations de src et paire au catalogue WDS ('B/wds/wds').

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

    """
    
    # formater pour recherche WDS
    # si nécessaire, remplacer 4e car par '?', p. e. «stfa 60» devient «stf? 60»
    
    viz.CACHE = False
    viz.ROW_LIMIT = 120000 # au cas où ?
    global strSource_format_pour_Notes
    # normaliser pour recherche WDS
    strSource = norm_WDS_src(src)
    
    # le cas échéant, remplacer 4e car alpha par '?'
    # split sur ' ' puisque strSource est normalisé avec un espace
    spl = strSource.split(' ')
    if len(spl[0]) == 4:
        strSource = spl[0][:3] + '? ' + spl[1]
    
    ### soumettre la requête
    #strSource = 'H 3*'
    return viz.query_constraints(catalog='B/wds/wds', Disc=strSource, Comp=paire)

    # variations avec critère Obs2
    #result = viz.query_constraints(catalog='B/wds/wds', Disc=source, Comp=paire, Obs2='<=2015')
    ##result = viz.query_constraints(catalog='B/wds/wds', Disc=source, Comp=paire, Obs2='2011..2015')
    

def rech_wds_notes(src):
    """
    Recherche les notes au sujet de src dans les notes au WDS ('B/wds/notes'), si présentes.

    Parameters
    ----------
    src : TYPE str
        La désignation de découvreur du système recherché.

    Returns
    -------
    TYPE astroquery.utils.commons.TableList
        Il s'agit d'une table des résultats.

    """
    ### obtenir WDS Notes
    # il faut normaliser strSource sur 7 car pour la recherche dans les notes
    # du WDS
    nom_src_format_pour_notes = norm_WDS_src_notes(src)

    notes_q = viz.query_constraints(catalog='B/wds/notes', Disc=nom_src_format_pour_notes)
    #wds_notes
    if notes_q != []:
        # garder seulement les deux dernières colonnes
        notes_q[0].keep_columns(['Text', 'RefCode'])
    return notes_q
        
def info_src_wds(src, paire, notes=True):
    """
    Recherche et imprime les résultats de recherche dans le catalogue WDS.
    
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

    """
    strSource = norm_WDS_src(src.upper())
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
    """
    Règles environement des variables bool pour exécution.

    Parameters
    ----------
    modei : TYPE, optional
        DESCRIPTION. mode interactif The default is False.
    impre : TYPE, optional
        DESCRIPTION. The default is False.
    imprd : TYPE, optional
        DESCRIPTION. The default is False.
    imprs : TYPE, optional
        DESCRIPTION. The default is False.

    Returns
    -------
    None.

    """
    global bool_mode_interactif, bool_imprEn_tete, bool_imprDetails, bool_imprSommaire
    bool_mode_interactif = modei
    bool_imprEn_tete = impre
    bool_imprDetails = imprd
    bool_imprSommaire = imprs


# %% INITIALISATIONS
no_version = 41

'''
Crée un dictionnaire des codes de notes pour les
observations d'étoiles doubles

Format sur 3 caractères, par ex. 'C L'
Position 1 : code de suivi {X, E, C, P ou T}
Position 2 : libre pour développement futur
Position 3 : code de méthode de mesure {L ou I}
'''
# VALIDATIONS
# fonction de date et heure
# délai max entre deux acquisitions d'échelle (m)
MAX_DELAI_DEPUIS_ACQUISITIONS_ECHELLE = 120
# différence de température entre deux acquisitions (°C)
MAX_DELTA_TEMPERATURE = 5
# délais entre première et dernière observation (jours)
MAX_DELAI_ENTRE_OBSERVATIONS = 7

codes_etat_obs_dict = {
    '123': ['1:état, 2:explication, 3:méthode.'],
    'C..': ["En cours d'observation. Voir explication."],
    'P..': ['Programme en PLANIFICATION.'],
    'T..': ['Programme TERMINÉ, voir explication.'],
    '?..': ["Aucun programme d'observation assigné."],
    '..L': ['Méthode de mesure par Lucky Imaging.'],
    '..I': ['Méthode de mesure par interférométrie des tavelures.'],
    '.O.': ['OPTIMAL. Programme complété avec N>1.'],
    '.A.': ['ACCEPTABLE, mais programme terminé avec N=1 et délai > {0} j.'.format(MAX_DELAI_ENTRE_OBSERVATIONS)],
    '.X.': ['Données INUTILISABLES. Voir carnet Jupyter Lab du programme']
}

# pour rech WDS (source seulement) formater src avec un espace entre découvreur et no
# alors len(src) = max 7
WDS_SRC_ESPACE_LEN = 1

# normalisation des noms de sources WDS à 7 caractères
# longueur fixe du nom de la source pour recherche dans WDS Notes
# c.-à-d. len(découvreur + espaces + no ) == 7
WDS_SRC_LEN_NOTES = 7

# les fichiers maîtres calibration d'échelle, masques et filtres
# se trouvent toujours dans ../med/cal_e/ pr au répertoire du système
nom_fich_m_cal = 'master_calibrations_e.csv'
nom_fich_m_filtres = 'master_filtres_cal.csv'
nom_fich_m_masques = 'master_masques_cal.csv'

### pandas options d'affichage des tables
pd.set_option('display.expand_frame_repr', True)
pd.set_option('display.colheader_justify', 'right')
pd.set_option('display.max_colwidth', 50)
pd.set_option('display.max_column', 30)
pd.set_option('display.width', 140)
pd.set_option("precision", 4)

# time scale and format for astropy Time objects
t_scale = 'utc'
t_format = 'isot'

# divers
NL = '\n'
# nom du fichier des mesures brutes produit lors de la post-réduction
fich_mesures_brutes = 'mesures_brutes.csv'
lst_log_post_reduction = list()
observatoires_df = None
resultatOK = True

# for tkinter
root = Tk()
root.wm_attributes('-topmost', 1)
root.withdraw()

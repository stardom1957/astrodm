# -*- coding: utf-8 -*-
"""
@author: Dominique Martel

Comprend diverses fonctionnalités pour planifier, réduire les observations
à partir des données d'acquisition d'étoiles doubles et de pré-réduction
produites par le logiciel REDUC (de Florent Losse) et produit également
diverses listes. 

This research has made use of the VizieR catalogue access tool, CDS,
Strasbourg, France.  The original description of the VizieR service was
published in A&AS 143, 23
"""

# %% imports
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
from astroquery.vizier import Vizier as viz
import re
from os import path
from tkinter import Tk
import os
import glob
import pickle
from astropy.coordinates import SkyCoord
import hashlib

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

        # type de mesure
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
        self.nbr_images_acq = None

        # filtre
        self.strIdFiltre = ''

        # note
        self.note = ''
        
        # mise au point map
        self.map = 0
        
        # validité
        # True ssi ncfla et ncfle de sep et pos sont non None
        self.valide = True
        

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
        
        # valeur de la map de l'échelle utilisée dans la méthode calcule_sep
        # la valeur indiquée est toujours valide
        self.mapEchelle = 0

        # liste des index de calibration d'échelle
        self.lstIndexCalE = list()

        # Pandas dataframe de mesures brutes
        self.reduc_brute_df = ''
        
        #debug je ne sais pas si cela sera utile
        self.valide = True


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
            #debug print("relecture_mes_brutes::Relecture de ", ncfmb)
            self.reduc_brute_df = pd.read_csv(ncfmb)
        except FileNotFoundError:
            #debug
            print("relecture_mes_brutes::Relecture de ", ncfmb)
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
        
        # sep et sep_sigma
        self.sep, self.sep_sigma = 0, 0

        # pa et pa_sigma lus du log Reduc de sep
        self.pa,  self.pa_sigma = 0, 0

        # Delta Matrix sep et pos
        self.delta_matrix_sep, self.delta_matrix_pos = 0, 0


    def calcule_sep(self):
        '''
        À partir de reduc_brute_df calcule la distance entre chaque point et
        produit les statistiques descriptives des données.
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
            # debug df = df.append(master_calibrations_e_df.loc[master_calibrations_e_df.index_cal_e==idx_cal_e])
            tempo = master_calibrations_e_df.loc[master_calibrations_e_df.index_cal_e==idx_cal_e]
            df = pd.concat([df, tempo])

        
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
        
        # calcul sep et sep_sigma
        self.sep = self.E_moy * self.dist_moy
        
        # Propagation des incertitudes dans sep_sigma
        self.sep_sigma = abs(self.E_moy * self.dist_moy) *\
            math.sqrt(math.pow((self.E_moy_sigma/self.E_moy), 2) +\
                 math.pow((self.dist_sigma/self.dist_moy), 2)) 


#
# Classe Bloc
#
class Bloc:
    '''
    Un bloc d'observation est un constituant d'un objet Session.
    
    Si le type d'observation est 'complete', un bloc comprend un objet
    AcquisitionSeparation, un objet AcquisitionPosition et un objet
    ReductionComplete.
    
    Si le type d'observation est 'ech', un bloc comprend un objet
    AcquisitionEchelle et un objet ReductionEchelle.
    '''
    
    def __init__(self, noBloc, typeSession):
        self.no_bloc = noBloc
        self.typeSession = typeSession
        
        # indique que le bloc ne doit PAS faire l'objet d'une réduction
        self.valide = True

        if typeSession == 'complete':
            self.sep = AcquisitionSeparation('sep')
            self.pos = AcquisitionPosition('pos')
            self.reduc = ReductionComplete()

        if typeSession == 'ech':
            self.ech = AcquisitionEchelle('sep')
            self.reduc = ReductionEchelle()

    def validations(self, nsession):
        '''Valide le bloc d'observation.
        
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
        
        #######################################################################
        # Validation 1 - existence de l'index de calibration
        # Récupérer les données de tous les index de calibration indiqués
        # dans le bloc d'observation
        #

        # créer un df vide avec même structure que master_calibrations_e_df
        calibration_echelle_df = pd.DataFrame(data=None, index=None,\
                          columns=list(master_calibrations_e_df.keys()))

        # puis récupérer les informations de chaque index de calibration
        # présent dans self.reduc.lstIndexCalE dans un Pandas df
        for idx_cal_e in self.reduc.lstIndexCalE:
            #debug calibration_echelle_df = calibration_echelle_df.append(master_calibrations_e_df.loc[master_calibrations_e_df.index_cal_e==idx_cal_e])
            tempo = master_calibrations_e_df.loc[master_calibrations_e_df.index_cal_e==idx_cal_e]
            calibration_echelle_df = pd.concat([calibration_echelle_df, tempo])
                
        # si calibration_echelle_df est vide, alors c'est probablement parce que la valeur de
        # l'index ne se situe pas dans master_calibrations_e_df
        
        # fatal si index n'existe pas
        if len(calibration_echelle_df) == 0:
            inscrire_dans_log("ERREUR!  N{0} b{1} : index de calibration non trouvé(s) dans master_calibrations_e_df!".\
                  format(nsession, self.no_bloc))
            inscrire_dans_log("Ce bloc ne sera pas inclus dans la réduction.")
            # marquer le bloc comme non valide
            self.valide = False
            return

        #######################################################################
        # Validation 2 : map unique pour acquisitions échelle et sep
        #  valider si la/les** acquisition d'échelle dans calibration_echelle_df ont la même
        #  map que celle de sep du bloc courant
        #  ** S'il y a plus d'un index de calibration dans lstIndexCalE,
        # d'abord bâtir un set avec les valeurs et ajouter celle de sep
        # alors si len du set == 1, map est unique
        
        tempo = set()
        # trouver les map de calibration
        for idx in calibration_echelle_df.index:
            tempo.add(calibration_echelle_df.loc[idx, 'map'])
        # ajouter la map de sep
        tempo.add(self.sep.map)
        
        # fatal si non respecté
        # valide ssi un seul élément
        if len(tempo) == 1:
            self.reduc.mapEchelle = tempo.pop()
            del tempo
        else:
            inscrire_dans_log("ERREUR!  N{0} b{1}, cal_E : map non égales!".format(nsession, self.no_bloc))
            # la map n'est pas la même
            inscrire_dans_log("Ce bloc ne sera pas inclus dans la réduction.")
            # marquer le bloc comme non valide
            self.valide = False

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
        # inscrire les dates de chacun des index de calibration
        for idx in calibration_echelle_df.index:
            dth = str_dt_isot_a_TimeIsot(dt=calibration_echelle_df.loc[idx,'dt_obs_utc'])
            # ajouter jour julien
            listeDates.append(dth.jd)
            
        # ajouter la date (jd) de l'acquisition  de sep du bloc (dtime_utc_acq)
        listeDates.append(self.sep.dtime_utc_acq.jd)
        listeDates.sort()
        
        # calculer intervalle entre première et dernière date en min
        # jd * 1440 min/jour
        intervalle = abs(listeDates[0] - listeDates[len(listeDates)-1]) * 1440
        if intervalle > MAX_DELAI_DEPUIS_ACQUISITIONS_ECHELLE:
            inscrire_dans_log('*'*50)
            inscrire_dans_log("ERREUR!")
            inscrire_dans_log("  N{0} b{1}, cal_E et sep : délai depuis dern. acq échelle > {2} m!".\
                  format(nsession, self.no_bloc, MAX_DELAI_DEPUIS_ACQUISITIONS_ECHELLE))
            inscrire_dans_log("  Ce bloc ne sera pas inclus dans la réduction.")
            inscrire_dans_log("  Pour plus de détails, exécutez res.hier()")
            inscrire_dans_log('*'*50)
            self.reduc.delaiDepuisAcqEchValide = False

            # marquer le bloc comme non valide
            self.valide = False

        ##############################################
        # Validation 4 : intervalle de températures entre toutes les 
        # acquisitions d'un même bloc incluant acquisition d'échelle.
        # Valide si intervalle des temp_to <= MAX_DELTA_TEMPERATURE
        # sinon imprimer une alerte et continuer

        listeTemp = list()
        for idx in calibration_echelle_df.index:
            listeTemp.append(calibration_echelle_df.loc[idx,'temp_to'])
        listeTemp.append(self.sep.temp_to)
        listeTemp.sort()
        intervalle = abs(listeTemp[0] - listeTemp[len(listeTemp)-1])

        if intervalle > MAX_DELTA_TEMPERATURE:
            # non fatal pour le moment
            #
            self.reduc.deltaTemperatureValide = False
            inscrire_dans_log('*'*50)
            inscrire_dans_log("AVERTISSEMENT!")
            inscrire_dans_log("  N{0} b{1}, : intervalle de température entre calibration et sep > {2}°!".\
                  format(nsession, self.no_bloc, MAX_DELTA_TEMPERATURE))
            inscrire_dans_log("  Pour plus de détails, exécutez res.hier()")
            inscrire_dans_log('*'*50)

        #################################################
        # Validation 5 : delta matrix
        # La valeur de pa est lue dans le log reduc de sep.
        # Dans Reduc de sep, cette valeur est calculée à partir de delta_matrice_sep
        # qui DOIT être copiée par l'usager à partir du Reduc de pos correspondant.
        # Afin de vérifier si cette étape a été faite correctement, on 
        # vérifie si delta_matrice_sep == delta_matrice_pos.
         
        if self.reduc.delta_matrix_sep == self.reduc.delta_matrix_pos:
            self.reduc.deltaMatrixReducValide = True
        else:
            inscrire_dans_log("ERREUR!")
            inscrire_dans_log('  Session no. {0}, bloc {1} :'.\
                  format(nsession, self.no_bloc))
            inscrire_dans_log("   Le delta matrix de sep est différent de delta matrix de pos")
            inscrire_dans_log("     delta matrix de sep {0}, delta matrix de pos {1}\n".\
                  format(self.reduc.delta_matrix_sep, self.reduc.delta_matrix_pos))
            inscrire_dans_log("   Ceci peut vouloir dire que la valeur de delta matrix n'a")
            inscrire_dans_log("   pas été transférée de la pré-réduction (REDUC) de pos à")
            inscrire_dans_log("   celle de sep, ce qui rend la valeur de pa incorrecte!")
            inscrire_dans_log("   Ce bloc ne sera pas inclus dans la réduction.")

            # marquer le bloc comme non valide
            self.valide = False


#
# Classe Session
#
class Session:
    """Contient la liste des blocs (lstBlocs) d'observation d'une session
    d'observation.
    """

    def __init__(self, noSession, typeSession):
        """
        Paramètres positionnels :
        noSession           -- no de l'observation (S dans les rapports et structures)
        typeSession -- 'ech' Échelle, ou 'complete' Complète
        """

        self.noSession = noSession
        self.typeSession = typeSession
        self.nbrBloc = 0
        
        self.reductionCompletee = False
        
        # indique qu'au moins un bloc est valide
        self.au_moins_un_bloc_valide = True

        # ces attributs seulements pour observation 'complete',
        self.cheminS = ''

        # liste des objets Blocs
        self.lstBlocs = list()
        
    def ajouteBloc(self, no_bloc, type_ses):
        self.lstBlocs.append(Bloc(no_bloc, type_ses))
        self.nbrBloc += 1
   

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
                 WDSdr='non',
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
         chemin_systeme    -- String nom complet du fichier info_système
         nom_systeme_WDS   -- String id WDS du système (non normalisé) :
           par ex. stfa254 ou stf60
         id_sys_alt1 -- String nom alternatif 1, par défaut ''
         id_sys_alt2 -- String nom alternatif 2, par défaut ''
         WDSdr       -- String 'oui' | 'non', par-défaut 'non' (WDS data request obtenu)
         remarques   -- String remarques, notes, par défaut ''
        """
        
        if chemin_systeme != '' and nom_systeme_WDS == '' and\
                 id_sys_alt1 == '' and id_sys_alt2 == '' and\
                 WDSdr == 'non' and remarques == '':

            #
            # création par lecture d'un fichier csv
            #
            
            # nom du système
            self.nom = path.basename(chemin_systeme)

            # nom complet du fichier info système
            # debug self.ncfinfo_systeme = chemin_systeme + '/' + self.nom + '_info_système.csv'
            self.ncfinfo_systeme = chemin_systeme + '/info-systeme.csv'
            assert path.exists(self.ncfinfo_systeme),\
                'doublesOutils.Systeme.__init__ :: ' +\
                    self.ncfinfo_systeme + ' non trouvé.'
            
            # chemin du système
            self.rep = chemin_systeme
            
            # lire le fichier info-systeme qui contient tous les autres 
            # attributs
            try:
                # Pandas df du système
                self.informations_df = pd.read_csv(self.ncfinfo_systeme)
            except FileNotFoundError:
                print('doubleOutils.Systeme.__init__ :: fichier info-systeme non lisible.')
                sys.exit()
            
            return
        
        if chemin_systeme != '' and nom_systeme_WDS != '':
            # création à l'aide des arguments. Ceci inclus une
            # recherche astroquery dans le WDS et par diverses méthodes des
            # packages astropy et astroplan
            #
            # id_sys_alt1, id_sys_alt2 et remarques sont facultatifs
            
            # debug s'assurer que nom du système est en majuscules
            #self.nom = nom_systeme_WDS.replace(' ', '').upper()
            
            # normaliser source sur WDS_SRC_LEN_NOTES car
            self.nom= norm_WDS_src_notes(nom_systeme_WDS)
            
            # DEBUG ajout de WDSdr (data request) ici

            informations_dict = {
              'id_system': self.nom,
              'id_WDS': ['à venir'],
              'RAJ2000': ['à venir'],
              'DEJ2000': ['à venir'],
              'id_system_alt1': ['"' + id_sys_alt1 + '"'],
              'id_system_alt2': ['"' + id_sys_alt2 + '"'],
              'const': ['à venir'],
              'WDSdr': [WDSdr],
              # ATTENTION GARGER " SI NÉCESSAIRE P. E. pour une ','
              'remarques': ['"' + remarques + '"']
            }
            self.informations_df = pd.DataFrame(informations_dict)

            # s'assurer  que certains attributs texte soient entourés de "
            self.normalise_attributs_chaines()
            
            # nom complet du (futur) fichier info-systeme.csv
            #debug self.ncfinfo_systeme = chemin_systeme + '/' + self.nom + '/' + self.nom + '_info_système.csv'
            self.ncfinfo_systeme = chemin_systeme + '/' + self.nom + '/info-systeme.csv'

            
            #
            # compléter les attributs du système 'à venir'
            #
            
            # recherche de l'enregistrement de self.nom (nom de découvreur)
            # dans catalog='B/wds/wds' et inscrire id, ra et dec dans df
            result_rech_WDS = rech_wds(self.nom, '*')
            self.informations_df.loc[0, 'id_WDS'] = result_rech_WDS['WDS'].item(0)
            
            # prendre AD et DEC à partir de l'enregistrement 0
            raj2000 = result_rech_WDS['RAJ2000'].item(0)
            dej2000 = result_rech_WDS['DEJ2000'].item(0)
            self.informations_df.loc[0, 'RAJ2000'] = raj2000
            self.informations_df.loc[0, 'DEJ2000'] = dej2000
            
            # trouver la constellation d'après les coordonnées de l'enr 0
            coordonnees = SkyCoord(ra=raj2000, dec=dej2000, frame='fk5', unit=(u.hourangle, u.deg))
            self.informations_df.loc[0, 'const'] = coordonnees.get_constellation(short_name=True)


#
# Classe DoubleSessionsComplete
#
class DoubleSessionsComplete:
    """
    Contient toutes les données des session d'observations (S=1, 2, ...), la
    liste des blocs (b=1, 2, ...), pour le système et la paire concernés.
    """
    def __init__(self, typeSession='complete', chProg=''):
        """
        Paramètres Keyword :
         typeSession -- String type d'observation :
           'complete' -- observation complète avec pos et sep
         chProg -- String chemin du dossier du programme d'observation
          (par défault '')
        """
        self.typeSession = typeSession
        self.cheminProgramme = chProg
        self.reductionExecutee = False
        # nom complet du fichier log de réduction
        self.ncf_log_reduction = ''
        
        # nombre de sessions d'observation (S) et nombre de Rlogs
        self.nbrS = 0
        self.nbrRlogs = 0
        
        # lstObjSession contiendra la liste des objets Session
        self.lstObjSession = []
        
        # checksum (md5) de l'ensemble des fichiers logs utilisés pour
        # la post-réduction
        self.checksum = ''

        if typeSession == 'complete':
            self.typeSession = typeSession
            
            # créer objet Systeme avec fichier info-systeme.csv qui se trouve
            # dans le chemin chProg
            self.systeme = Systeme(chemin_systeme=path.dirname(path.dirname(chProg.rstrip('\\'))))

            # nom de la paire
            self.paire = ''
            
            # programme d'observation
            self.prog = path.basename(chProg.rstrip('\\'))
            
            ##################################
            # reductions_des_observations_df #
            ##################################
            
            # reductions_des_observations_df contient la liste de tous les blocs
            # d'observations
            # définition des colonnes de observations_df
            
            lstCol = ['obs_prog', 'id_system', 'id_WDS', 'paire',\
             'const', 'S', 'no_bloc', 'Date_UTC',\
             'obs_epoque_J', 'sep', 'sep_sigma', 'pa',\
             'pa_sigma', 'observatoire', 'observateur',\
             'transp', 'seeing', 'temp_to', 'humid',\
             'press_bar', 'map', 'deltaMatrixReducValide',\
             'delaiDepuisAcqEchValide',\
             'deltaTemperatureValide', 'eval_Q', 'lstIndexCalE',\
             'E_moy', 'filtre'
            ]
            
            # créer le df vide avec seulement les noms des colonnes définies
            # plus haut
            #
            self.reductions_des_observations_df = pd.DataFrame([], columns=lstCol)

            ###########################
            # moyennes_par_session_df #
            ###########################
            
            # dataframe qui contient les moyennes par sessions (des blocs)
            # créer moyennes_par_session_df vide avec les colonnes suivantes
            lstCol = ['S', 'Date_UTC', 'epoque_moy',\
            'sep_moy', 'sep_sigma_moy', 'pa_moy', 'pa_sigma_moy',
            'deltaTemperatureValide', 'delaiDepuisAcqEchValide',
            'deltaMatrixReducValide'
            ]
            self.moyennes_par_session_df = pd.DataFrame(list(), columns=lstCol)
            
            ##########################
            # groupes_de_sessions_df #
            ##########################


            # groupes_de_sessions_df contient les groupes de sessions qui
            # peuvent être utilisées pour publications et sert à produire
            # resultats_pour_publication_df
            
            # liste des tuples des no de session (S) et Date_UTC
            self.lst_tup_dates = list()
            
            # df des groupes de sessions
            lstCol = ['Groupe', 'Dates_UTC', 'delai_entre_S (j)', 'Sessions']
            self.groupes_de_sessions_df = pd.DataFrame(list(), columns=lstCol)

            #################################
            # resultats_pour_publication_df #
            #################################

            # resultats_pour_publication_df contient une ligne pour chaque
            # groupe de session espacée de moins de MAX_DELAI_ENTRE_OBSERVATIONS.
            # Les valeurs moyennes et autres renseignements pour le rapport
            # des sessions seront renseignés dans self.calculer_pour_publication
            # colonnes
            lstCol_resultats_pour_publication_df = ['prog', 'id_system', 'pr',\
            'con', 'N', 'groupe', 'Dates_UTC', 'delai_entre_N', 'Échéance', 'Sessions', 'epoque',\
            'pa', 'pa_sig', 'sep', 'sep_sig',\
            'WDS_o2', 'WDS_pa2', 'WDS_sep2',\
            'État']
            
            # créer resultats_pour_publication_df vide
            self.resultats_pour_publication_df =\
                pd.DataFrame(list(), columns=lstCol_resultats_pour_publication_df)
            
            #
            # moyennes des valeurs pour publication
            #
            #debug self.sep_moy, self.pa_moy, self.epoque_moy = 0, 0, 0
            # debug self.pa_sigma_moy, self.sep_sigma_moy = 0, 0
            
            # date de la dernière observation pour rapport des moyennes
            #debug self.date_obs_n = None

            # date Obs2 dans WDS
            self.wds_Obs2 = ''
            
            # différence en jours entre première et dernière observation
            #debug self.delai_entre_S = 0
            
            # état de la session, inscrire 'L' en position 3 pour 'Lucky imaging'
            # réfère à codes_etat_obs_dict
            # sera renseigné dans calculer_pour_publication
            self.etat = 'P L' # par défaut

    def liste_etat(self):
        #debug print("\ntypeSession : {0}".format(self.typeSession))
        #debug print("           Système : {0}".format(self.systeme.nom))
        #debug print("             Paire : {0}".format(self.paire))
        print("         Programme : {0}".format(self.prog))
        print("Nombre de sessions : {0}\n".format(self.nbrS))
        #debug print("      État : {0}".format(self.etat))
        print("  CheminProgramme  : {0}".format(self.cheminProgramme ))
        print("       Fichier log : {0}\n".format(self.ncf_log_reduction))
        
        if self.reductionExecutee:
            print(" ----------------------")
            print("           Réduction")
            print(" Session   complétée?")
            print(" ----------------------")
            for idx in range(len(self.lstObjSession)):
                print(" Session {0} {1}".format(self.lstObjSession[idx].noSession, self.lstObjSession[idx].reductionCompletee))
            print(" ======================")
            
            #debug print("\n Nombre de Rlogs : {0}".format(self.nbrRlogs))
            #debug print(" Toutes les sessions réduites : {0}".format(self.toutes_les_sessions_reduites()))
            #debug print("\n\n Résultats pour publication dans s.resultats_pour_publication_df")

    def toutes_les_sessions_reduites(self):
        for idx in range(len(self.lstObjSession)):
            tlsr = (True and self.lstObjSession[idx].reductionCompletee)
        return tlsr


    def cree_liste_objets_Session(self):
        """
        parcoure cheminProgramme et retourne un Tupple contenant la liste
        (List) des objets Session et un int du nombre de sessions.
        
        Retourne None, 0 si erreur ou aucun S*.
    
        Paramètres positionnels :
         typeSession -- String type d'observation ('ech' ou 'complete')
         cheminProgramme -- String chemin complet du programme d'observation
    
        Paramètre Keyword :
         nomSysteme -- String nom du système (par défaut None
                                              si observation d'échelle)
        """
        
        # liste des sessions d'observations
        lstSessions = list()
        
        if self.typeSession == 'ech':
            #########################################
            # il s'agit d'une observation d'échelle
            #########################################
    
            '''
            Ce type d'observation ne comprend pas de dossiers .cheminS. Il s'agit plutôt
            d'un dossier du type 2021-10-08b01 qui représente un seul bloc
            d'observation d'échelle. Il faut donc créer un objet Observation
            avec noSession=1 et ensuite créer l'unique bloc de typeSession='ech'
            '''
            # trouver le nom complet fichier log réduction (ncflr)
            lst_ncflr = glob.glob(self.cheminProgramme + '/reduc/RLog_*.txt')
    
            if len(lst_ncflr) != 1:
                # erreur fatale, il n'y a pas eu réduction d'échelle, puisque ncflr absent
                tampon = "doublesoutils.cree_liste_objets_Session :: log de reduc absent dans " + self.cheminProgramme + '/reduc'
                inscrire_dans_log(tampon)
                return
    
            # nous avons un log reduc
            # rechercher le nom de l'index de calibration dans cheminProgramme
            # pattern de recherche pour la forme yyyy-mm-jjbnn (ex. 2021-11-08b02)
            str_re_pat = r'([0-9]{4}\-[0-9]{2}\-[0-9]{2}b[0-9]{2})'
            obj_pat = re.compile(str_re_pat)
            obj_match = obj_pat.search(self.cheminProgramme)
            
            if obj_match is None:
                # erreur fatale, le nom du dossier ne respecte pas le format
                # pour les index de calibration
                tampon = "doublesoutils.cree_liste_objets_Session :: dans le chemin «" + self.cheminProgramme + '» :'
                inscrire_dans_log(tampon)
                tampon =  "... «{0}» n'est pas un nom d'index de calibration valide!".format(path.basename(self.cheminProgramme))
                inscrire_dans_log(tampon)
                return
    
            # nous avons un nom d'index de calibration valide
            #
            # trouver tous les *.txt dans cheminProgramme qui doivent comprendre
            # les logs d'acquisition et d'environnement (environnement.txt)
            lstFichiersTxt = glob.glob(self.cheminProgramme + '/*.txt')
    
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
                tampon = "doublesoutils.cree_liste_objets_Session :: Erreur fichier log environnement manquant."
                inscrire_dans_log(tampon)
                #debug return None, 0
            
            if ncfla is None:
                # erreur fatale
                tampon = "doublesoutils.cree_liste_objets_Session :: Erreur fichier log acquisition manquant."
                inscrire_dans_log(tampon)
                #debug return None, 0
    
            if ncfle is not None and ncfla is not None:
                # tout va bien
                # créer la liste d'observation avec un seul objet Session
                lstSessions.append(Session(1, 'ech')) # noSession=1
        
                # ajouter un seul bloc à cet objet Session
                lstSessions[0].ajouteBloc(0, 'ech') # nbrBlocs = noBloc = 1

                # incrire ncfla et ncfle dans le bloc
                lstSessions[0].lstBlocs[0].ech.ncfle = ncfle
                lstSessions[0].lstBlocs[0].ech.ncfla = ncfla
                
                # placer l'index de calibration dans l'objet reduc de l'objet Session,
                # bloc 1, (objet AcquisitionEchelle)
                lstSessions[0].lstBlocs[0].reduc.lstIndexCalE.append(obj_match.group(0))
        
                # inscrire nom complet fichier log réduction (ncflr)
                lstSessions[0].lstBlocs[0].reduc.ncflr_sep = lst_ncflr[0]
                
                self.lstObjSession = lstSessions
            
    
        else:
            #################################
            # type_session= 'complete'      #
            #################################
            
            # trouver tous les répertoires Sx dans self.cheminProgramme
            lstDesRepS = glob.glob(self.cheminProgramme + '/S*/')
            index_S = 0
            
            if len(lstDesRepS) == 0:
                # il n'y a aucune session N
                self.lstObjSession = None
                tampon = "doublesoutils.cree_liste_objets_Session :: pas de session (S) dans " + self.cheminProgramme
                inscrire_dans_log(tampon)
            else:
                # parcourir les dossiers de session
                for ch_rep_session_S in lstDesRepS:
                    '''
                    Ce type d'observation comprend un certain nombre de dossiers S* avec possiblement plusieurs
                    blocs d'observation bxx.
                    '''
        
                    # information de base de la session, programme, système, paire et blocs d'observations
                    # identifier d'abord le no de la session Sx
                    tempo = path.basename(path.dirname(ch_rep_session_S))
                    
                    # créer la session dans la liste lstSessions
                    lstSessions.append(Session(int(tempo.strip('S')), 'complete'))
                    
                    # chemin du répertoire Sx
                    lstSessions[index_S].cheminS = ch_rep_session_S
                    
                    # trouver liste des répertoires blocs bx, x=1, ...
                    listeRepBlocs = liste_blocs(ch_rep_session_S)
                                    
                    # vérifier s'il existe des blocs
                    if len(listeRepBlocs) == 0:
                        # il n'y a aucun bloc
                        lstSessions[index_S].lstBlocs = None
                        tampon = "doublesoutils.cree_liste_objets_Session :: pas de bloc dans " + self.cheminProgramme
                        inscrire_dans_log(tampon)
                    else:
                        # nom du programme d'observations tiré du chemin du programme
                        #debug obs_prog = path.basename(path.dirname(self.cheminProgramme))
                        #debug lstSessions[index_S].prog = path.basename(self.cheminProgramme)
            
                        # traiter tous les blocs
                        index_bloc = 0
                        for repBlocCourant in listeRepBlocs:
                            # récupérer le no du répertoire bloc pour inscription dans l'objet bloc
                            tempo = int(path.basename(path.dirname(repBlocCourant)).split('b')[1])
                            # ajouter le bloc courant à la session courante
                            lstSessions[index_S].ajouteBloc(tempo, 'complete') # nbrBlocs = noBloc = 1
            
                            ################################
                            # préparation traitement de sep
                            ################################
                            # déterminer le log d'acquisition et environnement
                            tempo = repBlocCourant + '/sep/'
            
                            #ncfla_sep, ncfle_sep = trouverLogsAetE(tempo, self.systeme.nom)
                            ncfla_sep, ncfle_sep = trouverLogsAetE(tempo)
                            if ncfle_sep is None:
                                tampon = "doublesoutils.cree_liste_objets_Session :: Erreur fichier log environnement manquant."
                                inscrire_dans_log(tampon)
                                tampon = "... {0}".format(tempo)
                                inscrire_dans_log(tampon)
                                #debug return None, 0
                            
                            if ncfla_sep is None:
                                tampon = "doublesoutils.cree_liste_objets_Session :: Erreur fichier log acquisition manquant."
                                inscrire_dans_log(tampon)
                                tampon = "... {0}".format(tempo)
                                inscrire_dans_log(tampon)
                                #debug return None, 0
            
                            # trouver log de réduction de sep
                            ncflr_sep = trouverLogReduc(repBlocCourant + '/sep/reduc')
            
                            if ncflr_sep is None:
                                # probablement pré-réduction non fait
                                tampon = "doublesoutils.cree_liste_objets_Session :: fichier log REDUC manquant."
                                inscrire_dans_log(tampon)
                                tampon = "... {0}".format(repBlocCourant + '/sep/reduc')
                                inscrire_dans_log(tampon)
                                inscrire_dans_log("    Probablement pré-réduction non faite")
                                #debug return None, 0
            
                            ################################
                            # préparation traitement de pos
                            ################################
                            # déterminer le log d'acquisition et environnement pos
                            tempo = repBlocCourant + '/pos/'
                            #ncfla_pos, ncfle_pos = trouverLogsAetE(tempo, self.systeme.nom)
                            ncfla_pos, ncfle_pos = trouverLogsAetE(tempo)
                            if ncfle_pos is None:
                                tampon = "doublesoutils.cree_liste_objets_Session :: Erreur fichier log environnement manquant."
                                inscrire_dans_log(tampon)
                                tampon = "... {0}".format(tempo)
                                inscrire_dans_log(tampon)
                                #debug return None, 0
                            
                            if ncfla_pos is None:
                                tampon = "doublesoutils.cree_liste_objets_Session :: Erreur fichier log acquisition manquant."
                                inscrire_dans_log(tampon)
                                tampon = "... {0}".format(tempo)
                                inscrire_dans_log(tampon)
                                #debug return None, 0
            
                            # trouver log de réduction de pos
                            ncflr_pos = trouverLogReduc(repBlocCourant + '/pos/reduc')
            
                            if ncflr_pos is None:
                                tampon = "doublesoutils.cree_liste_objets_Session :: fichier log REDUC manquant."
                                inscrire_dans_log(tampon)
                                tampon = "... {0}".format(repBlocCourant + '/pos/reduc')
                                inscrire_dans_log(tampon)
                                inscrire_dans_log("    Probablement pré-réduction non faite")
                                #debug return None, 0
            
                            # inscrire ncfla_sep, ncfle_sep et ncflr_sep
                            # inscrire ncfla_pos, ncfle_pos et ncflr_pos
             
                            # sep
                            lstSessions[index_S].lstBlocs[index_bloc].sep.ncfla =  ncfla_sep
                            lstSessions[index_S].lstBlocs[index_bloc].sep.ncfle =  ncfle_sep
                            if ncflr_sep is not None:
                                lstSessions[index_S].lstBlocs[index_bloc].reduc.ncflr_sep =\
                                    repBlocCourant + '/sep/reduc/' + ncflr_sep
                            else:
                                lstSessions[index_S].lstBlocs[index_bloc].reduc.ncflr_sep = None
                                lstSessions[index_S].lstBlocs[index_bloc].reduc.valide = False
            
                            # pos
                            lstSessions[index_S].lstBlocs[index_bloc].pos.ncfla =  ncfla_pos
                            lstSessions[index_S].lstBlocs[index_bloc].pos.ncfle =  ncfle_pos
                            if ncflr_pos is not None:
                                lstSessions[index_S].lstBlocs[index_bloc].reduc.ncflr_pos =\
                                    repBlocCourant + '/pos/reduc/' + ncflr_pos
                            else:
                                lstSessions[index_S].lstBlocs[index_bloc].reduc.ncflr_pos = None
                                lstSessions[index_S].lstBlocs[index_bloc].reduc.valide = False
                            index_bloc += 1
                    index_S += 1
            self.lstObjSession = lstSessions
            self.nbrS = index_S



    def creer_reductions_des_observations_df(self):
        """
        Crée le Pandas dataframe reductions_des_observations_df qui contient
        le  détail de toutes les réductions.
        """
        # au départ, len(self.reductions_des_observations_df) == 0
        
        # pour chacune des sessions
        for ses in self.lstObjSession:
            #print('Session no. {0}'.format(ses.lstObjSession))
            # pour chacun des bloc
            for b in ses.lstBlocs:
                # produire un df avec les données
                # prog_obs, system, id_wds, paire, const, N, b, dt_obs_utc,\
                #    epoque, sep, sep_sigma, pos, pos_sigma
                
                if b.reduc.ncflr_sep is not None and\
                  b.reduc.ncflr_pos is not None and\
                  b.reduc.valide and b.valide:
                    
                    # incrire la réduction complétée pour cette session
                    ses.reductionCompletee = True
                    data = [\
                             self.prog,\
                             self.systeme.nom,\
                             'WDS ' + self.systeme.informations_df.loc[0].id_WDS,
                             self.paire,
                             self.systeme.informations_df.loc[0].const,
                             ses.noSession,\
                             b.no_bloc,\
                             b.sep.dtime_utc_acq.value,\
                             #debug b.sep.dtime_utc_acq,\
                             b.sep.dtime_utc_acq.jyear,\
                             b.reduc.sep,\
                             b.reduc.sep_sigma,\
                             b.reduc.pa,\
                             b.reduc.pa_sigma,
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
        
        On en profite aussi pour déterminer l'état de chaque sessions.
        """
        # maintenant utilisé pour calculer les échéances
        # format de <class 'astropy.time.core.Time'> avec scale utc car
        # tous les dt sont UTC
        maintenant = Time(datetime.utcnow(), scale='utc')
       
        # au départ, len(self.resultats_pour_publication_df) == 0 et on
        # procède ssi len(self.moyennes_par_session_df) != 0
        
        if len(self.moyennes_par_session_df) != 0:
            # recherche id WDS de la source et paire pour obtenir Obs2, pa2 et
            # sep2 == année et valeurs dernière observation
            # ces résultats seront incluses dans les repports pour comparaison
            #
            result_rech_WDS = rech_wds(self.systeme.nom, self.paire)
            self.wds_Obs2 = result_rech_WDS[0]['Obs2'].item()
            self.wds_pa2 = result_rech_WDS[0]['pa2'].item()
            self.wds_sep2 = result_rech_WDS[0]['sep2'].item()
    
            #
            # produire la liste des tuples (sessions, dates) à partir
            # de moyennes_par_session_df
            #
            for idx in self.moyennes_par_session_df.index:
                self.lst_tup_dates.append((self.moyennes_par_session_df.loc[idx, 'S'],\
                           self.moyennes_par_session_df.loc[idx, 'Date_UTC']))
    
            if len(self.lst_tup_dates) == 1:
                # il y une seule session, alors
                # créer une liste 'artificielle' de la sorte
                # [(1, '2021-10-12'), (1, '2021-10-12'), 1)]
                # en répétant le tuple et avec un délai de 1 jour
                #
                self.lst_tup_dates.append(self.lst_tup_dates[0])
    
            # produire la liste des délais sous la forme suivante :
            # [(noSession1, date1), (noSession2, date2), délai]
            # par ex. :
            # [(1, '2021-10-12'), (3, '2021-10-17'), 5] où
            # le délai entre session 1 et 3 est de 5 jours
            liste_des_delais_sessions = produire_liste_delais(self.lst_tup_dates)
     
            #
            # produire le dataframes des groupes d'observations dans
            # groupes_de_sessions_df
            # sous la forme
            '''
                Groupe                                         Dates_UTC delai_entre_S (j)  Liste sessions (N)
              0    (1)                          [2021-10-12, 2021-10-14]                 2              [1, 2]
              1    (2)                          [2021-10-17, 2021-10-19]                 2              [3, 4]
              2    (3)                          [2021-10-14, 2021-10-17]                 3              [2, 3]
              3    (4)              [2021-10-12, 2021-10-14, 2021-10-17]                 5           [1, 2, 3]
              
              tous ces groupes sont valides!
            '''
            
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
                    
            #####################################################################
            # TRAITEMENT DES GROUPES DE SESSIONS de groupes_de_sessions_df
            # (tous les groupes de sessions avec un délai <= MAX_DELAI_ENTRE_OBSERVATIONS)
            # resultats_pour_publication_df PASSE 1
            #
            # parcourir groupes_de_sessions_df et calculer les moyennes de chaque
            # groupe à partir de self.moyennes_par_session_df et placer dans
            # resultats_pour_publication_df
            #
            # le code d'état sera TOL pour un groupe de plus d'une session ou
            # TAL sinon
            # le code d'état sera placé dans l'enregistrement de resultats_pour_publication_df
            #
            for index_groupe in self.groupes_de_sessions_df.index:
                str_groupe = self.groupes_de_sessions_df.loc[index_groupe, 'Groupe']
                lst_str_dates =  self.groupes_de_sessions_df.loc[index_groupe, 'Dates_UTC']
                delai =  self.groupes_de_sessions_df.loc[index_groupe, 'delai_entre_S (j)']
                lst_int_sessions_du_groupe = self.groupes_de_sessions_df.loc[index_groupe, 'Sessions']
                
                # calculer les moyennes des sessions qui se trouvent dans
                # lst_int_sessions_du_groupe
                if len(lst_int_sessions_du_groupe) == 1:
                    # le groupe contient une seule observation
                    # éviter de calculer la moyenne sur une seule observation
                    # juste utiliser les valeurs dans self.moyennes_par_session_df
                    #
                    nbrSessions = 1
                    no_de_session = lst_int_sessions_du_groupe[0]
                    # trouver l'index de no_de_session dans
                    # self.moyennes_par_session_df
                    #
                    index_de_no_de_session = self.moyennes_par_session_df.\
                      loc[self.moyennes_par_session_df.S==no_de_session].index[0]
                    
                    sep_moy    = self.moyennes_par_session_df.loc[index_de_no_de_session,'sep_moy']
                    sep_sigma_moy = self.moyennes_par_session_df.loc[index_de_no_de_session,'sep_sigma_moy']
                    pa_moy  = self.moyennes_par_session_df.loc[index_de_no_de_session,'pa_moy']
                    pa_sigma_moy = self.moyennes_par_session_df.loc[index_de_no_de_session,'pa_sigma_moy']
                    
                    epoque_moy = self.moyennes_par_session_df.loc[index_de_no_de_session,'epoque_moy']
                    #Date_UTC = self.moyennes_par_session_df.loc[index_de_no_de_session,'Date_UTC']
                    
                else:
                    # lst_int_sessions_du_groupe contient la liste exhaustive des
                    # sessions d'observations PAS UN INTERVAL!!!
                    #
                    # parcourir lst_int_sessions_du_groupe et calculer les moyennes
                    # avec chaque sessions à partir de self.moyennes_par_session_df
                    # par ex. si lst_int_sessions_du_groupe = [1,3,4], il faut
                    # parcourir session 1, 3 et 4 de self.moyennes_par_session_df
                    #
                    
                    nbrSessions = len(lst_int_sessions_du_groupe)
                    sep_m, pa_m, epoque_m, sep_sigma_m, pa_sigma_m =\
                        0, 0, 0, 0, 0
                        
                    for no_de_session in lst_int_sessions_du_groupe:
                        # trouver l'index de no_de_session dans
                        # self.moyennes_par_session_df
                        #
                        index_de_no_de_session = self.moyennes_par_session_df.\
                          loc[self.moyennes_par_session_df.S==no_de_session].index[0]
    
                        #        
                        # calculer les sommes = numérateurs des moyennes
                        #
                          
                        sep_m += self.moyennes_par_session_df.loc[index_de_no_de_session,'sep_moy']
                        # propagation des incertitudes sep_sigma
                        sep_sigma_m += math.pow(self.moyennes_par_session_df.loc[index_de_no_de_session,'sep_sigma_moy'],2)
                        
                        pa_m += self.moyennes_par_session_df.loc[index_de_no_de_session,'pa_moy']
                        # propagation des incertitudes pa_sigma
                        pa_sigma_m += math.pow(self.moyennes_par_session_df.loc[index_de_no_de_session,'pa_sigma_moy'],2)
                        
                        epoque_m += self.moyennes_par_session_df.loc[index_de_no_de_session,'epoque_moy']
                        # Date_UTC sera la dernière date lue dans le groupe
                        #dern_obs_utc = self.moyennes_par_session_df.loc[index_de_no_de_session,'Date_UTC']
    
                    #
                    # calculer les moyennes et propager les incertitudes
                    #
                    sep_moy = sep_m / nbrSessions
                    pa_moy = pa_m / nbrSessions
                    epoque_moy = epoque_m / nbrSessions
    
                    # pa_sigma_moy
                    pa_sigma_moy = math.sqrt(pa_sigma_m) / nbrSessions
            
                    # sep_sigma_moy
                    sep_sigma_moy = math.sqrt(sep_sigma_m) / nbrSessions
    
                    #
                    # produire resultats_pour_publication_df avec ces résultats
                    #
                    # déterminer le code d'état du groupe
                    #
            
                    # état de la session, inscrire 'L' en position 3 pour 'Lucky imaging'
                    # réfère à codes_etat_obs_dict
                    
                if nbrSessions > 1:
                    # toujours TOL dans ce cas
                    etat = 'TOL'
                    str_echeance = ''

                else:
                    # dans le cas d'une session avec N==1, il faut calculer la date d'échéance
                    # reprendre la date d'acquisition du bloc no 1 de sep pour calcul de l'échéance
                    dtUTC_acquisition_sep = self.lstObjSession[0].lstBlocs[0].sep.dtime_utc_acq
                    
                    # calculer échéance par rapport à MAX_DELAI_ENTRE_OBSERVATIONS
                    dt_echeance = dtUTC_acquisition_sep + MAX_DELAI_ENTRE_OBSERVATIONS
                    str_echeance = (dt_echeance).value.split('T')[0]
                    
                    # si maintenant est passé date d'échéance, alors sessions terminée TAL
                    # sinon session en cours CEL
                    #debug fudger maintenant pour forcer échéance non échue
                    #debug maintenant = dt_echeance - 4
                    if maintenant > dt_echeance:
                        etat = 'TAL'
                        delai = np.nan
                    else:
                        etat = 'CEL'
                        delai = abs(round((maintenant - dt_echeance).value, 1))
                    
                data = [
                   self.prog,\
                   self.systeme.nom,\
                   self.paire,\
                   self.systeme.informations_df.loc[0,'const'],\
                   nbrSessions,\
                   str_groupe,\
                   lst_str_dates,\
                   delai,\
                   str_echeance,\
                   lst_int_sessions_du_groupe,\
                   epoque_moy,\
                   pa_moy,\
                   pa_sigma_moy,\
                   sep_moy,\
                   sep_sigma_moy,\
                   self.wds_Obs2,\
                   self.wds_pa2,\
                   self.wds_sep2,\
                   etat
                ]
                self.resultats_pour_publication_df.loc[self.resultats_pour_publication_df.index.size] = data
            
            ############################################################################
            # TRAITEMENT DES SESSIONS ISOLÉES AYANT FAIT L'OBJET D'UNE RÉDUCTION VALIDE
            # resultats_pour_publication_df PASSE 2
            #
            # toutes les sessions «isolées» valides qui se touvent dans
            # self.moyennes_par_session_df représentent une possibilité de publication.
            # Il faut donc parcourir self.moyennes_par_session_df de nouveau et
            # ajouter toutes les sessions valides qui ne font pas partie d'un groupe
            # dans self.resultats_pour_publication_df
            #
            # L'état sera 'C7L' avec une échéance calculée si Dates_UTC (ayant 
            # un seule date) < MAX_DELAI_ENTRE_OBSERVATIONS ou l'état sera 'TAL' sinon. 
            #
            # Le code d'état se trouvera dans l'enregistrement de resultats_pour_publication_df
            #
            for idx_session in self.moyennes_par_session_df.index:
                if self.moyennes_par_session_df.loc[idx_session, 'delaiDepuisAcqEchValide'] and \
                   self.moyennes_par_session_df.loc[idx_session, 'deltaMatrixReducValide']:
                       # la session est valide
                       no_ses = self.moyennes_par_session_df.loc[idx_session, 'S']
                       session_isolee = True
                       # si la session n'est présente dabs aucun des groupes de
                       # groupes_de_sessions_df, alors elle est isolée
                       #
                       for index_s in self.groupes_de_sessions_df.index:
                           if no_ses in self.groupes_de_sessions_df.loc[index_s, 'Sessions']:
                               # la session se trouve dans un groupe est n'est donc
                               # pas isolée
                               session_isolee = False
                               
                       if session_isolee:
                           # la session est valide et isolée
                           # ajouter la session à self.resultats_pour_publication_df
                           str_groupe = '(-)'
                           # date d'acquisition en str
                           lst_str_dates = '[' + self.moyennes_par_session_df.loc[idx_session, 'Date_UTC'] + ']'
                           
                           # reprendre la date d'acquisition du bloc no 1 de sep pour calcul de l'échéance
                           dtUTC_acquisition_sep = self.lstObjSession[idx_session].lstBlocs[0].sep.dtime_utc_acq
                           lst_int_sessions_du_groupe = '[' + str(no_ses) + ']'
                           
                           dt_echeance = dtUTC_acquisition_sep + MAX_DELAI_ENTRE_OBSERVATIONS
                           str_echeance = (dt_echeance).value.split('T')[0]
                           
                           # si maintenant est passé date d'échéance, alors sessions terminée TAL
                           # sinon session en cours CEL
                           if maintenant > dt_echeance:
                               etat = 'TAL'
                               delai = np.nan
                           else:
                               etat = 'CEL'
                               delai = abs(round((dt_echeance - maintenant).value, 1))

                           data = [
                           self.prog,\
                           self.systeme.nom,\
                           self.paire,\
                           self.systeme.informations_df.loc[0,'const'],\
                           1,\
                           str_groupe,\
                           lst_str_dates,\
                           delai,\
                           str_echeance,\
                           lst_int_sessions_du_groupe,\
                           self.moyennes_par_session_df.loc[idx_session, 'epoque_moy'],\
                           self.moyennes_par_session_df.loc[idx_session, 'pa_moy'],\
                           self.moyennes_par_session_df.loc[idx_session, 'pa_sigma_moy'],\
                           self.moyennes_par_session_df.loc[idx_session, 'sep_moy'],\
                           self.moyennes_par_session_df.loc[idx_session, 'sep_sigma_moy'],\
                           self.wds_Obs2,\
                           self.wds_pa2,\
                           self.wds_sep2,\
                           etat
                           ]
                           self.resultats_pour_publication_df.loc[self.resultats_pour_publication_df.index.size] = data
                           
            self.reductionExecutee = True

              
            
            
    def calculer_moyennes_par_session(self):
        """
        À partir de reductions_des_observations_df, calcule les moyennes des
        sessions d'observations (N) du programme d'observations et produit
        le pandas dataframe moyennes_par_session_df. Pour une session, les
        moyennes doivent être calculées à partir des résultats des blocs
        d'observations, mais les mouennes sont valides seulement si les blocs
        respectent Les critères de validité des facteurs environnementaux suivants :
           - mises au point (map) inchangées au cours des acquisitions;
             -- indiqué par
           - les écarts de température <= MAX_DELTA_TEMPERATURE;
           - le délai depuis la dernière aquisition d'échelle
              <= MAX_DELAI_DEPUIS_ACQUISITIONS_ECHELLE
        
        moyennes_par_session_df contient les moyennes calculées
        pour chacune des sessions d'observation valides avec les critères
        de validité.
        
        moyennes_par_session_df sera utilisé pour resultats_pour_publication_df,
        aussi bien dans le Jupyter notebook des observations que
        dans le module listeReductions.
        """
        
        # au départ, len(self.moyennes_par_session_df) == 0 et on procède
        # ssi self.reductions_des_observations_df n'est pas vide
        
        if len(self.reductions_des_observations_df) != 0:
            # extraire la liste des valeurs des S dans tempo
            # de reductions_des_observations_df
            tempo = self.reductions_des_observations_df.loc[:,'S']
            
            # produire le set des no de sessions S
            listeDesSessions = set()
            for idx in tempo.index:
                listeDesSessions.add(tempo[idx])
                
            for session in listeDesSessions:
                # il faut travailler avec les blocs de chaque S de
                # self.reductions_des_observations_df
                # extraire ces blocs dans session_df
                session_df = self.reductions_des_observations_df[self.\
                                       reductions_des_observations_df.S == session]
                if len(session_df) == 1:
                    # un seul bloc d'observations, donc on retourne simplement
                    # l'enregistrement
                    idx = session_df.index[0]
                    sep_moy    = session_df.loc[idx,'sep']
                    pa_moy  = session_df.loc[idx,'pa']
                    epoque_moy = session_df.loc[idx,'obs_epoque_J']
                    dern_obs_utc = session_df.loc[idx,'Date_UTC'].split('T')[0]
                    pa_sigma_moy = session_df.loc[idx,'pa_sigma']
                    sep_sigma_moy = session_df.loc[idx,'sep_sigma']
    
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
    
                    sep_moy      = session_df.loc[interval_idx,'sep'].mean()
                    pa_moy    = session_df.loc[interval_idx,'pa'].mean()
                    epoque_moy   = session_df.loc[interval_idx,'obs_epoque_J'].mean()
                    dern_obs_utc = session_df.loc[interval_idx,'Date_UTC']\
                        [session_df.index[1]].split('T')[0]
            
                    # propager les incertitudes pa_sigma
                    tempo = 0
                    for val in session_df.loc[interval_idx,'pa_sigma']:
                        tempo += math.pow(val, 2)
                    pa_sigma_moy = math.sqrt(tempo) / len(session_df)
            
                    # propager les incertitudes sep_sigma
                    tempo = 0
                    for val in session_df.loc[interval_idx,'sep_sigma']:
                        tempo += math.pow(val, 2)
                    sep_sigma_moy = math.sqrt(tempo) / len(session_df)
                
                #
                # pour la session en cours
                # produire moyennes_par_session_df avec ces résultats
                # y compris les critères de validité
                #
                lstData = [
                   session,\
                   dern_obs_utc,\
                   epoque_moy,\
                   sep_moy,\
                   sep_sigma_moy,\
                   pa_moy,\
                   pa_sigma_moy,\
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
        pd.set_option("display.precision", 4)
        i = self.reductions_des_observations_df.index.size


        # 'm' == moyenne de toutes les observations et leurs blocs
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
            print("RÉSULTATS POUR PUBLICATION")
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
            # pour chacun des S (observations)
            # on désire imprimer les champs suivants (et dans cet ordre) :
            lstChamps = [\
                         'S',\
                         'bloc',\
                         'Date_UTC',\
                         'obs_epoque_J',\
                         'pa',\
                         'pa_sigma',\
                         'sep',\
                         'sep_sigma',\
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
            #debug print("    Paire : {0}".format(self.paire))
            #debug print("Programme : {0}".format(self.prog))
            #debug print('\n')
            self.liste_etat()
            print('\n')
            
            print("DÉTAILS DES SESSIONS D'OBSERVATIONS")
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
        if self.typeSession == 'complete':
            if sortie.upper() == 'FICHIER':
                # sortie vers fichier out.txt dans rép d'exécution
                ancien_stdout = sys.stdout
                f = open('out.txt', mode='w', encoding="utf-8")
                sys.stdout = f
    
            print('-'*102)
            #debug print('{0} :'.format(self.systeme.nom))
            print(self.systeme.informations_df)
            print('-'*102)
            
            # puisqu'ils ne change pas durant les observations, tirer typeSession,
            # et le nom de la paire de la première observation de la liste
            
            if len(self.lstObjSession) != 0:
                if self.lstObjSession[0].typeSession == 'complete':
                    print('              Paire : {0}'.format(self.paire))
                    print('          Programme : {0}'.format(self.prog))
                    print('  reductionExecutee : {0}'.format(self.reductionExecutee))
            
            #print(NL)
            print('-'*127)
            print('RÉSULTATS POUR PUBLICATION')
            if len(self.resultats_pour_publication_df) != 0:
                print(self.resultats_pour_publication_df)
            else:
                print('Aucun')
            print('\r')


            print('-'*127)
            print('RÉDUCTION DES OBSERVATIONS')
            if len(self.reductions_des_observations_df) != 0:
                print(self.reductions_des_observations_df)
            else:
                print('Aucun')
            print('\r')


            print('-'*127)
            print('MOYENNES PAR SESSION')
            if len(self.moyennes_par_session_df) != 0:
                print(self.moyennes_par_session_df)
            else:
                print('Aucun')
            
            print('\r')
            
            for ses in self.lstObjSession:
                print('#'*64)
                print('Session no {0} de type «{1}», contenant {2} bloc{3}'.format(\
                             ses.noSession, ses.typeSession, ses.nbrBloc, 's' if ses.nbrBloc > 1 else '') )
                print("Session valide : {0}".format(ses.au_moins_un_bloc_valide))
                print('Chemin {0} : '.format(ses.cheminS))
                print('#'*64)
                if ses.typeSession == 'ech':
                    for b in range(ses.nbrBloc):
                        print('    ' + '#' * 14)
                        print('  bloc {0}'.format(ses.lstBlocs[b].no_bloc))
                        print('    ' + '#' * 14)
                        for key in ses.lstBlocs[b].__dict__.keys():
                            print("        {0} = {1}".format(key, ses.lstBlocs[b].__dict__[key]))
                            if key == 'ech':
                                for key2 in ses.lstBlocs[b].__dict__[key].__dict__.keys():
                                    print("{0}{1} = {2}".format(' '*12, key2, ses.lstBlocs[b].__dict__[key].__dict__[key2]))
                            if key == 'reduc':
                                for key2 in ses.lstBlocs[b].__dict__[key].__dict__.keys():
                                    print("{0}{1} = {2}".format(' '*12, key2, ses.lstBlocs[b].__dict__[key].__dict__[key2]))
            
                    print('\r')
                
                if ses.typeSession == 'complete':
                    for b in range(ses.nbrBloc):
                        print(NL)
                        print('        ' + '#' * 21)
                        print('         Session {0}, bloc {1}'.format(ses.noSession, ses.lstBlocs[b].no_bloc))
                        print('        ' + '#' * 21)
                        print('\r')
                        for key in ses.lstBlocs[b].__dict__.keys():
                            print("        {0} = {1}".format(key, ses.lstBlocs[b].__dict__[key]))
                            if key == 'sep':
                                for key2 in ses.lstBlocs[b].__dict__[key].__dict__.keys():
                                    print("{0}{1} = {2}".format(' '*12, key2, ses.lstBlocs[b].__dict__[key].__dict__[key2]))
                            if key == 'pos':
                                for key2 in ses.lstBlocs[b].__dict__[key].__dict__.keys():
                                    print("{0}{1} = {2}".format(' '*12, key2, ses.lstBlocs[b].__dict__[key].__dict__[key2]))
                            if key == 'reduc':
                                for key2 in ses.lstBlocs[b].__dict__[key].__dict__.keys():
                                    if 'reduc_brute_df' in key2:
                                        print('reduc_brute_df :')
                                        print(ses.lstBlocs[b].__dict__[key].__dict__[key2])
                                    else:
                                        print("{0}{1} = {2}".format(' '*12, key2, ses.lstBlocs[b].__dict__[key].__dict__[key2]))
                                    
                    print('\r')
                    
            if sortie.upper() == 'FICHIER':
                f.close()
                sys.stdout = ancien_stdout
        else:
            print("code à développer pour une session de type 'ech'.")

    def liste_fichiers_logs(self):
        fichiers = list()
        for index_session in range(len(self.lstObjSession)):
            for index_bloc in range(len(self.lstObjSession[index_session].lstBlocs)):
                fichiers.append(self.lstObjSession[index_session].lstBlocs[index_bloc].sep.ncfle)
                fichiers.append(self.lstObjSession[index_session].lstBlocs[index_bloc].sep.ncfla)
                fichiers.append(self.lstObjSession[index_session].lstBlocs[index_bloc].reduc.ncflr_sep)
                fichiers.append(self.lstObjSession[index_session].lstBlocs[index_bloc].pos.ncfle)
                fichiers.append(self.lstObjSession[index_session].lstBlocs[index_bloc].pos.ncfla)
                fichiers.append(self.lstObjSession[index_session].lstBlocs[index_bloc].reduc.ncflr_pos)
        return fichiers

            
# %% FONCTIONS
def version():
    print(__name__ + ' version ' + str(no_version) + ', avril 2023.')

def filtre_etat_NA(etat):
    ''' filtre les état sans prog et / ou paire assigné '''
    return '?' in etat

def filtre_etat_X(etat):
    ''' filtre les états en erreur '''
    return 'X' in etat

def filtre_etat_C(etat):
    ''' filtre les états en cours '''
    return 'C' in etat

def filtre_etat_R(etat):
    ''' filtre les états qui demandent une réduction '''
    return 'R' in etat

def filtre_etat_P(etat):
    ''' filtre les états en planification '''
    return 'P' in etat

def filtre_etat_T(etat):
    ''' filtre les états terminé '''
    return 'T' in etat

def estNan(val):
    """ Cette comparaison permet de trouver si une variable contient NaN. """
    return val != val

def drive(distance, d=0, m=0, s=0):
    """
    Retourne le temps de parcourt (en s) par dérive sidérale pour parcourir la
    distance distance pour un objet ayant une déclinaison d m s.
    
    Paramètres positionnels :
       'dist' int distance en secondes d'arc
       déclinaison de la cible :
         'd' degrées (par défaut 0)
         'm' arc min (par défaut 0)
         's' arc sec (par défaut 0)
    """
    
    # transformer d m s en notation décimale
    dms = d + (m / 60) + (s / 3600)
    print(" {0} °ms".format(dms))
    
    # constante 15.041084 arcsec par seconde de temps solaire moyen
    # à l'équateur céleste
    #
    temps = abs(distance / (15.041084 * math.cos(math.radians(dms))))
    print(" {0} s".format(temps))

def ajoute_ckecksum(objet_hash, fich):
    with open(fich,"rb") as f:
        # Read fich  in chunks of 1K and update hash
        for byte_block in iter(lambda: f.read(1024),b""):
            objet_hash.update(byte_block)

def calcule_ckecksum_fichiers(chemin_programme):
    liste_fichiers = list()
    md5_hash_fichiers = hashlib.md5()
    lstDesRepS = glob.glob(chemin_programme + '/S*/')
    if len(lstDesRepS) != 0:
        for ch_rep_session_S in lstDesRepS:
            listeRepBlocs = liste_blocs(ch_rep_session_S)
            if len(listeRepBlocs) != 0:
                for rep_bloc in listeRepBlocs:
                    # trouver tous les logs d'acquisition dans /sep
                    ncfla, ncfle = trouverLogsAetE(rep_bloc + '/sep')
                    liste_fichiers.append(ncfle)
                    liste_fichiers.append(ncfla)
                    # trouver le Rlog_ dans /sep/reduc
                    tempo = trouverLogReduc(rep_bloc + '/sep/reduc')
                    if tempo is not None:
                        liste_fichiers.append(rep_bloc + '/sep/reduc/' + tempo)

                    # trouver tous les logs d'acquisition dans /pos
                    ncfla, ncfle = trouverLogsAetE(rep_bloc + '/pos')
                    liste_fichiers.append(ncfle)
                    liste_fichiers.append(ncfla)
                    # trouver le Rlog_ dans /pos/reduc
                    tempo = trouverLogReduc(rep_bloc + '/pos/reduc')
                    if tempo is not None:
                        liste_fichiers.append(rep_bloc + '/pos/reduc/' + tempo)
                    
    if len(liste_fichiers) != 0:
        # calculer et ajouter le md5 de chaque fichier à md5_hash
        for fichier in liste_fichiers:
            if fichier is not None:
                ajoute_ckecksum(md5_hash_fichiers, fichier)
        #debug print(md5_hash.hexdigest())
        return md5_hash_fichiers.hexdigest()


def inscrire_dans_log(strinscription):
    lst_log_post_reduction.append(strinscription)

def ecrire_log_sur_disque(ncflog=''):
    with open(ncflog, mode='w', encoding="utf-8") as f:
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
    lst_intervalles = []
    fin = len(liste_tup_dates) - 1
    for r in range(0, fin):
        debut = r
        fin = debut + 1
        while fin < len(liste_tup_dates):
            delai = round(diff_dt(liste_tup_dates[debut][1], liste_tup_dates[fin][1]), 1)
            if delai != 0:
                lst_intervalles.append((debut, fin, delai))
            fin += 1
        
    # créer une nouvelle liste des tuples avec le delai entre chaque couple
    tempo = list()
    for couple in lst_intervalles:
        date1 = liste_tup_dates[couple[0]]
        date2 = liste_tup_dates[couple[1]]
        #delai = abs(date2[1] - date1[1])
        delai = diff_dt(date2[1], date1[1])
        tempo.append([date1, date2, delai])
        
    # retourner liste triée sur délai et trouver le miminum
    tempo.sort(key=lambda tup: tup[2], reverse=False)
        
    return tempo


def produire_systag():
    """
    Retourne un systag (système tag), c.-à-d. la date du système au format iso
    """
    return datetime.now().isoformat().split('.')[0].replace(':','')

def post_reduction(type_session='complete', ch_prog=''):
    """
    Effectue la post-réduction des données du chemin passé en paramètre selon le
    type d'observation.
    
    Si ch_prog contient des résultats de pré-réduction :
    
    - pour une observation de type 'ech', retourne un objet Sessions.
    - Pour une observation de type 'complete', retourne un objet DoubleSessions.

    Si ch_prog ne contient pas de résultats de pré-réduction, mais contient
    des données d'acquisition :
    
    - pour une observation de type 'ech', retourne None.
    - Pour une observation de type 'complete', retourne un objet DoubleSessions
      avec les attributs qui décrivent les acquisitions des sessions d'observations.

    
    Retourne None en cas d'erreur.
    
    Inscrit les avertissements dans le fichier «post-réduction.log» dans ch_prog.

    Paramètres keywords :
    type_session -- String :
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
    global lst_log_post_reduction
    lst_log_post_reduction = list()
    inscrire_dans_log(produire_systag())

    # lire le fichier observatoires dans un df
    # lire les fichiers de support (maîtres de calibrations, etc)
    # et placer dans master_calibrations_e_df, master_filtres_cal_df, master_masques_cal_df
    #
    resultatOK = lire_fichiers_support(type_session, ch_prog)
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

    if type_session == 'complete':
        # Dans ce cas, ch_prog doit être dossier du type P2021-023 et avoir
        # au moins un S avec au moins un bloc d'observation. On doit bâtir un
        # objet DoubleSessionComplete.
        #

        ###################################################
        # créer l'objet DoubleSessionsComplete
        ###################################################
        # Dans l'objet sessions, l'objet Systeme sera créé à partir du chemin du système.
        # Remonter au dossier du système à partir du dossier de ch_prog
        # par ex. «STTA254» dans D:\DOCUMENTS\Astronomie\...\STTA254\AB\P2021-023
        objet_sessions = DoubleSessionsComplete(typeSession=type_session, chProg=ch_prog)
        
        # inscrire nom complet du fichier de log réduction
        objet_sessions.ncf_log_reduction = ncfichier_log_post_reduction
        
        # trouver le nombre de Rlog_ qui se trouvent dans ch_prog
        objet_sessions.nbrRlogs = len(listeLogsReduc(ch_prog))
        
        # nom de la paire dans objet_sessions
        objet_sessions.paire = path.basename(path.dirname(ch_prog.rstrip('\\')))

        # créer la liste des sessions
        objet_sessions.cree_liste_objets_Session()

        if len(objet_sessions.lstObjSession) == 0:
            # il n'y a pas de S
            inscrire_dans_log("Aucune sessions (répertoire S*) présente dans ce programme.")
            ecrire_log_sur_disque(ncflog=ncfichier_log_post_reduction)
            return None
        
        ######################################################################
        # boucle de réduction complète pour tous les blocs d'observations    #
        ######################################################################
        
        ses_actuelle = 0
        for ses in objet_sessions.lstObjSession:
            # debug
            for bloc in ses.lstBlocs:
                # lire et extraire données du log d'acquisition et
                # d'environnement sep et pos
                extraire_Log_acq_env(ses, bloc, 'sep')
                extraire_mesure_brutes_logReduc(ses, bloc, 'sep')
                extraire_Log_acq_env(ses, bloc, 'pos')
                extraire_mesure_brutes_logReduc(ses, bloc, 'pos')
                
                #################################################
                #                 Réduction
                #################################################

                # relecture du fichier des mesures brutes sep dans un dataframe
                # Pandas
                if bloc.reduc.ncflr_sep is not None and bloc.reduc.valide:
                    bloc.reduc.relecture_mes_brutes(path.dirname(bloc.reduc.ncflr_sep) + '/' + fich_mesures_brutes)
                    
                    ####################################
                    # validations générales pour sep
                    bloc.validations(ses.noSession)
                    if not bloc.valide:
                        ecrire_log_sur_disque(ncflog=ncfichier_log_post_reduction)
                        # le bloc est déjà marqué comme non valide
                        #debug return None
                    else:
                        ################
                        # Calculs sep et récupère pa
                        # NOTE : la valeur de thêta est dans la réduction de pos
                        bloc.reduc.calcule_sep()

            ses_actuelle += 1

            # validité de la session :
            #  si au moins un bloc est valide, alors la session est
            # également valide
            ses.au_moins_un_bloc_valide = False
            for bloc in ses.lstBlocs:
                if bloc.valide:
                    ses.au_moins_un_bloc_valide = True
                    break
                
        # création de l'objet DoubleSessions.reductions_des_observations_df
        objet_sessions.creer_reductions_des_observations_df()
        
        # calcule les moyennes par session d'observations
        objet_sessions.calculer_moyennes_par_session()
        
        # production des valeurs moyennes des sessions pour sep, pa,
        # epoque avec la propagation des incertitudes
        #
        # ce sont les résultats qui sont succeptibles d'être publiées
        #
        objet_sessions.calculer_pour_publication()
        
        # produire et inscrire la signature MD5 des fichiers logs utilisés
        # pour cette post-réduction
        lst_fichiers_logs = objet_sessions.liste_fichiers_logs()

        global md5_hash
        md5_hash = hashlib.md5()
        # calculer et ajouter le md5 de chaque fichier à md5_hash
        for fichier in lst_fichiers_logs:
            if fichier is not None:
                ajoute_ckecksum(md5_hash, fichier)
    
        #debug print(md5_hash.hexdigest())
        objet_sessions.checksum = md5_hash.hexdigest()

        # sauvegarder objet_sessions dans le dossier du PROGRAMME
        #
        tempo = ch_prog + '/' + objet_sessions.systeme.nom + '_' +\
                   objet_sessions.paire + '_' + objet_sessions.prog  + '_sessions.obj'
        filehandler = open(tempo, 'wb')
        pickle.dump(objet_sessions, filehandler)
        filehandler.close()
        
        inscrire_dans_log('\nTraitement terminé. Sessions enregistrées dans :')
        inscrire_dans_log(" ... «{0}»".format(tempo))
        ecrire_log_sur_disque(ncflog=ncfichier_log_post_reduction)

        return objet_sessions

    ###############################
    # Réduction D'échelle
    ###############################

    if type_session == 'ech':
        # créer l'objet sessions
        sessions = DoubleSessionsComplete(typeSession=type_session, chProg=ch_prog)
        sessions.cree_liste_objets_Session()

        #debug lstObservations, n = cree_liste_objets_Session(type_session, ch_prog)

        if len(sessions.lstObjSession) == 0:
            ecrire_log_sur_disque(ncflog=ncfichier_log_post_reduction)
            # retourner None en cas d'erreur fatale
            return None

        # Il n'y a pas de boucle puisqu'il n'y a pas de S et la notion de bloc
        # est intégrée dans le nom de dossier d'acquisition (par ex. 2020-10-08b01).
        # Extraire les données du log d'acquisition et d'environnement de la session
        # comme pour le type de mesure 'sep' et extraire et exporter
        # les mesures brutes à partir du log de REDUC dans un csv
        
        session = sessions.lstObjSession[0]
        bloc = sessions.lstObjSession[0].lstBlocs[0]
        extraire_Log_acq_env(session, bloc, 'sep')
        extraire_mesure_brutes_logReduc(session, bloc, 'sep')
        
        # lecture des mesures brutes dans un dataframe Pandas
        session.lstBlocs[0].reduc.relecture_mes_brutes(path.dirname(session.lstBlocs[0].reduc.ncflr_sep) +\
                                              '/' + fich_mesures_brutes)
        
        # passer LfplusDf, LfplusDf_sigma, Lo et Lo_sigma pour le calcul de Z
        session.lstBlocs[0].reduc.calcule_Z(\
           session.lstBlocs[0].reduc.LfplusDf,\
           session.lstBlocs[0].reduc.LfplusDf_sigma,\
           session.lstBlocs[0].reduc.Lo,\
           session.lstBlocs[0].reduc.Lo_sigma\
        )
        session.lstBlocs[0].reduc.calcule_E()
        imprime_rapport_E(session)
        maj_master_calibrations(session)
        
        # terminer le log et écrire sur disque
        session.reductionExecutee = True
        inscrire_dans_log("Traitement terminée.")
        ecrire_log_sur_disque(ncflog=ncfichier_log_post_reduction)
        
        return session


def convertToFloat(strVal):
    try:
        return float(strVal)
    except ValueError:
        print("{0} --> conversion à float impossible.".format(strVal))
        sys.exit()


def trouverLogReduc(ch):
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


def listeLogsReduc(ch):
    """
    Retourne une liste des noms complets des fichiers Rlog_* de réduction (REDUC)
    RLog_*.txt présents dans le chemin passé en paramètre ou une chaîne vide sinon.
    
    Seuls les RLog_* qui se trouvent dans les dossiers \reduc\ sont pris en
    compte

    Paramètre positionnel :
    ch -- String chemin du dossier d'où commencer la recherche.
    """
    listeR = list()
    for root, dirs, files in os.walk(ch):
        for name in files:
            if os.path.isfile(os.path.join(root, name)):
                if 'RLog_' in name:
                    listeR.append(os.path.join(root, name))
    # garder seulement les \\reduc\\
    listeFinale = list()
    for rep in listeR:
        if '\\reduc\\' in rep:
            listeFinale.append(rep)
    
    return listeFinale


def trouverLogsAetE(chemin):
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
    Parcourt le chemin passé en paramètre et retourne la liste (List()) des
    chemins des rép des bloc d'observations (c.-à-d. les répertoires b01, b02,
    ..., présents dans le chemin).

    Paramètre positionnel :
    ch -- String chemin complet à parcourir

    """
    return glob.glob(ch + '/b*/')


def extraire_Log_acq_env(ses, bloc, typeMesure):
    """
    Pour le bloc courant, repère les fichiers log d'acquisition et log de
    réduction et récupère diverses données dépendant du type de réduction
    ('ech' ou 'complete') et du types de mesure ('ech', 'sep' ou 'pos').
    Également, le fichier« environnement.txt» est lu et traité.
    
    S'il sagit d'une réduction d'échelle ('ech'), on en profite pour récupérer id_masque
    et id_filtre qui se trouvent dans environnement.txt.
    
    Les données sont colligées dans les objets Acquisition appropriés de l'objet Session (ses)
    passé en paramètre.
    
    Note : dans le cas d'une réduction d'échelle ('ech') le type de mesure (.typeMesure) est
    toujours 'sep', noSession==1 et no_bloc==1.

    Paramètres positionnels :
    ses -- objet Session
    bloc -- objet Bloc
    typeMesure -- String 'pos' ou 'sep'
    """

    # fle = nom complet du fichier log environnement
    if ses.typeSession == 'ech':
        fle = bloc.ech.ncfle

    if ses.typeSession == 'complete':
        if typeMesure == 'pos':
            fle = bloc.pos.ncfle
        if typeMesure == 'sep':
            fle = bloc.sep.ncfle

    if fle is not None:
        with open(fle) as f:
            lignesLues = f.readlines()
        f.close()

        ################################################
        # extraction des données du log d'environnement
        ################################################
        for ligne in lignesLues:
            if ses.typeSession == 'ech':
                # id_masque
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'masque=' in ligneForm:
                    bloc.ech.strIdMasque = (ligneForm.split('=')[1])
    
                # note d'acquisition dans sep
                if ('note=' in ligne) or ('note =' in ligne):
                    tempo = (ligne.split('=')[1]).rstrip('\n')
                    bloc.ech.note = tempo
    
                # id_filtre
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'filtre=' in ligneForm:
                    bloc.ech.strIdFiltre = (ligneForm.split('=')[1])
    
                # 'map' mise au point
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'map=' in ligneForm:
                    try:
                        bloc.ech.map = int((ligneForm.split('=')[1]))
                    except ValueError:
                        inscrire_dans_log('N{0}, b{1} ech : map doit être int!'.format(ses.noSession, bloc.no_bloc))
                        bloc.ech.valide = False
    
                # 'temp_to' température du to
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'temp_to=' in ligneForm:
                    bloc.ech.temp_to = convertToFloat((ligneForm.split('=')[1]))
    
            if ses.typeSession == 'complete':
                if typeMesure == 'sep':
                    ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                    # extraire le/les index de calibration
                    if 'index_cal_e=' in ligneForm:
                        tempo = ligneForm.split('=')[1]
                        if tempo != '':
                            bloc.reduc.lstIndexCalE = tempo.split(',')
                        else:
                            inscrire_dans_log("N{0}, b{1}, sep : index_cal_e est absent!".format(ses.noSession, bloc.no_bloc))
                            inscrire_dans_log("Exécutez sessions.hier() pour diagnostic.")
                            bloc.reduc.valide = False
    
                    # 'map' mise au point
                    ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                    if 'map=' in ligneForm:
                        try:
                            bloc.sep.map = int((ligneForm.split('=')[1]))
                        except ValueError:
                            inscrire_dans_log('N{0}, b{1} sep : map doit être int!'.format(ses.noSession, bloc.no_bloc))
                            bloc.sep.valide = False
    
                    # 'temp_to' température du to
                    ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                    if 'temp_to=' in ligneForm:
                        bloc.sep.temp_to = convertToFloat((ligneForm.split('=')[1]))
    
                    # 'transp' transparence
                    ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                    if 'transp=' in ligneForm:
                        bloc.sep.transp = convertToFloat((ligneForm.split('=')[1]))
    
                    # 'humid'
                    ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                    if 'humid=' in ligneForm:
                        bloc.sep.humid = convertToFloat((ligneForm.split('=')[1]))
    
                    # 'press_bar' pression barométrique
                    ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                    if 'press_bar=' in ligneForm:
                        bloc.sep.press_bar = convertToFloat((ligneForm.split('=')[1]))
    
                    # seeing
                    ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                    if 'seeing=' in ligneForm:
                        bloc.sep.seeing = (ligneForm.split('=')[1])
    
                    # id_filtre
                    ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                    if 'filtre=' in ligneForm:
                        bloc.sep.strIdFiltre = (ligneForm.split('=')[1])
    
                if typeMesure == 'pos':
                    ligneForm = ligne.replace(' ', '').rstrip('\n')
                    # le log d'environnement de pos contient l'évaluation du quadrant de pos
                    if 'eval_quadrant=' in ligneForm.lower():
                        bloc.pos.eval_Q = (ligneForm.split('=')[1]).upper()
    
                    # 'map' mise au point
                    ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                    if 'map=' in ligneForm:
                        try:
                            bloc.pos.map = int((ligneForm.split('=')[1]))
                        except ValueError:
                            inscrire_dans_log('N{0}, b{1} pos : map doit être int!'.format(ses.noSession, bloc.no_bloc))
                            bloc.pos.valide = False
    
                    # 'temp_to' température du to
                    ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                    if 'temp_to=' in ligneForm:
                        bloc.pos.temp_to = convertToFloat((ligneForm.split('=')[1]))
    
                    # 'transp' transparence
                    ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                    if 'transp=' in ligneForm:
                        bloc.pos.transp = convertToFloat((ligneForm.split('=')[1]))
    
                    # 'humid'
                    ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                    if 'humid=' in ligneForm:
                        bloc.pos.humid = convertToFloat((ligneForm.split('=')[1]))
    
                    # 'press_bar' pression barométrique
                    ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                    if 'press_bar=' in ligneForm:
                        bloc.pos.press_bar = convertToFloat((ligneForm.split('=')[1]))
    
                    # seeing
                    ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                    if 'seeing=' in ligneForm:
                        bloc.pos.seeing = (ligneForm.split('=')[1])
    
                    # id_filtre
                    ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                    if 'filtre=' in ligneForm:
                        bloc.pos.strIdFiltre = (ligneForm.split('=')[1])
                    
                # note d'environnement sep | pos
                if ('note=' in ligne) or ('note =' in ligne):
                    tempo = (ligne.split('=')[1]).rstrip('\n')
                    if typeMesure == 'sep':
                        bloc.sep.note = tempo
                    if typeMesure == 'pos':
                        bloc.pos.note = tempo
    
                # remarques d'environnement sep | pos
                if ('remarques=' in ligne) or ('remarques =' in ligne):
                    tempo = (ligne.split('=')[1]).rstrip('\n')
                    if typeMesure == 'sep':
                        bloc.sep.remarques = tempo
                    if typeMesure == 'pos':
                        bloc.pos.remarques = tempo

    
    ###########################################################
    # extraction des données dans le log d'acquisition
    ###########################################################
    #  fla = nom complet fichier log acquisition (de FC)

    if ses.typeSession == 'ech':
        # no_bloc == 0 toujours
        fla = bloc.ech.ncfla
        
        if fla is not None:
            with open(fla) as f:
                lignesLues = f.readlines()
            f.close()
    
            for ligne in lignesLues:
                # date UTC d'acquisition (en assumant que PC d'acquisition réglé sur UTC)
                if 'Date=' in ligne:
                    bloc.ech.date_utc_acq = (ligne.split('=')[1]).rstrip('\n')
            
                # heure UTC d'acquisition
                if 'Mid(UT)=' in ligne:
                    bloc.ech.heure_utc_acq = (ligne.split('=')[1]).rstrip('\n')
    
                # nombre d'images acquises
                if 'Limit=' in ligne:
                    tempo = (ligne.split('=')[1]).rstrip('\n')
                    if 'Frames' in tempo:
                        bloc.ech.nbr_images_acq = tempo.split(' ')[0]
                    elif 'Seconds' in tempo:
                        bloc.ech.nbr_images_acq = 'interval de ' + tempo.split(' ')[0] + ' s'
        else:
            bloc.ech.valide = False


    if ses.typeSession == 'complete':
        #debug b = bloc.no_bloc - 1
        if typeMesure == 'pos':
            fla = bloc.pos.ncfla
            if fla is not None:
                with open(fla) as f:
                    lignesLues = f.readlines()
                f.close()
    
                for ligne in lignesLues:
                    # date UTC d'acquisition (en assumant que PC d'acquisition réglé sur UTC)
                    if 'Date=' in ligne:
                        bloc.pos.date_utc_acq = (ligne.split('=')[1]).rstrip('\n')
                
                    # heure UTC d'acquisition
                    if 'Mid(UT)=' in ligne:
                        bloc.pos.heure_utc_acq = (ligne.split('=')[1]).rstrip('\n')
            
                    # nombre d'images acquises
                    if 'Limit=' in ligne:
                        tempo = (ligne.split('=')[1]).rstrip('\n')
                        if 'Frames' in tempo:
                            bloc.pos.nbr_images_acq = tempo.split(' ')[0]
                        elif 'Seconds' in tempo:
                            bloc.pos.nbr_images_acq = 'interval de ' + tempo.split(' ')[0] + ' s'
            else:
                bloc.pos.valide = False

        if typeMesure == 'sep':
            fla = bloc.sep.ncfla
            if fla is not None:
                with open(fla) as f:
                    lignesLues = f.readlines()
                f.close()
        
                for ligne in lignesLues:
                    # date UTC d'acquisition (en assumant que PC d'acquisition réglé sur UTC)
                    if 'Date=' in ligne:
                        bloc.sep.date_utc_acq = (ligne.split('=')[1]).rstrip('\n')
                
                    # heure UTC d'acquisition
                    if 'Mid(UT)=' in ligne:
                        bloc.sep.heure_utc_acq = (ligne.split('=')[1]).rstrip('\n')
            
                    # nombre d'images acquises
                    if 'Limit=' in ligne:
                        tempo = (ligne.split('=')[1]).rstrip('\n')
                        if 'Frames' in tempo:
                            bloc.sep.nbr_images_acq = tempo.split(' ')[0]
                        elif 'Seconds' in tempo:
                            bloc.sep.nbr_images_acq = 'interval de ' + tempo.split(' ')[0] + ' s'

            else:
                bloc.sep.valide = False
                
    ###################################################################################
    # VALIDATIONS
    # vérifier si toutes les variables communes «importantes» contiennent des données
    ###################################################################################

    # s'il s'agit d'une réduction d'échelle
    #  rechercher les informations de id_masque dans master_masques_cal_df
    if ses.typeSession == 'ech' and bloc.reduc.ncflr_sep is not None:
        global info_filtre_df, info_masque_df

        info_masque_df = master_masques_cal_df.loc[master_masques_cal_df.id_masque==\
                                                   bloc.ech.strIdMasque]
        if info_masque_df.index.size != 1:
            tampon = "Erreur, zéro ou plus d'une occurence de " + \
            bloc.ech.strIdMasque + ' dans master_masques_cal.csv'
            inscrire_dans_log(tampon)
            bloc.reduc.valide = False
        else:
            # placer LfplusDf, LfplusDf_sigma, Lo et Lo_sigma dans reduc
            bloc.reduc.LfplusDf = info_masque_df.loc[0, 'LfplusDf']
            bloc.reduc.LfplusDf_sigma = info_masque_df.loc[0, 'LfplusDf_sigma']

        # rechercher les informations de id_filtre dans master_filtres_cal_df
        info_filtre_df = master_filtres_cal_df.loc[master_filtres_cal_df.id_filtre==\
                                                   bloc.ech.strIdFiltre]
        
        if info_filtre_df.index.size != 1:
            tampon = "ech : Erreur, zéro ou plus d'une occurence de " + \
              bloc.ech.strIdFiltre + ' dans master_filtre_cal.csv'
            inscrire_dans_log(tampon)
            bloc.ech.valide = False
        else:
            bloc.reduc.Lo = info_filtre_df.loc[0,'Lo']
            bloc.reduc.Lo_sigma = info_filtre_df.loc[0,'Lo_sigma']


        if bloc.ech.temp_to is None:
            inscrire_dans_log('environnement ech temp_to requis')
            bloc.ech.valide = False

        if bloc.ech.map == 0:
            inscrire_dans_log('environnement ech map requise!')
            bloc.ech.valide = False

        # validation date et heure d'acquisition UTC
        d = bloc.ech.date_utc_acq
        h = bloc.ech.heure_utc_acq

        if d == '':
            inscrire_dans_log('acq ech date_utc_acq requise')
            bloc.ech.valide = False
            
        if h == '':
            inscrire_dans_log('acq ech heure_utc_acq requise')
            bloc.ech.valide = False


        # inscrire dt utc iso observation dans ...ech.dtime_utc_acq
        if d != '' and h != '':
            bloc.ech.dtime_utc_acq = str_dt_isot_a_TimeIsot(date=d, heure=h)

        if bloc.ech.nbr_images_acq == 0:
            inscrire_dans_log('acq ech nombre images ou secondes acquises requis')
            bloc.ech.valide = False

    if ses.typeSession == 'complete':
        #debug b = bloc.no_bloc - 1
        if typeMesure == 'sep':
            # environnement sep
            if bloc.sep.ncfle is not None:
                if bloc.sep.temp_to is None:
                    inscrire_dans_log('N{0}, b{1} sep : environnement sep temp_to requis'.format(ses.noSession, bloc.no_bloc))
                    bloc.sep.valide = False
                if bloc.sep.map == 0:
                    inscrire_dans_log('N{0}, b{1} sep : environnement sep map requise!'.format(ses.noSession, bloc.no_bloc))
                    bloc.sep.valide = False

            # validation date et heure d'acquisition UTC
            # acquisition sep
            if bloc.sep.ncfla is not None:
                d = bloc.sep.date_utc_acq
                h = bloc.sep.heure_utc_acq
                if d == '':
                    inscrire_dans_log('N{0}, b{1} acquisition sep date_utc_acq requise'.format(ses.noSession, bloc.no_bloc))
                    bloc.sep.valide = False
                if h == '':
                    inscrire_dans_log('N{0}, b{1} acquisition sep heure_utc_acq requise'.format(ses.noSession, bloc.no_bloc))
                    bloc.sep.valide = False
                
                # inscrire dt utc iso observation dans ...sep.dtime_utc_acq
                if d != '' and h != '':
                    bloc.sep.dtime_utc_acq = str_dt_isot_a_TimeIsot(date=d, heure=h)
    
                if bloc.sep.nbr_images_acq == 0:
                    inscrire_dans_log('N{0}, b{1} acquisition sep : nombre images ou secondes acquises requis'.format(ses.noSession, bloc.no_bloc))
                    bloc.sep.valide = False
        
            # vérifier qu'il y a au moins un index de calibration d'échelle
            # reduc sep
            if bloc.reduc.ncflr_sep is not None:
                if len(bloc.reduc.lstIndexCalE) == 0:
                    tampon = "N{0}, b{1} : le fichier «".format(ses.noSession, bloc.no_bloc) + bloc.sep.ncfle +\
                        "» ne contient pas d'index de calibration d'échelle!"
                    inscrire_dans_log(tampon)
                    bloc.reduc.valide = False

        if typeMesure == 'pos':
            # rien à faire avec bloc.reduc.ncflr_pos is not None:
            
            # environnement pos
            #
            if bloc.pos.ncfle is not None:
                if bloc.pos.temp_to is None:
                    inscrire_dans_log('N{0}, b{1} pos : environnement pos temp_to requis'.format(ses.noSession, bloc.no_bloc))
                    bloc.pos.valide = False
                    
                if bloc.pos.map == 0:
                    inscrire_dans_log('N{0}, b{1} pos : environnement pos map requise!'.format(ses.noSession, bloc.no_bloc))
                    bloc.pos.valide = False
                    
                if bloc.pos.eval_Q == '':
                    inscrire_dans_log("N{0}, b{1} pos : environnement pos valeur de eval_Q requise!".format(ses.noSession, bloc.no_bloc))
                    bloc.pos.valide = False

            # validation date et heure d'acquisition UTC
            # acquisition pos
            #
            if bloc.pos.ncfla is not None:
                d = bloc.pos.date_utc_acq
                h = bloc.pos.heure_utc_acq
                if d == '':
                    inscrire_dans_log('N{0}, b{1} pos : acq pos date_utc_acq requise'.format(ses.noSession, bloc.no_bloc))
                    bloc.pos.valide = False
                if h == '':
                    inscrire_dans_log('N{0}, b{1} pos : acq pos heure_utc_acq requise'.format(ses.noSession, bloc.no_bloc))
                    bloc.pos.valide = False
            
                # inscrire dt utc iso obsservation dans .dtime_utc_acq
                #
                if d != '' and h != '':
                    bloc.pos.dtime_utc_acq = str_dt_isot_a_TimeIsot(date=d, heure=h)
    
                if bloc.pos.nbr_images_acq is None:
                    tampon = 'N{0}, b{1} pos : acq pos nombre images ou secondes acquises requis'.format(ses.noSession, bloc.no_bloc)
                    inscrire_dans_log(tampon)
                    bloc.pos.valide = False
    

def extraire_mesure_brutes_logReduc(ses, bloc, typeMesure):
    """
    Pour le bloc courant, repère le fichier Rlog*.txt produit par reduc et
    écrit les mesures brutes de la réduction dans un nouveau fichier csv.

    Les données sont colligées dans les objets Reduction appropriés de l'objet
    Session (ses) passé en paramètre.
    
    Note : dans le cas d'une réduction d'échelle ('ech') les paramètres sont
    toujours «objet ses», 1, 1.

    Paramètres positionnels :
     ses        -- objet Session
     noBloc     -- int no du bloc traité
     typeMesure -- String 'pos' ou 'sep'
    """
    
    ############################################################################
    # lecture du fichier log de REDUC approprié pour le type de session et mesure
    if (ses.typeSession == 'ech') or (ses.typeSession == 'complete' and typeMesure == 'sep'):
        ncflr = bloc.reduc.ncflr_sep
    else:
        ncflr = bloc.reduc.ncflr_pos
        
    if ncflr is not None:
        # préparation du patron RE pour la recherche des nombres en point flottant
        # compilation par re
        str_patron_nombres = r'[0-9.]+'
        pn = re.compile(str_patron_nombres)

        with open(ncflr) as f:
            lignesLues = f.readlines()
        f.close()
            
        nbrLignes_totales = len(lignesLues)
        
        nligne = 0
        # no de la première ligne de mesures brutes à extraire
        nligne_depart_data = 0
    
        for ligne in lignesLues:
            if ses.typeSession == 'complete' and typeMesure == 'sep':
                # bien que la réduction est pour sep, en réalité pa (pos) se trouve dans le RLog de sep
                # au lieu de celui de pos
                if 'theta =' in ligne:
                    #récupérer theta et theta_sigma (p. e. theta =   108.9  (sigma:0.06  Med:108.9))
                    tempo = ligne.split('=')[1]
                    strTousLesNombres = pn.findall(tempo)
                    
                    bloc.reduc.pa = convertToFloat(strTousLesNombres[0])
                    bloc.reduc.pa_sigma = convertToFloat(strTousLesNombres[1])
    
                # récupérer également Delta Matrix pour comparer éventuellement avec celui de pos correspondant
                if 'Delta Matrix :' in ligne:
                    bloc.reduc.delta_matrix_sep =\
                        convertToFloat((ligne.split(':')[1].strip(' ')).rstrip('\n'))
    
            if ses.typeSession == 'complete' and typeMesure == 'pos':
                # juste récupérer delta matrice pour comparer avec celle qu'on trouverra
                # dans le log d'acquisition de sep corresponant au même bloc
                if 'Delta Matrix :' in ligne:
                    bloc.reduc.delta_matrix_pos =\
                        convertToFloat((ligne.split(':')[1].strip(' ')).rstrip('\n'))
    
            # trouver le no de lignes de la chaîne 'Raw Data' dans lignesLues
            if ses.typeSession == 'ech' or (ses.typeSession == 'complete' and typeMesure == 'sep'):
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
                if strTousLesNombres == []:
                    break
        
                # placer match 0, 1, 3 et 4 correspondants à xA, yA, xB, yB dans tampon de ligne
                reduc_brut_lst += {strTousLesNombres[0] + ', ' + strTousLesNombres[1] + ', ' + strTousLesNombres[3] + ', '\
                                      + strTousLesNombres[4]}
        
            # écrire le tampon de lignes dans reduc_brut.csv
            entete_csv = 'xA,yA,xB,yB'
            with open(path.dirname(ncflr) + '/' + fich_mesures_brutes, mode='w', encoding="utf-8") as f:
                # écrire l'en-tête
                f.write(entete_csv + NL)
        
                # écrire les valeurs
                for line in reduc_brut_lst:
                    for val in line:
                        f.write(val)
                    f.write(NL)
            f.close()
    else:
        # ncflr is None
        pass
    

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
            inscrire_dans_log("Écriture de {0} terminée!".format(nom_complet_fich_maitre_cal))
        else:
            print(NL + 'Données non inscrites!')
            inscrire_dans_log(NL + 'Données non inscrites!')

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
        print('\n Réduction exécutée avec les résultats suivants :')
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

    
def imprime_rapport_E(ses):
    """Imprime rapport. """
    
    print("  RÉDUCTION POUR CALIBRATION D'ÉCHELLE")
    #l = len('Index de calibration : {0}\n'.format(index_cal_e))
    l = len('Index de calibration : {0}\n'.format(ses.lstBlocs[0].reduc.lstIndexCalE[0]))
    print('#' * (l+3))
    print('# Index de calibration : {0} #'.format(ses.lstBlocs[0].reduc.lstIndexCalE[0]))
    print('#' * (l+3))
    print(NL)

    l = 50
    print('COORDONNÉES DES CENTROÏDES ET DISTANCES (px)'.center(l))
    print('-' * l)
    print(ses.lstBlocs[0].reduc.reduc_brute_df)
    
    l = 37
    print(NL * 2)
    print('STATISTIQUES DESCRIPTIVES'.center(l))
    print('-' * l)
    print('                dist_min : {0:>7.3f} px'.format(ses.lstBlocs[0].reduc.dist_min))
    print('                dist_max : {0:>7.3f} px'.format(ses.lstBlocs[0].reduc.dist_max))
    print('                dist_moy : {0:>7.3f} px'.format(ses.lstBlocs[0].reduc.dist_moy))
    print('              écart type : {0:>7.3f} px'.format(ses.lstBlocs[0].reduc.dist_sigma))
    print("nombre d'images retenues : {0:>2d} sur {1:s}\n".format(ses.lstBlocs[0].reduc.n_data,\
                                                                  ses.lstBlocs[0].ech.nbr_images_acq))
    
    print('E = {0:>4.4f} "/pix ± {1:>4.4f} "/pix'.format(ses.lstBlocs[0].reduc.E, ses.lstBlocs[0].reduc.E_sigma))

    
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
        return abs(str_dt_isot_a_TimeIsot(dt=dt2) - str_dt_isot_a_TimeIsot(dt=dt1)).value
    else:
        return abs(dt2 - dt1).value


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



def lire_fichiers_support(typeSession, chemin_prog):
    """
    Lecture des fichiers maîtres de calibration,
    lecture fichiers filtres et masques si typeSession 'ech',
    lecture fichier des observatoires
    
    retourne False
    
    Paramètres positionnels :
     typeSession -- String type session :
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
    # il faut distinguer l'environnement de développement de celui de production
    # si 'dev' dans chemin_prog, alors développement
    # sinon si 'data' dans chemin_prog, alors production
    #
    if 'dev' in chemin_prog:
        # en développement
        ch_rep_cal = r'D:\\DOCUMENTS\\Astronomie\\dev\med\\cal_e\\'
    else:
        # en production
        ch_rep_cal = r'D:\\DOCUMENTS\\Astronomie\\Data\\med\\cal_e\\'
    
    # lire le fichier maître des calibrations
    nom_complet_fich_maitre_cal = ch_rep_cal + nom_fich_m_cal
    try:
        master_calibrations_e_df = pd.read_csv(nom_complet_fich_maitre_cal)
        # faire une copie dans nom_complet_fich_maitre_cal + '.bak'
        master_calibrations_e_df.to_csv(nom_complet_fich_maitre_cal + '.bak', index=False)
        
    except FileNotFoundError:
        tampon = 'doubleoutils.lire_fichiers_support :: fichier {0} NON trouvé.'.format(nom_complet_fich_maitre_cal)
        inscrire_dans_log(tampon)
        boolResultatOK = False
    
    if typeSession == 'ech':
        # lire les deux fichiers master filtres et masques dans des df
        fich_mfiltres = ch_rep_cal + nom_fich_m_filtres
        fich_mmasques = ch_rep_cal + nom_fich_m_masques

        try:
            master_filtres_cal_df = pd.read_csv(fich_mfiltres)
            
        except FileNotFoundError:
            tampon = 'doubleoutils.lire_fichiers_support :: Fichier {0} NON trouvé.'.format(fich_mfiltres)
            inscrire_dans_log(tampon)
            boolResultatOK = False
            

        try:
            master_masques_cal_df = pd.read_csv(fich_mmasques)
            
        except FileNotFoundError:
            tampon = 'doubleoutils.lire_fichiers_support :: Fichier {0} NON trouvé.'.format(fich_mmasques)
            inscrire_dans_log(tampon)
            boolResultatOK = False

    return boolResultatOK


def valide_nom_systeme(chaine):
    """
    Valide silencieusement si chaine est un nom de système et existe bien dans
    le WDS et retourne tupple True | False et résultats de la recherche WDS | None.

    Paramètre positionnel :
     chaine -- String chaine à valider.
    """
    
    ch = chaine.lower()

    if len(ch) > WDS_SRC_LEN_NOTES:
        return False, None

    # recherche du discoverer
    str_re_pat = r'^[a-z]+'
    obj_pat = re.compile(str_re_pat)
    obj_match = obj_pat.match(ch)
    
    str_id_disc = obj_match.group(0)
    if str_id_disc == '' or len(str_id_disc) > 4:
        return False, None

    #print("str_id_disc= '" + str_id_disc + "'")

    # recherche du no de système
    str_re_pat = r'[0-9*]+'
    obj_pat = re.compile(str_re_pat)
    
    obj_match = obj_pat.search(ch)
    str_no_sys = obj_match.group(0)
    if str_no_sys == '' or len(str_no_sys) > 5:
        return False, None

    # valide si le système existe dans le WDS
    result_rech_WDS = rech_wds(ch, '*')
    if len(result_rech_WDS) != 0:
        return True, result_rech_WDS
    else:
        return False, None


def norm_WDS_src(source):
    """
    Retourne un String avec nom de la source normalisée au normes WDS,
    c.-à-d. avec un seul espace entre découvreur (3 ou 4 lettres) et
    no (1 à 4 chiffres) ssi len(source) < WDS_SRC_LEN_NOTES.

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
    # si < WDS_SRC_LEN_NOTES
    if len(str_id_disc) + len(str_no_sys) < WDS_SRC_LEN_NOTES:
        return(str_id_disc + ' ' * WDS_SRC_ESPACE_LEN + str_no_sys)
    else:
        return(str_id_disc + str_no_sys)


def norm_WDS_src_notes(source):
    """
    Normalise source sur WDS_SRC_LEN_NOTES caractères.

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


    # normalisation sur WDS_SRC_LEN_NOTES car

    nbr_espaces = WDS_SRC_LEN_NOTES - len(str_id_disc) - len(str_no_sys)
    #print('nbr_espaces= ', nbr_espaces)

    return(str_id_disc + ' ' * nbr_espaces + str_no_sys)

def rech_wds_id(src, paire):
    """Recherche les informations de src et paire au catalogue WDS ('B/wds/wds').

    Parameters
    ----------
    src : TYPE str
        Doit commencer par un chiffre, l'id WDS (par ex. '19591+3831') du système recherché.'
    paire : str
        La paire, sous la forme 'ab', 'a,bc', etc ou '*' si toutes les paires
        sont recherchées.

    Returns
    -------
    TYPE astroquery.utils.commons.TableList
         Le résultat de la recherche sous la forme d'une table.

    """
    
    viz.CACHE = False
    viz.ROW_LIMIT = 120000 # au cas où ?

    if src[0].isdigit() and len(src) == 10:
        return viz(catalog='B/wds/wds', columns=WDS_colonnes).query_constraints(WDS=src, Comp=paire)
               # viz.query_constraints(catalog='B/wds/wds', WDS=src, Comp=paire)
    else:
        return 'Erreur pas un id WDS'


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
    
    viz.CACHE = False
    viz.ROW_LIMIT = 120000 # au cas où ?
    global strSource_format_pour_Notes

    # normaliser pour recherche WDS
    strSource = norm_WDS_src(src)
    
    # si nécessaire, remplacer 4e car par '?', p. e. «stfa 60» devient «stf? 60»
    # split sur ' ' puisque strSource est normalisé avec un espace
    spl = strSource.split(' ')
    if len(spl[0]) == 4:
        strSource = spl[0][:3] + '? ' + spl[1]
    
    ### soumettre la requête
    #strSource = 'H 3*'
    # resultat = viz.query_constraints(catalog='B/wds/wds', Disc=strSource, Comp=paire)
    resultat = viz(catalog='B/wds/wds', columns=WDS_colonnes).query_constraints(Disc=strSource, Comp=paire)
    #(catalog="VII/258/vv10",columns=['*', '_RAJ2000', '_DEJ2000'])
    if resultat != []:
        # enlever les sources en trop
        idx = []
        # normaliser source
        src_norm = norm_WDS_src_notes(src)
        for r in range(len(resultat[0])):
            if resultat[0]['Disc'].item(r) == src_norm:
               idx.append(r)
        nouveau = resultat[0][idx]
        return nouveau
    else:
        return []

    # variations avec critère Obs2
    #result = viz.query_constraints(catalog='B/wds/wds', Disc=source, Comp=paire, Obs2='<=2015')
    ##result = viz.query_constraints(catalog='B/wds/wds', Disc=source, Comp=paire, Obs2='2011..2015')
    

def rech_wds_notes(wds_src):
    """
    Recherche les notes au sujet de src dans les notes au WDS ('B/wds/notes'), si présentes.

    Parameters
    ----------
    wds_src : TYPE str
        L'identité WDS de la source'.

    Returns
    -------
    TYPE astroquery.utils.commons.TableList
        Il s'agit d'une table des résultats.

    """
    notes_q = viz.query_constraints(catalog='B/wds/notes', WDS=wds_src)
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
    
    if len(qres) != 0:
        print('\nIl y a {0} résultats pour «{1}», paire = «{2}».\n'.format(len(qres), strSource, strPaire))
        # trier sur WDS et composants
        qres.sort(['Disc', 'Comp'])
        #NOTE qres[qres.keys().pprint()
    
        print('Données tirées du Washington Double Stars Catalog (WDS)')
        print('Tris sur "Disc" et "Comp"')
        max_larg = 160
        print('-' * max_larg)
        qres.pprint(show_unit=True, max_width=max_larg, max_lines=200)
        print('-' * max_larg)
        
        
        if notes:
            # obtenir WDS Notes
            # obtenir l'id WDS de la source
            id_WDS = qres['WDS'].item(0)
            wds_notes = rech_wds_notes(id_WDS)
            if wds_notes != []:
                print('\n ***** WSD Notes pour {0} *****'.format(strSource))
                wds_notes[0].pprint(max_width=120)
            else:
                print('Aucune note trouvée.')
    else:
        print("La requête pour '{0}' n'a donné aucun résultat".format(strSource))
        sys.exit()


def liste_variables_environnement():
    """
    Liste les variables d'environnement.

    Parameters
    ----------
    Aucun
    
    Returns
    -------
    None.

    """
    version()
    print('MAX_DELAI_DEPUIS_ACQUISITIONS_ECHELLE', MAX_DELAI_DEPUIS_ACQUISITIONS_ECHELLE)
    print('MAX_DELTA_TEMPERATURE', MAX_DELTA_TEMPERATURE)
    print('MAX_DELAI_ENTRE_OBSERVATIONS', MAX_DELAI_ENTRE_OBSERVATIONS)
    print('WDS_SRC_LEN_NOTES', WDS_SRC_LEN_NOTES)
    print('WDS_SRC_ESPACE_LEN', WDS_SRC_ESPACE_LEN)
    print('nom_fich_m_cal', nom_fich_m_cal)
    print('nom_fich_m_filtres', nom_fich_m_filtres)
    print('nom_fich_m_masques', nom_fich_m_masques)
    print('t_scale', t_scale)
    print('t_format', t_format)
    print('fich_mesures_brutes', fich_mesures_brutes)


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
        # debug info_systemes_df = info_systemes_df.append(pd.read_csv(dir),ignore_index=True)
        info_systemes_df = pd.concat([info_systemes_df, pd.read_csv(dir)], ignore_index=True)
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
      Retourne True ssi le nom du dernier répertoire du chemin passé en paramètre est
      formaté correctement comme un programme d'observation, par ex. 'P2022-004'.
      
      Par exemple, dans le chemin suivant 
      
     'D:\\DOCUMENTS\\Astronomie\\Data/med\\A   152\\AB\\P2022-020\\' ;
     
     les segments qui se trouvent à la suite de '/med', c.-à-d. : '\\A   152\\' et '\\AB\\'
     ont déjà été trouvés valides comme système et paire respectivement. Donc, le pattern
     'Paaaa-nnn' recherché doit obligatoirement se retrouver à la fin du chemin.
     
     Ici l'on cherche '\\P2022-004\\'
      
    Paramètre positionnel
     chemin -- chemin du répertoire à vérifier.
    """
    if not estNan(chemin):
        str_re_pattern = r'(/P[0-9]{4}-[0-9]{3}/)$'
        obj_pat = re.compile(str_re_pattern)
        res = obj_pat.search(chemin.replace('\\', '/'))
        return res is not None
    return False


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
    Imprime un rapport détaillé des réductions trouvées dans chemin et retourne un 
    Pandas DataFrame trié des réductions.

    Paramètres Keyword
     chemin          -- String chemin de tête des systèmes (par défaut '')
     tri             -- Int ordre de tri de 1 à 4, selon dictionnaire
                        liste_de_tri_prog
     impr_table_etat -- Boolean imprime légende des états (par défaut True)
     sortie          -- T (terminal) ou F (fichier)
    """
    
    if sortie.upper() == 'F':
        # sortie vers fichier ./med/med-planification/....txt
        systag = produire_systag()
        
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
            
        #### imprimer le rapport des réductions
        print('Trié par', liste_de_tri_reduc[tri])
        print('\r')
        #print('-' * 176)
    
        pd.set_option('display.expand_frame_repr', True)
        pd.set_option('display.colheader_justify', 'right')
        pd.set_option('display.max_colwidth', 50)
        pd.set_option('display.max_column', 18)
        pd.set_option('display.width', 300)
        pd.set_option('display.max_row', 10000)
        pd.set_option("display.precision", 3)
    
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
            for code in codes_etat_obs_dict:
                print('   {0} {1}'.format( code, codes_etat_obs_dict[code]))
        
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
    

def produire_liste_programmes(ch):
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
        lst_sessions = []
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
                #debug nbr_etat_NA += 1
            
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
                            # s'il n'y a pas de programme, il faut quand même créer
                            # l'enregistrement, l'ajouter au df et
                            # incrémenter le compteur approprié

                            data = [obs_prog, id_system, paire, id_WDS, const, lst_sessions, Dates_UTC, delai, str_dth_echeance_utc, etat]
                            # ajouter à la liste des programmes
                            lst_prog_df.loc[lst_prog_df.index.size] = data
                            #debug nbr_etat_NA += 1
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
                                    # un bloc dans ce S
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
                                        #debug nbr_etat_P += 1
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
                                            
                                            checksum = calcule_ckecksum_fichiers(s.cheminProgramme)

                                            if s.checksum != checksum:
                                                # ************ Les données ont changées! ****************
                                                # il faut lancer une post-réduction
                                                s = post_reduction(type_session='complete', ch_prog=chemin_prog)
                                                        
                                        else:
                                            # il n'y a pas d'objet s,
                                            # il n'y a donc pas eu de réduction exécutée
                                            # mais nous devons vérifier s'il peut exister des 
                                            # données d'acquisition valides...
                                            # on exécute donc une post-réduction ;)
                                            s = post_reduction(type_session='complete', ch_prog=chemin_prog)
                                                            
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
                                            
                                            # récupérer échéance dans s.resultats_pour_publication_df
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
                                            #debug nbr_etat_T += 1

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
                                                        # si moins de MAX_DELAI_ENTRE_OBSERVATIONS jours alors etat = 'CRL' ou 'CEL'
                                                        # sinon etat = 'TRL'
                                                        #debug str_dth_echeance_utc = 'à calculer selon les blocs'
                                                        # calculer le délai
                                                        
                                                        dtUTC_acquisition_sep = s.lstObjSession[index_session].lstBlocs[index_bloc].sep.dtime_utc_acq
                                                        lst_dates = []
                                                        lst_dates.append(dtUTC_acquisition_sep.value.split('T')[0])
                        
                                                        # dans ce cas, il faut calculer la date
                                                        # d'échéance de l'observation qui est
                                                        # la date unique qui se trouve dans lst_dates
                                                        # + MAX_DELAI_ENTRE_OBSERVATIONS
                                                        #
                                                        #debug dth_echeance_utc = str_dt_isot_a_TimeIsot(dt=dtUTC_acquisition_sep) + MAX_DELAI_ENTRE_OBSERVATIONS
                                                        
                                                        dth_echeance_utc = dtUTC_acquisition_sep + MAX_DELAI_ENTRE_OBSERVATIONS
                                                        #debug str_dth_echeance_utc = dth_echeance_utc.value.split('T')[0]
                                                        #vérifier si OK
                                                        str_dth_echeance_utc = dth_echeance_utc.to_value('isot').split('T')[0]
                                                        if s.lstObjSession[index_session].au_moins_un_bloc_valide:
                                                            if maintenant > dth_echeance_utc:
                                                                etat = 'TRL'
                                                                #debug nbr_etat_T += 1
                                                                #debug nbr_etat_R += 1
                                                            else:
                                                                etat = 'CRL'
                                                                #debug nbr_etat_C += 1
                                                                #debug nbr_etat_R += 1
                                                        else:
                                                            etat = 'TXL'
                                                            #debug nbr_etat_X += 1
                                                            #debug nbr_etat_T += 1

                                                        #debug delai = round(diff_dt(maintenant.isoformat(), dth_echeance_utc.value),1)
                                                        delai = round(abs((maintenant - dth_echeance_utc).value), 1)
                                                    else:
                                                        # il reste seulement le cas etat = 'P L'
                                                        etat = 'P L'
                                                        #debug nbr_etat_P += 1
                                                        delai = np.nan
                                                
                                                # construire l'enregistrement
                                                data = [obs_prog, id_system, paire, id_WDS, const, lst_sessions, Dates_UTC, delai, str_dth_echeance_utc, etat]
                                                # ajouter à la liste des programmes
                                                lst_prog_df.loc[lst_prog_df.index.size] = data
                                            else:
                                                # il s'agit du cas où une réduction à eue lieue
                                                # donc il aura un C ou un X si aucun bloc valide
                                                # ici on a besoin de date_utc_acq de l'un
                                                # des blocs valides. On peut donc passer.
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
    if sortie.upper() == 'F':
        systag = produire_systag()
        
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
    programmes_df = produire_liste_programmes(chemin)
    nbrEnregistrements = len(programmes_df)
    int_nbr_prog_uniques = len(liste_programmes_uniques)
   
    ### trier le résultat
    programmes_df.sort_values(by=liste_de_tri_prog[tri], ignore_index=True,\
                              inplace=True)
    #programmes_df.fillna(' ', inplace=True)
    
    # Calculer le nombre par état
    #
    ## nbr_etat_T (terminé)
    etat_T_serie = programmes_df['État'].apply(filtre_etat_T)
    etat_T_df = programmes_df.drop(programmes_df.loc[etat_T_serie].index)
    nbr_etat_T = nbrEnregistrements - len(etat_T_df)
    
    
    ## nbr_etat_P (en planification)
    #
    etat_P_serie = programmes_df['État'].apply(filtre_etat_P)
    etat_P_df = programmes_df.drop(programmes_df.loc[etat_P_serie].index)
    nbr_etat_P = nbrEnregistrements - len(etat_P_df)
    
    ## nbr_etat_NA (sans prog / paire assigné)
    #
    etat_NA_serie = programmes_df['État'].apply(filtre_etat_NA)
    etat_NA_df = programmes_df.drop(programmes_df.loc[etat_NA_serie].index)
    nbr_etat_NA = nbrEnregistrements - len(etat_NA_df)

    ## nbr_etat_C (en cours)
    #
    etat_C_serie = programmes_df['État'].apply(filtre_etat_C)
    etat_C_df = programmes_df.drop(programmes_df.loc[etat_C_serie].index)
    nbr_etat_C = nbrEnregistrements - len(etat_C_df)
    
    ## nbr_etat_R (données prêtes pour pré-réduction)
    #
    etat_R_serie = programmes_df['État'].apply(filtre_etat_R)
    etat_R_df = programmes_df.drop(programmes_df.loc[etat_R_serie].index)
    nbr_etat_R = nbrEnregistrements - len(etat_R_df)

    ## nbr_etat_X (données inutilisables)
    #
    etat_X_serie = programmes_df['État'].apply(filtre_etat_X)
    etat_X_df = programmes_df.drop(programmes_df.loc[etat_X_serie].index)
    nbr_etat_X = nbrEnregistrements - len(etat_X_df)

    #### imprimer le rapport des programmes
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
        for code in codes_etat_obs_dict:
            print('   {0} {1}'.format( code, codes_etat_obs_dict[code]))
    
    # inutile d'imprimer ces exemples si stdout est redirigé vers un fichier
    if sortie != 'F':
        print('\nEXEMPLES DE REQUÊTES :')
        print("liste_des_programmes_df.query(\"obs_prog == 'P2022-020'\")")
        print("liste_des_programmes_df.query(\"id_system == 'STF 982'\")")
        print("liste_des_programmes_df.query(\"const == 'And'\")")
        print("liste_des_programmes_df.query(\"const == 'And' or const == 'Gem'\")")
        print("avec la variable rech = ['STT545', 'STF60'] :")
        print('  liste_des_programmes_df.query("id_system == @rech")')

    if sortie == 'F':
        # rétablir stdout
        sys.stdout = ancien_stdout
        f.close()
        print("Sortie dans :\n  {0}".format(ncfis))

    return programmes_df

    
# %% INITIALISATIONS
no_version = 54
# à partir de cette version, ce module inclut le code du module doubleslistes

'''
Crée un dictionnaire des codes de notes pour les
observations d'étoiles doubles

Format sur 3 caractères, par ex. 'C L'
Position 1 : code de suivi {X, E, C, P ou T}
Position 2 : libre pour développement futur
Position 3 : code de méthode de mesure {L ou I}
'''

# CONSTANTES DE VALIDATIONS
# fonction de date et heure
# délai max entre deux acquisitions d'échelle (m)
MAX_DELAI_DEPUIS_ACQUISITIONS_ECHELLE = 120.0
# différence de température entre deux acquisitions (°C)
MAX_DELTA_TEMPERATURE = 5.0
# délais entre première et dernière observation (jours)
MAX_DELAI_ENTRE_OBSERVATIONS = 7.0

codes_etat_obs_dict = {
    '123': ['1:état, 2:explication, 3:méthode.'],
    'C..': ["En cours d'observation. Voir explication."],
    'P..': ['Programme en PLANIFICATION.'],
    'T..': ['Programme TERMINÉ, voir explication.'],
    '?..': ["Aucun programme d'observation assigné."],
    '.A.': ['ACCEPTABLE, mais programme terminé avec N=1 et délai > {0} j.'.format(MAX_DELAI_ENTRE_OBSERVATIONS)],
    '.E.': ["ÉCHÉANCE de {0} j imminante!".format(MAX_DELAI_ENTRE_OBSERVATIONS)],
    '.O.': ['OPTIMAL. Programme complété avec N>1.'],
    '.S.': ["Nouvelle SESSION à planifier."],
    '.R.': ["Il peut y avoir des données prêtes pour la PRÉ-RÉDUCTION."],
    '.X.': ['Données INUTILISABLES! Voir journal de post-réduction.'],
    '..L': ['Méthode de mesure par Lucky Imaging.'],
    '..I': ['Méthode de mesure par interférométrie des tavelures.']
}

# pour rech WDS (source seulement) formater src avec un espace entre découvreur et no
# alors len(src) <= WDS_SRC_LEN_NOTES
WDS_SRC_ESPACE_LEN = 1

# normalisation des noms de sources WDS à WDS_SRC_LEN_NOTES caractères
# longueur fixe du nom de la source pour recherche dans WDS Notes
# c.-à-d. len(découvreur + espaces + no ) == WDS_SRC_LEN_NOTES
WDS_SRC_LEN_NOTES = 7

# colonnes demandées pour recherche dans WDS
WDS_colonnes = ['WDS', 'Disc', 'Comp', 'Obs1', 'Obs2', 'Nobs', 'pa1', 'pa2', 'sep1', 'sep2', 'mag1', 'mag2', 'DM', 'Notes', 'n_RAJ2000',\
               'RAJ2000', 'DEJ2000', 'pmRA1', 'pmDE1']

# les fichiers maîtres calibration d'échelle, masques et filtres
# se trouvent toujours dans /med/cal_e/ relativement au répertoire d'exécution du script
# qui exploite  ce module
nom_fich_m_cal = 'master_calibrations_e.csv'
nom_fich_m_filtres = 'master_filtres_cal.csv'
nom_fich_m_masques = 'master_masques_cal.csv'

### pandas options d'affichage des tables
pd.set_option('display.expand_frame_repr', True)
pd.set_option('display.colheader_justify', 'right')
pd.set_option('display.max_colwidth', 50)
pd.set_option('display.max_column', 15)
pd.set_option('display.width', 200)
pd.set_option('display.max_row', 10000)
pd.set_option("display.precision", 6)
pd.set_option('display.max_rows', None)

# time scale and format for astropy Time objects
t_scale = 'utc'
t_format = 'isot'

# divers
NL = '\n'
# nom du fichier des mesures brutes produit lors de la post-réduction
fich_mesures_brutes = 'mesures_brutes.csv'
observatoires_df = None
resultatOK = True

# for tkinter
root = Tk()
root.wm_attributes('-topmost', 1)
root.withdraw()

# construire la liste de tri pour les listes
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

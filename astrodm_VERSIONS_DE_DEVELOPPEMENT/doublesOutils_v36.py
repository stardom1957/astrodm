# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 16:35:23 2020
version 35
Cette version est incompatibles avec les observations faites avec le Microguide

@author: Dominique Martel

Comprend diverses fonctionnalités pour planifier, réduire les observations
à partir des données d'acquisition d'étoiles doubles et de pré-réduction
produites par le logiciel REDUC (de Florent Losse) et produit également
diverses listes. 
"""

# %% imports et définition des constantes
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
from astroquery.vizier import Vizier as v
import re
from os import path
from tkinter import Tk
import os
import glob
import pickle

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
    ''' La classe AcquisitionSeparation étend la classe Acquisition avec ...'''
    def __init__(self, typeMesure):
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
    ''' La classe AcquisitionPosition étend la classe Acquisition avec ...'''
    def __init__(self, typeMesure):
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
    ''' La classe AcquisitionEchelle étend la classe Acquisition avec ...'''
    def __init__(self, typeMesure):
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
    La classe Reduction contient les données de base d'une réduction.
    '''
    def __init__(self):
        # nom complet fichier log réduction (produit par Reduc)
        # un pour pos et un pour sep
        # sera déterminé par fonction de sélection interactive des fichiers
        self.ncflr_sep = ''
        self.ncflr_pos = ''
        
        # bool indicateur delta matrix sep et pos valides
        self.deltaMatrixValide = False

        # mapEchelleValide indicateur de mise au point (map) valides entre sep et
        # les map correspondant à chacun des lstIndexCalE
        # mapReducValide indicateur que map sep == map lstIndexCalE correspondant
        self.mapEchelleValide, self.mapReducValide = False, False
        # validité de l'intervalle entre deux mesures d'échelles si elles
        # doivent servir pour la même réductions
        self.intervalleEchValide = False
        
        # valeur de la map de l'échelle utilisée dans la méthode calcule_rho
        # la valeur indiquée est toujours valide
        self.mapEchelle = 0

        # liste des index de calibration d'échelle
        self.lstIndexCalE = list()

        # mesures brutes dans Pandas dataframe éventuellement
        self.reduc_brute_df = ''

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
    
        Parameters
        ----------
         int noN numéro de la session en cour
         int noB no du bloc en cour
    
        Returns
        -------
        rien
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
    '''  La classe Bloc ...'''
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
        '''
        Valide les ...
        
        Parameters
        ----------
         int nsession numéro de la session en cour
    
        Returns
        -------
        rien
        '''
        # Récupérer les données de tous les index de calibration indiqués
        # dans le bloc d'observation

        # créer un df vide avec même structure que master_calibrations_e_df
        df = pd.DataFrame(data=None, index=None, columns=list(master_calibrations_e_df.keys()))

        # puis récupérer les informations de chaque index présent dans
        # self.reduc.lstIndexCalE dans df
        for idx_cal_e in self.reduc.lstIndexCalE:
            df = df.append(master_calibrations_e_df.\
                loc[master_calibrations_e_df.index_cal_e==idx_cal_e])
                
        # si df est vide, alors c'est probablement parce que la valeur de
        # l'index ne se situe pas dans master_calibrations_e_df
        
        if len(df) == 0:
            print("N{0} b{1} : index de calibration non trouvé(s) dans master_calibrations_e_df!".\
                  format(nsession, self.indexBloc))
            print("self.reduc.lstIndexCalE=",self.reduc.lstIndexCalE)
            sys.exit()

        #######################################################################
        # Validation 1 : map unique pour acquisitions échelle et sep
        #  valider si la/les** acquisition d'échelle dans df ont la même
        #  map que celle de sep du bloc courant
        #  ** S'il y a plus d'un index de calibration dans lstIndexCalE,
        # d'abord bâtir un set avec les valeurs et ajouter celle de sep
        # alors si len du set == 1, map est unique
        # sinon imprimer une alerte et arrêter
        
        tempo = set()
        #
        for idx in df.index:
            tempo.add(df.loc[idx, 'map'])
        # ajouter map de sep
        tempo.add(self.sep.map)
        
        if len(tempo) == 1:
            self.reduc.mapEchelle = tempo.pop()
            del tempo
            self.reduc.mapEchelleValide = True
        else:
            print("N{0} b{1}, cal_E : map non égales!".format(nsession, self.indexBloc),\
                  self.reduc.lstIndexCalE)
            sys.exit()

        #######################################
        # Validation 2 : intervalle de temps entre
        # la/les calibration d'échelle et de l'observation en cours.
        # Trouver tous les dt_obs_utc des échelles et celle de sep
        # valider si l'intervalle d'acquisition <= TEMPS_ENTRE_ACQUISITIONS
        # utiliser le «truc» des jours Juliens pour chaque date, trier la liste
        # et trouver intervalle entre première et dernière date
        
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
        if intervalle > TEMPS_ENTRE_ACQUISITIONS:
            print("N{0} b{1}, cal_E et sep : intervalle de temps entre obs > {2} min!".\
                  format(nsession, self.indexBloc, TEMPS_ENTRE_ACQUISITIONS))
            sys.exit()

        ##############################################
        # Validation 3 : intervalle de températures entre toutes les 
        # observations incluant acquisition d'échelle
        # valide si intervalle des temp_to <= DELTA_TEMPERATURE
        # imprimer une alerte et continuer

        listeTemp = list()
        for idx in df.index:
            listeTemp.append(df.loc[idx,'temp_to'])
        listeTemp.append(self.sep.temp_to)
        listeTemp.sort()
        intervalle = abs(listeTemp[0] - listeTemp[len(listeTemp)-1])

        if intervalle > DELTA_TEMPERATURE:
            print(NL)
            print('*'*50)
            print("AVERTISSEMENT!")
            print("  N{0} b{1}, : intervalle de température entre calibration et sep > {2}°!".\
                  format(nsession, self.indexBloc, DELTA_TEMPERATURE))
            print("Pour plus de détails, exécutez sessions.hier()")
            print('*'*50)
        

#
# Classe Observation
#
class Observation:
    ''' La classe Observations ... 
    noObs :: no de l'observation (N dans les rapports et structures)
    nbrBlocs :: nombre de blocs d'observations
    typeObservation :: 'ech' Échelle, ou 'complete' Complète (typeMesure 'pos' ou séparation 'sep')
    '''

    def __init__(self, noObs, typeObservation):
        self.N = noObs + 1
        self.tobs = typeObservation
        self.nb = 0

        # ces attributs seulements pour observation 'complete',
        self.cheminN = ''

        # liste des objets Blocs
        self.b = list()
        
    def ajouteBloc(self, no_bloc, type_obs):
        self.b.append(Bloc(no_bloc, type_obs))
        self.nb += 1
   

#
# Classe Systeme
#
class Systeme:
    """ Structure des informations d'un système d'étoiles doubles ou multiples.
    
        Un objet Systeme contient les informations de base d'un système. Le
        créateur prend en paramètre soit un dictionnaire ou soit le nom WDS
        du système et renseigne les champs à l'aide de recherches astroquery.
    """
    
    def __init__(self, cheminSysteme):
        """ Création d'un objet Systeme.
        
            Paramètres
        """
        # chemin du système
        self.rep = cheminSysteme
        
        # nom du système
        self.nom = path.basename(cheminSysteme)

        # nom complet du fichier info système
        self.ncfinfo_systeme =  cheminSysteme + '/' + self.nom + '_info_système.csv'
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
    et la paire concernés pour le programme d'observation.
    '''
    def __init__(self, typeObs='complete', chProg=''):
        # nombre de sessions d'observation (N)
        self.nbrN = 0
        
        # lstNs contiendra la liste des objets Observations
        self.N = list()

        
        if typeObs == 'complete':
            self.tobs = typeObs
            self.systeme = Systeme(path.dirname(path.dirname(chProg)))

            # nom de la paire
            self.paire = ''
            
            # programme d'observation
            self.prog = path.basename(chProg)
            
            # observations_df contient la liste de tous les blocs
            # d'observations
            # colonnes de observations_df
            lstCol = ['obs_prog', 'id_system', 'id_WDS', 'paire',\
             'const', 'N', 'bloc', 'obs_DH_UTC',\
             'obs_epoque_B', 'rho', 'rho_sigma', 'theta',\
             'theta_sigma', 'observatoire', 'observateur',\
             'transp', 'seeing', 'temp_to', 'humid',\
             'press_bar', 'map', 'eval_Q',\
             'lstIndexCalE', 'E_moy', 'filtre'
            ]
            
            # le dataframe observations_df contiendra les observations réduites
            # créer le df vide avec seulement les noms des colonnes
            self.observations_df = pd.DataFrame(list(), columns=lstCol)
            
            # sommaire_obs_df contient une seule ligne avec les valeurs moyennes
            # et autres renseignements pour le rapport des sessions

            # df des réductions complète des sessions
            self.sommaire_obs_df = None
            
            # moyennes des sessions d'observations
            self.rho_moy, self.theta_moy, self.epoque_moy = 0, 0, 0
            self.theta_sigma_moy, self.rho_sigma_moy = 0, 0
            
            # date de la dernière observation pour rapport des moyennes
            self.date_obs_n = None
            # date Obs2 dans WDS
            self.wds_Obs2 = ''
            
            # différence en jours entre première et dernière observation
            self.delai_entre_N = 0
            
            # état de la session, inscrire 'L' en position 3 pour 'Lucky imaging'
            # réfère à codes_etat_obs_dict
            # sera renseigné dans calcule_moyennes_sessions
            self.etat = list('  L')


    def cree_observations_df(self):
        '''
        Cette méthode crée le pd.dataframe observations_df qui contient le
        détail de toutes les observations.
    
        Parameters
        ----------
         aucun    

        Returns
        -------
         rien
        '''
        # pour chacun des N (observations)
    
        for obs in self.N:
            #print('Observation no. {0}'.format(obs.N))
            # pour chacun des bloc
            for b in obs.b:
                # produire un df avec les données
                # prog_obs, system, id_wds, paire, const, N, b, dt_obs_utc,\
                #    epoque, rho, rho_sigma, pos, pos_sigma
                
                lstChamps = [\
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
                         b.pos.eval_Q,
                         b.reduc.lstIndexCalE,
                         b.reduc.E_moy,
                         'filtre'
                         ]
                self.observations_df.loc[self.observations_df.index.size] = lstChamps


    def calcule_moyennes_sessions(self):
        '''
        Produit un rapport concis à partir de self.observations_df  dans
        sommaire_obs_df.
        
        sommaire_obs_df sera utilisé pour le sommaire final des 
        observations aussi bien dans le Jupyter notebook des observations que dans 
        le module listeReductions.
    
        Parameters
        ----------
         aucun    

        Returns
        -------
         rien
        '''

        # calculer
        # rho_moy, theta_moy et leurs incertitudes

        # nombre de lignes dans observations_df
        i = self.observations_df.index.size

        self.rho_moy    = self.observations_df.loc[range(0,i),'rho'].mean()
        self.theta_moy  = self.observations_df.loc[range(0,i),'theta'].mean()
        self.epoque_moy = self.observations_df.loc[range(0,i),'obs_epoque_B'].mean()
        self.date_obs_n = self.observations_df.loc[i-1,'obs_DH_UTC'].split('T')[0]
        
        # calculer différence en jours (int) entre première et dernière observation
        str_dt1 = self.observations_df.loc[i-1,'obs_DH_UTC']
        str_dt2 = self.observations_df.loc[0,'obs_DH_UTC']
        self.delai_entre_N = int(diff_dt(str_dt1, str_dt2).value)

        # recherche id WDS de la source et paire
        result_rech_WDS = rech_wds(self.systeme.nom, self.paire)
        # Obs2, pa2 et sep2 == année et valeurs dernière observation listées dans WDS 
        self.wds_Obs2 = result_rech_WDS[0]['Obs2'].item()
        self.wds_pa2 = result_rech_WDS[0]['pa2'].item()
        self.wds_sep2 = result_rech_WDS[0]['sep2'].item()
        
        # propagation des incertitudes theta_sigma
        tempo = 0
        for val in self.observations_df.loc[range(0,i),'theta_sigma']:
            tempo += math.pow(val, 2)
        self.theta_sigma_moy = math.sqrt(tempo) / i

        # propagation des incertitudes rho_sigma
        tempo = 0
        for val in self.observations_df.loc[range(0,i),'rho_sigma']:
            tempo += math.pow(val, 2)
        self.rho_sigma_moy = math.sqrt(tempo) / i
        
        #
        # produire sommaire_obs_df avec ces résultats
        #
            
        # colonnes de sommaire_obs_df
        lstCol = ['prog', 'id_system', 'pr',\
        'con', 'N', 'dern_obs_utc', 'delai', 'epoque',\
        'pa', 'pa_sig', 'sep', 'sep_sig',\
        'WDS_o2', 'WDS_pa2', 'WDS_sep2',\
        'État'
        ]
        
        # déterminer code de suivi dans etat
        # réfère à codes_etat_obs_dict
        # si on arrive à ce point, alors seulement vérifier le nombre de sessions
        # d'observations self.nbrN
        
        # 'C' == en cours par défaut
        self.etat[0] = 'C'
        
        if self.nbrN >= 2:
            # terminée
            self.etat[0] = 'T'
        
        # produite une chaîne avec les codes d'état
        strEtat = ''
        for i in range(0, len(self.etat)):
            strEtat += self.etat[i]
           
        lstData = [
           self.prog,\
           self.systeme.nom,\
           self.paire,\
           self.systeme.informations_df.loc[0,'const'],\
           self.nbrN,\
           self.date_obs_n,\
           self.delai_entre_N,\
           self.epoque_moy,\
           self.theta_moy,\
           self.theta_sigma_moy,\
           self.rho_moy,\
           self.rho_sigma_moy,\
           self.wds_Obs2,\
           self.wds_pa2,\
           self.wds_sep2,\
           strEtat
        ]
        self.sommaire_obs_df = pd.DataFrame(list(), columns=lstCol)
        self.sommaire_obs_df.loc[self.sommaire_obs_df.index.size] = lstData
        

    def imprimeRapport(self, typeRapport='m'):
        '''
        La méthode rapport ...
    
        Parameters
        ----------
         DoubleSessions ses
         String typeRapport
           l : listes
           c : données complète des sessions
           m : moyennes des sessions
    
        Returns
        -------
         rien
        '''
        pd.set_option('display.expand_frame_repr', True)
        pd.set_option('display.colheader_justify', 'right')
        pd.set_option('display.max_colwidth', 50)
        pd.set_option('display.max_column', 30)
        pd.set_option('display.width', 100)
        pd.set_option("precision", 4)
        i = self.observations_df.index.size


        # 'm' == moyenne de toutes les observations et leurs blocs
        #
        if typeRapport == 'm':
            print(NL)
            print("RÉSULTATS D'OBSERVATIONS")
            print('-'*pd.get_option('display.width'))
            print(self.sommaire_obs_df)
            print('-'*pd.get_option('display.width'))
            print(NL)
            for code in codes_etat_obs_dict:
                print(' ', code, codes_etat_obs_dict[code])
        


        # 'l' == sommaire de toutes les observations et leurs blocs
        # seulement pour impression, pas de structure de données créée
        if typeRapport == 'l':
            print(NL)
            #debug print('#'*25)
            print("LISTE DES OBSERVATIONS")
            #debug print('#'*25)
            print("RÉDUCTION COMPLÈTE")
            
            # en-tête des sessions
            print('-'*100)
            print(self.systeme.informations_df.to_string(index=False))
            #print(self.systeme.informations_df)
            #print(NL)
            print('-'*100)
            print("    Paire : {0}".format(self.paire))
            print("Programme : {0}".format(self.prog))
            print('-'*100)
            
            # pour chacun des N (observations)
            # on désire imprimer les champs suivants :
            lstChamps = [\
                         'N',\
                         'bloc',\
                         'obs_DH_UTC',\
                         'obs_epoque_B',\
                         'theta',\
                         'theta_sigma',\
                         'rho',\
                         'rho_sigma',\
                         'temp_to',\
                         'map',\
                         'lstIndexCalE',\
                         'E_moy',\
                         'eval_Q'
                         ]
            print(self.observations_df.loc[range(0,i), lstChamps].to_string(\
                index=True,\
                max_colwidth=25,
                line_width=100,
                justify='right'
                ))
            #print(self.observations_df.loc[range(0,i), lstChamps])
            
        # 'c' == toutes les données de toutes les observations et leurs blocs
        # seulement pour impression, pas de structure de données créée
        if typeRapport == 'c':
            print(NL)
            print("LISTE DES OBSERVATIONS")
            print("RÉDUCTION COMPLÈTE")
            
            # en-tête des sessions
            print('-'*100)
            print(self.systeme.informations_df.to_string(index=False))
            print('-'*100)
            print("    Paire : {0}".format(self.paire))
            print("Programme : {0}".format(self.prog))
            print('-'*100)
            print(self.observations_df)

            
    def hier(self, sortie='terminal'):
        '''
        Méthode qui liste la hiérarchie complète de l'objet DoubleSessions (self)
    
        Parameters
        ----------
         String sortie
          par défaut dans terminal, sinon
          liste dans ./out.txt (avec écrasement du contenu si fichier présent)
    
        Returns
        -------
         Hiérarchie complète de l'objet DoubleSessions (self).
        
        '''
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
        print(self.sommaire_obs_df)
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
                    print('  bloc {0}'.format(obs.b[b].indexBloc+1))
                    print('    ' + '#' * 14)
                    for key in obs.b[b].__dict__.keys():
                        print("        {0} = {1}".format(key, obs.b[b].__dict__[key]))
                        if key == 'ech':
                            for key2 in obs.b[b].__dict__[key].__dict__.keys():
                                print("{0}{1} = {2}".format(' '*12, key2, obs.b[b].__dict__[key].__dict__[key2]))
                        if key == 'reduc':
                            for key2 in obs.b[b].__dict__[key].__dict__.keys():
                                print("{0}{1} = {2}".format(' '*12, key2, obs.b[b].__dict__[key].__dict__[key2]))
        
                print('\r')
            
            if obs.tobs == 'complete':
                for b in range(obs.nb):
                    print(NL)
                    print('        ' + '#' * 14)
                    print('         Obs {0}, bloc {1}'.format(obs.N, obs.b[b].indexBloc))
                    print('        ' + '#' * 14)
                    print('\r')
                    for key in obs.b[b].__dict__.keys():
                        print("        {0} = {1}".format(key, obs.b[b].__dict__[key]))
                        if key == 'sep':
                            for key2 in obs.b[b].__dict__[key].__dict__.keys():
                                print("{0}{1} = {2}".format(' '*12, key2, obs.b[b].__dict__[key].__dict__[key2]))
                        if key == 'pos':
                            for key2 in obs.b[b].__dict__[key].__dict__.keys():
                                print("{0}{1} = {2}".format(' '*12, key2, obs.b[b].__dict__[key].__dict__[key2]))
                        if key == 'reduc':
                            for key2 in obs.b[b].__dict__[key].__dict__.keys():
                                if 'reduc_brute_df' in key2:
                                    print('reduc_brute_df :')
                                    print(obs.b[b].__dict__[key].__dict__[key2])
                                else:
                                    print("{0}{1} = {2}".format(' '*12, key2, obs.b[b].__dict__[key].__dict__[key2]))
                                
                print('\r')
                
        if sortie.upper() == 'FICHIER':
            f.close()
            sys.stdout = ancien_stdout


            
# %% FONCTIONS
def version():
    print(__name__ + ' ' + str(no_version) + ', janvier 2022')

def reduction(type_observation, cheminDeTeteProgramme):
    '''
    Effectue la réduction appropriée selon le type d'observation et le chemin
    passés en paramètres.

    Parameters
    ----------
     String type_observation
       'ech' == échelle
       'complete' == complète
     String cheminDeTeteProgramme

    Returns
    -------
     Retourne objet Observations ou DoubleSessions selon le cas
    '''
    #global fich_mesures_brutes
    # fichier des mesures brutes écrit dans chaque dossier reduc
    #fich_mesures_brutes = 'mesures_brutes.csv'
    
    # type d'observation échelle 'ech' ou complète 'complete'

    ################
    # Tronc commun #
    ################

    # lire les fichiers de support (maîtres de calibrations, etc)
    # et placer dans master_calibrations_e_df, master_filtres_cal_df, master_masques_cal_df
    lireFichiersSupport(type_observation, cheminDeTeteProgramme)
    
    ###############################
    # Réduction pour le calcul de
    # l'échelle E et E_sigma
    ###############################

    if type_observation == 'ech':
        # créer la liste des observations selon type_observation
        # créer l'objet sessions
        # (pas d'objet Systeme)

        lstObservations, n = creeLstObjObservations(type_observation, cheminDeTeteProgramme)
        # n == 0 dans ce cas
        
        # Il n'y a pas de boucle puisqu'il n'y a pas de N et la notion de bloc
        # est intégrée dans le nom de dossier d'acquisition (par ex. 2020-10-08b01).
        # Extraire les données du log d'acquisition et d'environnement, puis
        # comme pour le type e mesure 'sep', extraction et exportation (dans un autre csv)
        # des mesures brutes à partir du log de REDUC
        
        observation = lstObservations[0]
        extrait_Log_acq_env(observation, 1, 'sep')
        extrait_mesure_brutes_logReduc(observation, 1, 'sep')
        
        # lecture des mesures brutes dans un dataframe Pandas
        observation.b[0].reduc.relecture_mes_brutes(path.dirname(observation.b[0].reduc.ncflr_sep) +\
                                              '/' + fich_mesures_brutes)
        
        # passer LfplusDf, LfplusDf_sigma, Lo et Lo_sigma pour le calcul de Z
        observation.b[0].reduc.calcule_Z(\
           observation.b[0].reduc.LfplusDf,\
           observation.b[0].reduc.LfplusDf_sigma,\
           observation.b[0].reduc.Lo,\
           observation.b[0].reduc.Lo_sigma\
        )
        observation.b[0].reduc.calcule_E()
        imprime_rapport_E(observation)
        maj_master_calibrations(observation)
        return observation

    ######################
    # Réduction complète #
    ######################

    if type_observation == 'complete':
        # Dans ce cas, cheminDeTeteProgramme doit être dossier du type P2021-023 et avoir
        # au moins un N avec au moins un bloc d'observation. On doit bâtir un
        # objet doublesOutuils.DoubleSessions.
        #

        ###################################################
        # créer l'objet sessions
        ###################################################
        # Dans l'objet sessions, l'objet Systeme sera créé à partir du chemin du système.
        # Remonter au dossier du système à partir du dossier de cheminDeTeteProgramme
        # par «STTA254» dans D:\DOCUMENTS\Astronomie\dev\STTA254\AB\P2021-023

        sessions = DoubleSessions(typeObs=type_observation, chProg=cheminDeTeteProgramme)
            
        # nom de la paire dans sessions
        sessions.paire = path.basename(path.dirname(cheminDeTeteProgramme))

        # créer la liste des observations de sessions selon type_observation
        # le nombre de N sera placé dans sessions.nbrN
        sessions.N,  sessions.nbrN = creeLstObjObservations(type_observation,\
                                                          cheminDeTeteProgramme, sessions.systeme.nom)

        
        ######################################################################
        # boucle de réduction complète pour toutes les blocs d'observations  #
        ######################################################################

        for obs in sessions.N:
            for bloc in obs.b:
                # lire et extraire données du log d'acquisition et environnement sep
                extrait_Log_acq_env(obs, bloc.indexBloc, 'sep')
                
                #################################################
                #                 Réduction de sep
                #################################################
                extrait_mesure_brutes_logReduc(obs, bloc.indexBloc, 'sep')

                # relecture du fichier des mesures brutes sep dans un dataframe Pandas
                bloc.reduc.relecture_mes_brutes(path.dirname(bloc.reduc.ncflr_sep) +\
                                              '/' + fich_mesures_brutes)
                

                ####################################
                # validations générales pour sep
                ####################################
                bloc.validations(obs.N)

                ####################################
                # Calculs pour sep
                ####################################
                bloc.reduc.calcule_rho(obs.N, bloc.indexBloc)
                
                if bloc.reduc.mapEchelle != bloc.sep.map:
                    print('Observation no. {0}, bloc {1} :'.\
                          format(obs.N, bloc.indexBloc))
                    print("   La map d'échelle est différente de la map de l'acquisition sep :")
                    print("     map Échelle {0}, map acq sep {1}".\
                          format(bloc.reduc.mapEchelle, bloc.sep.map))
                    sys.exit()
                else:
                    bloc.reduc.mapReducValide = True
                
                ################################################
                #        traitement de pos
                ################################################
                extrait_Log_acq_env(obs, bloc.indexBloc, 'pos')
                
                #################################################
                #                 Réduction de pos
                #################################################
                extrait_mesure_brutes_logReduc(obs, bloc.indexBloc, 'pos')

                #################################################
                # VALIDATIONS delta matrice
                #################################################

                # delta matrix :
                #  RAPPEL : La valeur de theta est lue dans le log reduc de sep.
                #  Dans Reduc de sep, cette valeur est calculée à partir de delta_matrice_sep
                #  qui DOIT être copiée par l'usager à partir du Reduc de pos correspondant.
                #  Afin de vérifier si cette étape a été faite correstement, on 
                #  vérifie si delta_matrice_sep == delta_matrice_pos.
                 
                # Vérifier delta matrix
                if bloc.reduc.delta_matrix_sep == bloc.reduc.delta_matrix_pos:
                    bloc.reduc.deltaMatrixValide = True
                else:
                    print('Observation no. {0}, bloc {1} :'.\
                          format(obs.N, bloc.indexBloc))
                    print("   Le delta matrix de sep est différent de delta matrix de pos")
                    print("     delta matrix de sep {0}, delta matrix de pos {1}".\
                          format(bloc.reduc.delta_matrix_sep, bloc.reduc.delta_matrix_pos))
        
        # % création de observations_df
        # dans objet DoubleSessions.observations_df
        sessions.cree_observations_df()
        sessions.calcule_moyennes_sessions()

        #################################################
        #        SOMMAIRE DES OBSERVATIONS
        #################################################
        # rapport liste
        sessions.imprimeRapport('l')
        # rapport moyennes
        sessions.imprimeRapport('m')
        
        # sauvegarder l'objet sessions dans le dossier de la paire
        tempo = cheminDeTeteProgramme + '/' + sessions.systeme.nom + '_' +\
                   sessions.paire + '_' + sessions.prog  + '_sessions.obj'

        filehandler = open(tempo, 'wb')
        pickle.dump(sessions, filehandler)
        filehandler.close()
        print('\nTraitement terminé. Sessions enregistrées dans')
        print(" «{0}»".format(tempo))
        print(NL)
        print("Pour plus de détails exécutez:")
        print("  sessions.imprimeRapport('c'), ou")
        print("  sessions.hier() ou sessions.hier('out') sortie -> out.txt")
        return sessions

def convertToFloat(strVal):
    try:
        return float(strVal)
    except ValueError:
        print("{0} --> conversion à float impossible.".format(strVal))
        sys.exit()


def trouverLogReduc(ch):
    '''
    Trouve le fichier log de réduction (REDUC) RLog_*.txt dans ch

    Parameters
    ----------
     ch chemin complet à parcourir

    Returns
    -------
     Le nom complet du log de réduction.
    
    '''
    for root, dirs, files in os.walk(ch):
        for name in files:
            if os.path.isfile(os.path.join(root, name)):
                if 'RLog_' in name:
                    return name
    return ''


def trouverLogsAetE(chemin, nomSysteme):
    '''
    Trouve le fichier log d'acquisition (txt) et environnement dans chemin

    Parameters
    ----------
     chemin String chemin complet à parcourir
     ns String nom du système (ex. 'STTA254')

    Returns
    -------
     Tuple : nom complet log d'acquition, nom complet fichier environnement
    
    '''
    fla = fle = ''
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


    assert fle != '', "Fichier «environnement.txt» absent!"
    assert fla != '', "Fichier log acquisition absent!"
    return (fla, fle)


def liste_blocs(ch):
    '''
    Parcourt ch et retourne la liste des bnn (chemins des rép des bloc d'observations)

    Parameters
    ----------
     ch chemin complet à parcourir

    Returns
    -------
     Une liste des chemins des répertoires des blocs d'observations.
    
    '''
    return glob.glob(ch + '/b*') 


def creeLstObjObservations(typeObs, cheminProgramme, nomSysteme=None):
    '''
    Crée l'objet Observations du type typeObs en parcourant chemin.

    Parameters
    ----------
     String typeObs
     String chemin chemin complet ...
     Systeme systeme

    Returns
    -------
     List() doublesOutils.Observation avec toutes les données pertinentes des blocs d'observations
     trouvés dans chemin.
     
     Int nombreDeN le nombre de répertoires N valides
    '''
    
    # liste des observations
    lstO = list()
    
    if typeObs == 'ech':
        #########################################
        # il s'agit d'une observation d'échelle
        #########################################

        '''
        Ce type d'observation ne comprend pas de dossiers N* et le dossier du type 2021-10-08b01
        représente un seul bloc d'observation d'échelle. Il faut donc créer un objet Observation
        avec N=1 et ensuite créer l'unique bloc de typeObservation='ech'
        '''
        lstO.append(Observation(1, 'ech')) # N=1
        lstO[0].ajouteBloc(0, 'ech') # nbrBlocs = noBloc = 1

        # rechercher le nom de l'index de calibration dans dossierDeTete
        # pattern de recherche pour la forme yyyy-mm-jjbnn (ex. 2021-11-08b02)
        str_re_pat = r'([0-9]{4}\-[0-9]{2}\-[0-9]{2}b[0-9]{2})'
        obj_pat = re.compile(str_re_pat)
        obj_match = obj_pat.search(cheminProgramme)
        
        # placer l'index de calibration dans l'objet Observation, bloc 1, objet AcquisitionEchelle
        lstO[0].b[0].reduc.lstIndexCalE.append(obj_match.group(0))

        # trouver les noms complets des des logs acquisition et environnement
        # d'abord trouver tous les *.txt dans dossierDeTete
        lstFichiersTxt = glob.glob(cheminProgramme + '/*.txt')
        for f in lstFichiersTxt:
            if 'environnement' in f:
                lstO[0].b[0].ech.ncfle = f
            else:
                # lire la première ligne de f et évaluer
                try:
                    with open(f) as fich:
                        line = next(fich).strip()
                        if 'FireCapture' in line:
                            lstO[0].b[0].ech.ncfla = f
                    fich.close()
                    #break
                except StopIteration:
                    pass

        # trouver nom complet fichier log réduction (ncflr)
        tempo = glob.glob(cheminProgramme + '/reduc/RLog_*.txt')
        assert len(tempo) == 1, "log de reduc absent dans " + cheminProgramme + '/reduc'
        lstO[0].b[0].reduc.ncflr_sep = tempo[0]
        return lstO, 0

    else:
        
        # type_observation = 'complete'
        # trouver tous les répertoires Nx dans cheminProgramme
        lstDesRepN = glob.glob(cheminProgramme + '/N*')
        if len(lstDesRepN) !=0:
            # parcourir les dossiers de session N*
            nombreDeN = 0
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
  
                # traiter tous les blocs
                if len(listeRepBlocs) !=0:
                    nombreDeN += 1
                    lstO.append(Observation(obs_N-1, 'complete'))

                    # chemin du répertoire Nx
                    lstO[obs_N-1].cheminN = ch_rep_session_N
                    
                    # nom du programme d'observations tiré du chemin du programme
                    #debug obs_prog = path.basename(path.dirname(cheminProgramme))
                    #debug lstO[obs_N-1].prog = path.basename(cheminProgramme)

                    for repBlocCourant in listeRepBlocs:
                        # récupérer le no du bloc
                        #debug print("Traitement de " + repBlocCourant)
                        noBlocCourant = int(path.basename(repBlocCourant).split('b')[1])
    
                        ################################
                        # préparation traitement de sep
                        ################################
                        # ajouter le bloc courant dans l'observation courante
                        lstO[obs_N-1].ajouteBloc(noBlocCourant, 'complete') # nbrBlocs = noBloc = 1
    
                        # déterminer le log d'acquisition et environnement
                        tempo = repBlocCourant + '/sep/'
                        t = trouverLogsAetE(tempo, nomSysteme)
                        lstO[obs_N-1].b[noBlocCourant-1].sep.ncfla =  t[0]
                        lstO[obs_N-1].b[noBlocCourant-1].sep.ncfle =  t[1]
                        
                        # déterminer log de réduction
                        tempo = repBlocCourant + '/sep/reduc'
                        lstO[obs_N-1].b[noBlocCourant-1].reduc.ncflr_sep =\
                            tempo + '/' + trouverLogReduc(tempo)
    
                        ################################
                        # préparation traitement de pos
                        ################################
                        # déterminer le log d'acquisition et environnement
                        tempo = repBlocCourant + '/pos/'
                        t = trouverLogsAetE(tempo, nomSysteme)
                        lstO[obs_N-1].b[noBlocCourant-1].pos.ncfla =  t[0]
                        lstO[obs_N-1].b[noBlocCourant-1].pos.ncfle =  t[1]
                        
                        # déterminer log de réduction
                        tempo = repBlocCourant + '/pos/reduc'
                        lstO[obs_N-1].b[noBlocCourant-1].reduc.ncflr_pos =\
                            tempo + '/' + trouverLogReduc(tempo)
                
        return lstO, nombreDeN


def extrait_Log_acq_env(obs, bloc, typeMesure):
    '''
    Pour le bloc courant, repère les fichiers .ncfa (acquisition) et ncfr (réduction) 
    et récupère diverses données dépendant du type de réduction ('ech' ou 'complete')
    et du types de mesure ('ech', 'sep' ou 'pos'). Également, le fichier environnement.txt
    .ncfle est lu et traité.

    S'il sagit d'une réduction d'échelle ('ech'), on en profite pour récupérer id_masque
    et id_filtre qui se trouvent dans environnement.txt.
    
    Les données sont colligées dans les objets Acquisition appropriés de l'objet Observation
    passé en paramètre.
    
    Note : dans le cas d'une réduction d'échelle ('ech') le type de mesure (.typeMesure) est
    toujours 'sep', N==1 et bloc==1.


    Parameters
    ----------
     obs : objet de classe Observation
     bloc : no du bloc traité
     typeMesure : 'pos' ou 'sep'

    Returns
    -------
     rien, mais les données se trouvent dans l'objet Observation passé en paramètre.
    '''

    # fle = nom complet du fichier log environnement
    if obs.tobs == 'ech':
        fle = obs.b[bloc-1].ech.ncfle

    if obs.tobs == 'complete':
        if typeMesure == 'pos':
            fle = obs.b[bloc-1].pos.ncfle
        if typeMesure == 'sep':
            fle = obs.b[bloc-1].sep.ncfle
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
                obs.b[bloc-1].ech.strIdMasque = (ligneForm.split('=')[1])

            # note d'acquisition dans sep
            if ('note=' in ligne) or ('note =' in ligne):
                tempo = (ligne.split('=')[1]).rstrip('\n')
                obs.b[bloc-1].ech.note = tempo

            # id_filtre
            ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
            if 'filtre=' in ligneForm:
                obs.b[bloc-1].ech.strIdFiltre = (ligneForm.split('=')[1])

            # 'map' mise au point
            ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
            if 'map=' in ligneForm:
                try:
                    obs.b[bloc-1].ech.map = int((ligneForm.split('=')[1]))
                except ValueError:
                    print('N{0}, b{1} ech : map doit être int!'.format(obs.N, bloc.indexBloc))
                    sys.exit()

            # 'temp_to' température du to
            ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
            if 'temp_to=' in ligneForm:
                obs.b[bloc-1].ech.temp_to = convertToFloat((ligneForm.split('=')[1]))

        if obs.tobs == 'complete':
            if typeMesure == 'sep':
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                # extraire le/les index de calibration
                if 'index_cal_e=' in ligneForm:
                    tempo = ligneForm.split('=')[1]
                    if tempo != '':
                        obs.b[bloc-1].reduc.lstIndexCalE = tempo.split(',')
                    else:
                        print("N{0}, b{1}, sep : index_cal_e est absent!".format(obs.N, bloc))
                        print("Exécutez sessions.hier() pour diagnostic.")
                        sys.exit()

                # 'map' mise au point
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'map=' in ligneForm:
                    try:
                        obs.b[bloc-1].sep.map = int((ligneForm.split('=')[1]))
                    except ValueError:
                        print('N{0}, b{1} sep : map doit être int!'.format(obs.N, bloc.indexBloc))
                        sys.exit()

                # 'temp_to' température du to
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'temp_to=' in ligneForm:
                    obs.b[bloc-1].sep.temp_to = convertToFloat((ligneForm.split('=')[1]))

                # 'transp' transparance
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'transp=' in ligneForm:
                    obs.b[bloc-1].sep.transp = convertToFloat((ligneForm.split('=')[1]))

                # 'humid'
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'humid=' in ligneForm:
                    obs.b[bloc-1].sep.humid = convertToFloat((ligneForm.split('=')[1]))

                # 'press_bar' pression barométrique
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'press_bar=' in ligneForm:
                    obs.b[bloc-1].sep.press_bar = convertToFloat((ligneForm.split('=')[1]))

                # seeing
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'seeing=' in ligneForm:
                    obs.b[bloc-1].sep.seeing = (ligneForm.split('=')[1])

                # id_filtre
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'filtre=' in ligneForm:
                    obs.b[bloc-1].sep.strIdFiltre = (ligneForm.split('=')[1])

            if typeMesure == 'pos':
                ligneForm = ligne.replace(' ', '').rstrip('\n')
                # le log d'environnement de pos contient l'évaluation du quadrant de pos
                if 'eval_quadrant=' in ligneForm.lower():
                    obs.b[bloc-1].pos.eval_Q = (ligneForm.split('=')[1]).upper()

                # 'map' mise au point
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'map=' in ligneForm:
                    try:
                        obs.b[bloc-1].pos.map = int((ligneForm.split('=')[1]))
                    except ValueError:
                        print('N{0}, b{1} pos : map doit être int!'.format(obs.N, bloc.indexBloc))
                        sys.exit()

                # 'temp_to' température du to
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'temp_to=' in ligneForm:
                    obs.b[bloc-1].pos.temp_to = convertToFloat((ligneForm.split('=')[1]))

                # 'transp' transparance
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'transp=' in ligneForm:
                    obs.b[bloc-1].pos.transp = convertToFloat((ligneForm.split('=')[1]))

                # 'humid'
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'humid=' in ligneForm:
                    obs.b[bloc-1].pos.humid = convertToFloat((ligneForm.split('=')[1]))

                # 'press_bar' pression barométrique
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'press_bar=' in ligneForm:
                    obs.b[bloc-1].pos.press_bar = convertToFloat((ligneForm.split('=')[1]))

                # seeing
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'seeing=' in ligneForm:
                    obs.b[bloc-1].pos.seeing = (ligneForm.split('=')[1])

                # id_filtre
                ligneForm = ligne.replace(' ', '').rstrip('\n').lower()
                if 'filtre=' in ligneForm:
                    obs.b[bloc-1].pos.strIdFiltre = (ligneForm.split('=')[1])
                
            # note d'environnement sep | pos
            if ('note=' in ligne) or ('note =' in ligne):
                tempo = (ligne.split('=')[1]).rstrip('\n')
                if typeMesure == 'sep':
                    obs.b[bloc-1].sep.note = tempo
                if typeMesure == 'pos':
                    obs.b[bloc-1].pos.note = tempo

            # remarques d'environnement sep | pos
            if ('remarques=' in ligne) or ('remarques =' in ligne):
                tempo = (ligne.split('=')[1]).rstrip('\n')
                if typeMesure == 'sep':
                    obs.b[bloc-1].sep.remarques = tempo
                if typeMesure == 'pos':
                    obs.b[bloc-1].pos.remarques = tempo
    
    ###########################################################
    # extraction des données dans le log d'acquisition
    ###########################################################
    #  fla = nom complet fichier log acquisition (FC)

    if obs.tobs == 'ech':
        # bloc == 0 toujours
        fla = obs.b[0].ech.ncfla
        with open(fla) as f:
            lignesLues = f.readlines()
        f.close()

        for ligne in lignesLues:
            # date UTC d'acquisition (en assumant que PC d'acquisition réglé sur UTC)
            if 'Date=' in ligne:
                obs.b[0].ech.date_utc_acq = (ligne.split('=')[1]).rstrip('\n')
        
            # heure UTC d'acquisition
            if 'Mid(UT)=' in ligne:
                obs.b[0].ech.heure_utc_acq = (ligne.split('=')[1]).rstrip('\n')

            # nombre d'images acquises
            if 'Limit=' in ligne:
                tempo = (ligne.split('=')[1]).rstrip('\n')
                if 'Frames' in tempo:
                    obs.b[0].ech.nbr_images_acq = tempo.split(' ')[0]
                elif 'Seconds' in tempo:
                    obs.b[0].ech.nbr_images_acq = 'interval de ' + tempo.split(' ')[0] + ' s'


    if obs.tobs == 'complete':
        b = bloc - 1
        if typeMesure == 'pos':
            fla = obs.b[b].pos.ncfla
            with open(fla) as f:
                lignesLues = f.readlines()
            f.close()

            for ligne in lignesLues:
                # date UTC d'acquisition (en assumant que PC d'acquisition réglé sur UTC)
                if 'Date=' in ligne:
                    obs.b[b].pos.date_utc_acq = (ligne.split('=')[1]).rstrip('\n')
            
                # heure UTC d'acquisition
                if 'Mid(UT)=' in ligne:
                    obs.b[b].pos.heure_utc_acq = (ligne.split('=')[1]).rstrip('\n')
        
                # nombre d'images acquises
                if 'Limit=' in ligne:
                    tempo = (ligne.split('=')[1]).rstrip('\n')
                    if 'Frames' in tempo:
                        obs.b[b].pos.nbr_images_acq = tempo.split(' ')[0]
                    elif 'Seconds' in tempo:
                        obs.b[b].pos.nbr_images_acq = 'interval de ' + tempo.split(' ')[0] + ' s'

        if typeMesure == 'sep':
            fla = obs.b[b].sep.ncfla
            with open(fla) as f:
                lignesLues = f.readlines()
            f.close()
    
            for ligne in lignesLues:
                # date UTC d'acquisition (en assumant que PC d'acquisition réglé sur UTC)
                if 'Date=' in ligne:
                    obs.b[b].sep.date_utc_acq = (ligne.split('=')[1]).rstrip('\n')
            
                # heure UTC d'acquisition
                if 'Mid(UT)=' in ligne:
                    obs.b[b].sep.heure_utc_acq = (ligne.split('=')[1]).rstrip('\n')
        
                # nombre d'images acquises
                if 'Limit=' in ligne:
                    tempo = (ligne.split('=')[1]).rstrip('\n')
                    if 'Frames' in tempo:
                        obs.b[b].sep.nbr_images_acq = tempo.split(' ')[0]
                    elif 'Seconds' in tempo:
                        obs.b[b].sep.nbr_images_acq = 'interval de ' + tempo.split(' ')[0] + ' s'

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
                                                   obs.b[0].ech.strIdMasque]
        assert info_masque_df.index.size == 1, "Erreur, zéro ou plus d'une occurence de " + \
            obs.b[0].ech.strIdMasque + ' dans master_masques_cal.csv'
    
        # rechercher les informations de id_filtre dans master_filtres_cal_df
        info_filtre_df = master_filtres_cal_df.loc[master_filtres_cal_df.id_filtre==\
                                                   obs.b[0].ech.strIdFiltre]
        
        # placer LfplusDf, LfplusDf_sigma, Lo et Lo_sigma dans reduc
        obs.b[0].reduc.LfplusDf = info_masque_df.loc[0, 'LfplusDf']
        obs.b[0].reduc.LfplusDf_sigma = info_masque_df.loc[0, 'LfplusDf_sigma']
        obs.b[0].reduc.Lo = info_filtre_df.loc[0,'Lo']
        obs.b[0].reduc.Lo_sigma = info_filtre_df.loc[0,'Lo_sigma']
        
        assert info_filtre_df.index.size == 1, "ech : Erreur, zéro ou plus d'une occurence de " + \
            obs.b[0].ech.strIdFiltre + ' dans master_filtre_cal.csv'
        assert obs.b[0].ech.temp_to != None, 'environnement ech temp_to requis'
        assert obs.b[0].ech.map != 0, 'environnement ech map requise!'

        # validation date et heure d'acquisition UTC
        d = obs.b[0].ech.date_utc_acq
        h = obs.b[0].ech.heure_utc_acq
        assert d != '', 'acq ech date_utc_acq requise'
        assert h != '', 'acq ech heure_utc_acq requise'

        # inscrire dt utc iso observation dans ...ech.dtime_utc_acq
        obs.b[0].ech.dtime_utc_acq = str_dt_isot_a_TimeIsot(date=d, heure=h)
        assert obs.b[0].ech.nbr_images_acq != 0,\
            'acq ech nombre images ou secondes acquises requis'

    if obs.tobs == 'complete':
        b = bloc - 1
        if typeMesure == 'sep':
            assert obs.b[b].sep.temp_to != None, 'environnement sep temp_to requis'
            assert obs.b[b].sep.map != 0, 'environnement sep map requise!'

            # validation date et heure d'acquisition UTC
            d = obs.b[b].sep.date_utc_acq
            h = obs.b[b].sep.heure_utc_acq
            assert d != '', 'acq sep date_utc_acq requise'
            assert h != '', 'acq sep heure_utc_acq requise'
            
            # inscrire dt utc iso observation dans ...ech.dtime_utc_acq
            obs.b[b].sep.dtime_utc_acq = str_dt_isot_a_TimeIsot(date=d, heure=h)

            assert obs.b[b].sep.nbr_images_acq != 0, 'acq sep nombre images ou secondes acquises requis'
        
            # vérifier qu'il y a au moins un index de calibration d'échelle
            assert len(obs.b[b].reduc.lstIndexCalE) !=0,\
                "Le fichier «" + obs.b[b].sep.ncfle +\
                    "» ne contient pas d'index de calibration d'échelle!"

        if typeMesure == 'pos':
            assert obs.b[b].pos.temp_to != None, 'N{0}, b{1} pos : environnement pos temp_to requis'.format(obs.N, b)
            assert obs.b[b].pos.map != 0, 'N{0}, b{1} pos : environnement pos map requise!'.format(obs.N, b)

            # validation date et heure d'acquisition UTC
            d = obs.b[b].pos.date_utc_acq
            h = obs.b[b].pos.heure_utc_acq
            assert  d != '', 'N{0}, b{1} pos : acq pos date_utc_acq requise'.format(obs.N, b)
            assert h != '', 'N{0}, b{1} pos : acq pos heure_utc_acq requise'.format(obs.N, b)
            # inscrire dt utc iso observation dans ...ech.dtime_utc_acq
            obs.b[b].pos.dtime_utc_acq = str_dt_isot_a_TimeIsot(date=d, heure=h)

            assert obs.b[b].pos.nbr_images_acq != 0,\
                'N{0}, b{1} pos : acq pos nombre images ou secondes acquises requis'.format(obs.N, b)
            assert obs.b[b].pos.eval_Q != '',\
                "N{0}, b{1} pos : environnement pos valeur de eval_Q requise!".format(obs.N, b)
    

def extrait_mesure_brutes_logReduc(obs, noBloc, typeMesure):
    '''
    Pour le bloc courant, repère le fichier Rlog*.txt produit par reduc et extrait les mesures
    brutes de la réduction dans un nouveau fichier csv.

    Les données sont colligées dans les objets Reduction appropriés de l'objet Observation
    passé en paramètre.
    
    Note : dans le cas d'une réduction d'échelle ('ech') le type de mesure (.typeMesure) est
    toujours 'sep', N==1 et noBloc==1.


    Parameters
    ----------
     obs : objet de classe Observation
     noBloc : no du bloc traité
     typeMesure : 'pos' ou 'sep'

    Returns
    -------
     Produit le fichier reduc_brut.csv dans le répertoire de réduction.
    '''
    
    ############################################################################
    # préparation du patron RE pour la recherche des nombres en point flottant
    # compilation par re
    str_patron_nombres = r'[0-9.]+'
    pn = re.compile(str_patron_nombres)

    # lecture du fichier log de REDUC approprié pour le type d'observation et mesure
    if (obs.tobs == 'ech') or (obs.tobs == 'complete' and typeMesure == 'sep'):
        ncflr = obs.b[noBloc-1].reduc.ncflr_sep
    else:
        ncflr = obs.b[noBloc-1].reduc.ncflr_pos

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
                
                
                obs.b[noBloc-1].reduc.theta = convertToFloat(strTousLesNombres[0])
                obs.b[noBloc-1].reduc.theta_sigma = convertToFloat(strTousLesNombres[1])

            # récupérer également Delta Matrix pour comparer éventuellement avec celui de pos correspondant
            if 'Delta Matrix :' in ligne:
                obs.b[noBloc-1].reduc.delta_matrix_sep =\
                    convertToFloat((ligne.split(':')[1].strip(' ')).rstrip('\n'))

        if obs.tobs == 'complete' and typeMesure == 'pos':
            # juste récupérer delta matrice pour comparer avec celle qu'on trouverra
            # dans le log d'acquisition de sep corresponant au même bloc
            if 'Delta Matrix :' in ligne:
                obs.b[noBloc-1].reduc.delta_matrix_pos =\
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
    


def calcule_rho_theta_moy():
    '''
    En vue du calcul de la séparation des étoiles, à partir de reduc_brute_df,
    calcule la distance entre chaque point et produit les statistiques descriptives des données.

    Parameters
    ----------
     aucun

    Returns
    -------
    rien
    '''
    print('Calcule de la séparation')
    pass


def maj_master_calibrations(data):
    '''
    Met à jour le fichier maître des calibrations.
        
    master_calibrations_e.csv est modifié uniquement dans le cadre de ce programme. Si index_cal_e
    existe déjà dans master_calibrations_e.csv, il s'agit d'une nouvelles réduction effectuée de nouveau
    avec les mêmes données de réduction produites par REDUC (donc un simple cas de double exécution). Afin de 
    permettre de refaire une réduction au besoin, il faut présenter l'usager avec les résultats de la présente
    réduction en même temps que celle trouvée dans master_calibrations_e.csv le même index_cal_e. L'usager
    devra alors décider laquelle des deux réductions il désire garder.

    Parameters
    ----------
     data : objet Acquisition
     
     Lecture du fichier cal_e\master_calibration.csv

    Returns
    -------
     Modifie le fichier maître des calibrations
    '''
    
    # vérifier si index_cal_e existe dans master_calibrations_e_df
    # si c'est le cas, demander à l'us de remplacer ou annuler
    
    # trouver le nombre d'occurences de index_cal_e dans master_calibrations_e_df et agir en conséquence
    df = master_calibrations_e_df.loc[master_calibrations_e_df.index_cal_e==\
                                      data.b[0].reduc.lstIndexCalE[0]]
    
    # préparer le nouvel enregistrement de master_calibrations_cal_df dans une liste
    enr_lst = [data.b[0].reduc.lstIndexCalE[0],\
               data.b[0].ech.dtime_utc_acq.value,\
               data.b[0].ech.temp_to,\
               data.b[0].ech.map,\
               data.b[0].reduc.E,\
               data.b[0].reduc.E_sigma, 'f',\
               data.b[0].ech.strIdMasque,\
               data.b[0].ech.strIdFiltre,\
               data.b[0].ech.note\
              ]

    if df.index.size == 0:
        # ok pas d'occurence on demande si on écrit les infos
        print(enr_lst)
        tempo = data.b[0].reduc.lstIndexCalE[0].split('\\')
        
        reponse = input('... Inscrire données précédentes de {0} dans {1} (o|n)? '\
                        .format(data.b[0].reduc.lstIndexCalE[0],\
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
        reponse = input('? (a|b|x) :').upper()
        
        if reponse == 'A':
            print('garder A :: fichier non modifié.\nFin du programme.')
            sys.exit()
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
            print("Écriture de {0} terminée!".format(nom_complet_fich_maitre_cal))

        else:
            print("Annulé par l'usager. Au revoir!")
            sys.exit()


    # si plus d'une occurence, alors on arrête tout et on laisse l'us corriger la situation    
    else:
        print("ERREUR, plus d'une occurence de " + data.b[0].reduc.lstIndexCalE[0] +\
              " sortie du programme." )
        sys.exit()
    
def imprime_rapport_E(obs):
    '''  Imprime rapport '''
    print("  RÉDUCTION POUR CALIBRATION D'ÉCHELLE")
    #l = len('Index de calibration : {0}\n'.format(index_cal_e))
    l = len('Index de calibration : {0}\n'.format(obs.b[0].reduc.lstIndexCalE[0]))
    print('#' * (l+3))
    print('# Index de calibration : {0} #'.format(obs.b[0].reduc.lstIndexCalE[0]))
    print('#' * (l+3))
    print(NL)

    l = 50
    print('COORDONNÉES DES CENTROÏDES ET DISTANCES (px)'.center(l))
    print('-' * l)
    print(obs.b[0].reduc.reduc_brute_df)
    
    l = 37
    print(NL * 2)
    print('STATISTIQUES DESCRIPTIVES'.center(l))
    print('-' * l)
    print('                dist_min : {0:>7.3f} px'.format(obs.b[0].reduc.dist_min))
    print('                dist_max : {0:>7.3f} px'.format(obs.b[0].reduc.dist_max))
    print('                dist_moy : {0:>7.3f} px'.format(obs.b[0].reduc.dist_moy))
    print('              écart type : {0:>7.3f} px'.format(obs.b[0].reduc.dist_sigma))
    print("nombre d'images retenues : {0:>2d} sur {1:s}\n".format(obs.b[0].reduc.n_data,\
                                                                  obs.b[0].ech.nbr_images_acq))
    
    print('E = {0:>4.4f} "/pix ± {1:>4.4f} "/pix'.format(obs.b[0].reduc.E, obs.b[0].reduc.E_sigma))



def imprime_rapport_C(sessions):
    print(NL)
    print('#'*25)
    print("SOMMAIRE DES OBSERVATIONS")
    print('#'*25)
    print("RAPPORT DE RÉDUCTION COMPLÈTE")
    for obs in sessions.N:
        print('Observation no. {0}'.format(obs.N))
        for bloc in obs.b:
            pass
    
    '''
    print('STATISTIQUES DESCRIPTIVES'.center(l))
    print('-' * l)
    print('                dist_min : {0:>7.3f} px'.format(dist_min))
    print('                dist_max : {0:>7.3f} px'.format(dist_max))
    print('                dist_moy : {0:>7.3f} px'.format(dist_moy))
    print('              écart type : {0:>7.3f} px'.format(dist_sigma))
    print("nombre d'images retenues : {0:>2d}\n".format(n_data))
    print('séparation ...')
    #print('E = {0:>4.4f} "/pix ± {1:>4.4f} "/pix'.format(E, E_sigma))
    '''

    
def diff_dt(dt1, dt2):
    '''
    retourne la différence absolue (intervalle) entre dt1 et dt2 en J.jj.

    Parameters
    ----------
     astropy.time.core.Time dt1
     astropy.time.core.Time dt2 ou;
     
     str dt1 (format isot)
     str dt2 (format isot)

    Returns
    -------
     différence entre dt2 et dt1
    '''
    if type(dt2) == str and type(dt1) == str:
        return abs(str_dt_isot_a_TimeIsot(dt=dt2) - str_dt_isot_a_TimeIsot(dt=dt1))
    else:
        return abs(dt2 - dt1)


def str_dh_a_str_isot(d, h):
    '''
    Produit une chaîne Time au format isot de astropy avec d et h
    Toutes les dates en UTC

    Parameters
    ----------
     string d date au format yyyymmdd
     string h heure au format hhmmss.sss

    Returns
    -------
     String date au format isot de astropy p. ex. «2021-10-08T22:22:31.258»
     
     
    '''
    assert d.isdigit(), 'seulement des car chiffres dans la date'
    if '.' in h:
        tempo = h.split('.')
        assert tempo[0].isdigit() and tempo[1].isdigit(), "seulement des car chiffres dans l'heure"
    else:
        assert h.isdigit(), "seulement des car chiffres dans l'heure"
    
    return d[0:4] + '-' + d[4:6] + '-' + d[6:8] +\
        'T' + h[0:2] + ':' + h[2:4] + ':' + h[4:]

def str_dt_isot_a_TimeIsot(date='', heure='', dt=None):
    '''
    Convertit date et heure UTC au format Time isot UTC.

    Parameters
    ----------
    String date au format 'aaaammjj'
    String heure au format 'hhmmss.sss'
    String dt isot

    Returns
    -------
     Un objet astropy.time.core.Time
    '''
    if dt == None:
        return Time(str_dh_a_str_isot(date, heure), format=t_format, scale=t_scale)
    else:
        return Time(dt, format=t_format, scale=t_scale)

def dt_isot_a_datetime(date_isot):
    '''
    Convertir date_isot en un objet datetime (UTC).

    Parameters
    ----------
    date_isot date au format isot par ex. '2020-11-08T23:48:00'
    
    Returns
    -------
    objet datetime
    '''
    pass

def creeDateHeureLocale(dhl):
    '''
    Convertir dhl en un objet datetime UTC aware.

    Parameters
    ----------
    dhl date au format iso par ex. '2020-11-08T23:48:00UTC-4'
    
    Returns
    -------
    objet datetime
    '''
    
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

def lire_fichier_observatoires():
    try:
        return pd.read_csv('D:/DOCUMENTS/Astronomie/dev/astrodm/observatoires.csv')
    except FileNotFoundError:
        print('doubleOutils.lireFichiersSupport :: fichier observatoires.csv non trouvé. Sortie programme.')
        sys.exit()


def lireFichiersSupport(typeObservation, ch):
    '''
        Lecture des fichiers maîtres de calibration,
        lecture fichiers filtres et masques si typeObservation 'ech',
        lecture fichier des observatoires
    '''
    global master_calibrations_e_df, master_filtres_cal_df, master_masques_cal_df

    global observatoires_df, nom_complet_fich_maitre_cal
    global ch_rep_cal
    
    # localisation des fichiers de supports
    global cheminDesSystemes
    if typeObservation == 'complete':
        cheminDesSystemes = path.dirname(path.dirname(path.dirname(ch)))
        ch_rep_cal = cheminDesSystemes + '/cal_e/'
    else:
        cheminDesSystemes = path.dirname(ch) + '/'
        ch_rep_cal = cheminDesSystemes

    # lire le fichier observatoires dans un df
    observatoires_df = lire_fichier_observatoires()

    
    # lire le fichier maître des calibrations
    nom_complet_fich_maitre_cal = ch_rep_cal + nom_fich_m_cal
    try:
        master_calibrations_e_df = pd.read_csv(nom_complet_fich_maitre_cal)
        # faire une copie dans nom_complet_fich_maitre_cal + '.bak'
        master_calibrations_e_df.to_csv(nom_complet_fich_maitre_cal + '.bak', index=False)
    except FileNotFoundError:
        print('doubleoutils.lireFichiersSupport :: fichier {0} NON trouvé.'.format(nom_complet_fich_maitre_cal))
        sys.exit()
    
    if typeObservation == 'ech':
        # lire les deux fichiers master filtres et masques dans des df
        fich_mfiltres = ch_rep_cal + nom_fich_m_filtres
        fich_mmasques = ch_rep_cal + nom_fich_m_masques

        try:
            master_filtres_cal_df = pd.read_csv(fich_mfiltres)
            #print('Fichier {0} trouvé.'.format(fich_mfiltres))
        except FileNotFoundError:
            print('Fichier {0} NON trouvé.'.format(fich_mfiltres))
            sys.exit()

        try:
            master_masques_cal_df = pd.read_csv(fich_mmasques)
            #print('Fichier {0} trouvé.'.format(fich_mmasques))
        except FileNotFoundError:
            print('Fichier {0} NON trouvé.'.format(fich_mmasques))
            sys.exit()


def norm_WDS_src(source):
    '''
    normaliser src avec un seul espace entre découvreur et no ssi len < 7

    Parameters
    ----------
    source : TYPE str
        La désignation de découvreur du système recherché.

    Returns
    -------
    TYPE string désignation normalisée.

    '''
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
    '''
    Recherche les notes au sujet de src dans les notes au WDS ('B/wds/notes'), si présentes.

    Parameters
    ----------
    source : TYPE str
        La désignation de découvreur du système recherché.

    Returns
    -------
    TYPE string désignation normalisée sur WDS_SRC_LEN_NOTES.

    '''
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
    
    # formater pour recherche WDS
    # si nécessaire, remplacer 4e car par '?', p. e. «stfa 60» devient «stf? 60»
    
    v.CACHE = False
    v.ROW_LIMIT = 120000 # au cas où ?
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
    nom_src_format_pour_notes = norm_WDS_src_notes(src)

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
    '''
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

    '''
    global bool_mode_interactif, bool_imprEn_tete, bool_imprDetails, bool_imprSommaire
    bool_mode_interactif = modei
    bool_imprEn_tete = impre
    bool_imprDetails = imprd
    bool_imprSommaire = imprs


# %% DÉFINITIONS
'''
Crée un dictionnaire des codes de notes pour les
observations d'étoiles doubles

Format sur 3 caractères, par ex. 'C L'
Position 1 : code de suivi {X, E, C, P ou T}
Position 2 : libre pour développement futur
Position 3 : code de méthode de mesure {L ou I}
'''
codes_etat_obs_dict = {
    'X..': ['Délais dépassé, à reprendre.'],
    'E..': ['Résultats erronés, réduction inutilisable.'],
    'C..': ["en cours d'observation."],
    'P..': ['en PLANIFICATION.'],
    'T..': ['Terminé. Réduction complète, avec N=2 recommandé.'],
    '?..': ["Aucun programme d'observation assigné."],
    '..L': ['mesure par Lucky Imaging.'],
    '..I': ['mesure par interférométrie des tavelures.']
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

# VALIDATIONS
# fonction de date et heure
# intervalle max entre deux acquisitions d'échelle en minutes
TEMPS_ENTRE_ACQUISITIONS = 120
DELTA_TEMPERATURE = 3

# divers
NL = '\n'
no_version = 35
fich_mesures_brutes = 'mesures_brutes.csv'

# for tkinter
global root
root = Tk()
root.wm_attributes('-topmost', 1)
root.withdraw()

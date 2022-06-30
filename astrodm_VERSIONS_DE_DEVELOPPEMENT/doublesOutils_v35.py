# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 16:35:23 2020
version 35
Cette version est incompatibles avec les observations faites avec le Microguide

@author: Dominique Martel
Produit un rapport des observations des mesures de séparation et
angle de position d'une paire d'étoiles doubles.

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
    '''
    '''
    
    def __init__(self, cheminSysteme):
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
            lstCol = ['obs_prog', 'id_source', 'id_WDS', 'paire',\
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
            
            # resultats_reductions_sessions_df contient une seule ligne avec les valeurs moyennes
            # et autres renseignements pour le rapport des sessions

            # df des réductions complète des sessions
            self.resultats_reductions_sessions_df = None
            
            # moyennes des sessions d'observations
            self.rho_moy, self.theta_moy, self.epoque_moy = 0, 0, 0
            self.theta_sigma_moy, self.rho_sigma_moy = 0, 0
            
            # date de la dernière observation pour rapport des moyennes
            self.date_obs_n = None
            # date Obs2 dans WDS
            self.wds_Obs2 = ''
            
            # différence en jours entre première et dernère observation
            self.delta_dt_N = 0
            
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
        resultats_reductions_sessions_df.
        
        resultats_reductions_sessions_df sera utilisé pour le sommaire final des 
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
        self.delta_dt_N = int(diff_dt(str_dt1, str_dt2).value)

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
        # produire resultats_reductions_sessions_df avec ces résultats
        #
            
        # colonnes de resultats_reductions_sessions_df
        lstCol = ['prog', 'source', 'pe',\
        'con', 'N', 'dern_obs_utc', 'delais', 'epoque',\
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
           self.delta_dt_N,\
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
        self.resultats_reductions_sessions_df = pd.DataFrame(list(), columns=lstCol)
        self.resultats_reductions_sessions_df.loc[self.resultats_reductions_sessions_df.index.size] = lstData
        

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
        pd.set_option('display.width', 140)
        pd.set_option("precision", 4)
        i = self.observations_df.index.size


        # 'm' == moyenne de toutes les observations et leurs blocs
        #
        if typeRapport == 'm':
            print(NL)
            print("RÉSULTAT")
            print('-'*pd.get_option('display.width'))
            print(self.resultats_reductions_sessions_df.to_string(index=False))
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
            print(self.observations_df.loc[range(0,i), lstChamps].to_string(index=False))
            
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

            
    def hier(self, mode='console'):
        '''
        Liste la hiérarchie complète de l'objet DoubleSessions
    
        Parameters
        ----------
         aucun
    
        Returns
        -------
         Hiérarchie dans stdout.
        
        '''
        if mode == 'out':
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
            
        for obs in self.N:
            print('#'*56)
            print('Observation no {0} de type «{1}», contenant {2} bloc{3}'.format(\
                         obs.N, obs.tobs, obs.nb, 's' if obs.nb > 1 else '') )
            print('Chemin {0} : '.format(obs.cheminN))
            print('#'*56)
            if obs.tobs == 'ech':
                for b in range(obs.nb):
                    print('    ' + '#' * 10)
                    print('    le bloc {0} comprend les objets suivants :'.format(obs.b[b].indexBloc+1))
                    print('    ' + '#' * 10)
                    for key in obs.b[b].__dict__.keys():
                        print("        {0} = {1}".format(key, obs.b[b].__dict__[key]))
                        if key == 'ech':
                            for key2 in obs.b[b].__dict__[key].__dict__.keys():
                                print("{0}{1} = {2}".format(' '*12, key2, obs.b[b].__dict__[key].__dict__[key2]))
                        if key == 'reduc':
                            for key2 in obs.b[b].__dict__[key].__dict__.keys():
                                print("{0}{1} = {2}".format(' '*12, key2, obs.b[b].__dict__[key].__dict__[key2]))
        
                print('\n')
            
            if obs.tobs == 'complete':
                for b in range(obs.nb):
                    print(NL)
                    print('    ' + '#' * 10)
                    print('    le bloc {0} comprend les objets suivants :'.format(obs.b[b].indexBloc))
                    print('    ' + '#' * 10)
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
                                
                print('\n')
                
        if mode == 'out':
            f.close()
            sys.stdout = ancien_stdout


            
# %% FONCTIONS
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


def lireFichiersSupport(typeObservation):
    '''
        Lecture des fichiers maîtres de calibration,
        lecture fichiers filtres et masques si typeObservation 'ech',
        lecture fichier des observatoires
    '''
    global master_calibrations_e_df, master_filtres_cal_df, master_masques_cal_df

    # c'est le temps de lire le fichier observatoires dans le réperoire du package astro_doubles
    global observatoires, nom_complet_fich_maitre_cal
    try:
        observatoires = pd.read_csv('D:/DOCUMENTS/Astronomie/dev/astrodm/observatoires.csv')
    except FileNotFoundError:
        print('doubleOutils.lireFichiersSupport :: fichier observatoires.csv non trouvé. Sortie programme.')
        sys.exit()

    
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
    'E..': ['Erreur irrécupérable ou résultats incorrects. P. e. mauvaise paire mesurée.'],
    'C..': ["en cours d'observation."],
    'P..': ['en cours de PLANIFICATION.'],
    'T..': ['Terminé. Réduction complète, avec N=2 recommandé. Observations complétées.'],
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

# fichiers maîtres calibration d'échelle, masques et filtres
ch_rep_cal = 'D:/DOCUMENTS/Astronomie/dev/cal_e/'
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

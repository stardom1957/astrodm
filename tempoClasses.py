# -*- coding: utf-8 -*-
"""
Created on Thu Dec 16 19:51:34 2021

@author: dominique
"""
class Observation:
    ''' La classe Observations ... '''
    def __init__(self, noObs, nbrBlocs):
        self.N = noObs
        self.nbrBlocs = nbrBlocs
        self.lstBlocs = list()
        print('debug constructeur de Observation.\n')
       
class Bloc:
    '''  La classe Bloc ...'''
    def __init__(self, noObs, noBloc):
        self.N = noObs
        self.bloc = noBloc
        print('debug constructeur de Bloc.\n')


class Acquisition:
    '''
    La classe Acquisition contient les données d'acquisition pour un bloc
    d'observation.
    '''
    def __init__(self, typeReduction, typeM):
        
        # no d'observation
        self.N = 0
        # no du bloc d'observations
        self.bloc = 0
        
        # type de mesure
        self.typeMesure = typeM

        # liste des index de calibration
        self.lstIndexCalE = list()
        
        if typeReduction == 'ech':
            # id du masque et filtre utilisés
            self.strIdMasque = self.strIdFiltre = ''
            # nom complet du fichier log d'acquisition
            self.ncfla = ''
            # nom complet du fichier environnement
            self.ncfle = ''

        ################################################
        # Données seulement pour une réduction complète
        ################################################

        if typeReduction == 'complete':
            # nom complet des fichiers log d'acquisition sep et pos
            self.ncfla_sep = ''
            self.ncfla_pos = ''
            
            # nom complet des fichiers log environnement
            self.ncfle_sep = ''
            self.ncfle_pos = ''

            # évaluation du quadrant si réduction de pos
            self.eval_Q = ''

        # 'temp_to' température du to
        self.strTemp_to = ''

        # date UTC d'acquisition (en assumant que PC d'acquisition réglé sur UTC)
        self.date_utc_acq = ''

        # heure UTC d'acquisition
        self.heure_utc_acq = ''
        
        # note d'acquisition sep et pos
        # sep utilisée aussi dans réductions d'échelle
        self.note_acq_sep = ''
        self.note_acq_pos = ''

        # nombre d'images acquises
        self.nbr_images_acq = ''

        # filtre (aucune calibration requise)
        self.strIdFiltre=''


    def format_pour_csv(self):
        return ', '.join((\
                       str(self.N), str(self.bloc),\
                       *self.lstIndexCalE,\
                       self.strTemp_to,\
                       self.date_utc_acq,\
                       self.heure_utc_acq,\
                       self.note_acq_sep,\
                       self.note_acq_pos,\
                       self.nbr_images_acq,\
                       self.eval_Q
                        ))

class Reduction:
    '''
    La classe Reduction contient les données de la réduction complète ou ech pour
    un bloc d'observation.
    '''
    def __init__(self, noObs, noBloc, typeReduction=None):
        # no d'observation
        self.N = noObs
        # no du bloc d'observations
        self.bloc = noBloc
        
        #
        # tronc commun de réduction 'ech' et 'complete'
        # séparation moyenne en px et statistiques descriptives
        self.sep_moy_px = ''
        self.sep_moy_px_sigma = ''
        self.typeReduc = typeReduction

        # mesures brutes dans Pandas dataframe éventuellement
        self.reduc_brute_df = ''
        
        if typeReduction == 'complete':
            
            # theta lu du log Reduc de sep
            self.strTheta = ''
            self.strTheta_sigma = ''
            
            # theta et sigma theta
            self.theta, self.theta_sygma  = 0, 0
    
            # Delta Matrix sep et pos
            self.strDelta_matrix_pos = ''
            self.strDelta_matrix_sep = ''
            
        if typeReduction == 'ech':
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

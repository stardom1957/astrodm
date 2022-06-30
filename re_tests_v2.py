# -*- coding: utf-8 -*-
"""
Created on Thu Nov  4 22:20:15 2021

@author: dominique

quelques params :
re.IGNORECASE

mots clés Google : 'python re examples'
"""
import sys

# insérer le chemin suivant dans sys.path pour trouver le package astrodm
if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesOutils_v31 as do

# insérer le chemin suivant dans sys.path pour trouver le package astrodm

date_iso = '2021-10-08T19:53:34UTC-4'
date_loc_acq = '20211008'
heure_loc_acq = '195334.816'
UTC_decallage = '-4'

# préparation de l'objet datetime dt_obs
dla_annee = date_loc_acq[0:4]
dla_mois  = date_loc_acq[4:6]
dla_jour  = date_loc_acq[6:8]

dla_heure = heure_loc_acq[0:2]
dla_min   = heure_loc_acq[2:4]

heure_div = heure_loc_acq[4:].split('.')

dla_sec   = heure_div[0]
dls_msec  = heure_div[1]

# utiliser la date au format iso datetime (local) d'acquisition
dt_loc_acq = do.creeDateHeureLocale(date_iso)


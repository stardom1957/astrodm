# -*- coding: utf-8 -*-
"""
Created on Thu Nov  4 22:20:15 2021

@author: dominique

quelques params :
re.IGNORECASE

mots clés Google : 'python re examples'
"""

#from datetime import timedelta, datetime, tzinfo, timezone
#from astropy import units as u
from astropy.time import Time
import sys

# insérer le chemin suivant dans sys.path pour trouver le package astrodm
if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesOutils as do

# time scale and format for astropy Time objects
t_scale = 'utc'
t_format = 'isot'

# %% PRINCIPAL
if __name__ == "__main__":

    date_utc_iso = '2021-09-29T22:43:22.487UTC'.rstrip('UTC')
    date_utc_acq = '20211008'
    heure_utc_acq = '235334.816'

    # à partir d'une date iso
    dt1_utc_obs = Time(date_utc_iso, format=t_format, scale=t_scale)

    # à partir d'une date et heure au format texte (du log de Firecapture)
    dt2_utc_obs = Time(do.dateh_a_isot(date_utc_acq, heure_utc_acq), format=t_format, scale=t_scale)
    
    print(dt1_utc_obs)
    print(dt2_utc_obs)
    
    # quelques essais
    # extraire l'année par ex
    print(dt2_utc_obs.value[0:4])
    # époque Besselienne (numpy.float64)
    print(dt1_utc_obs.byear)
    # époque Besselienne (en texte)
    print(dt1_utc_obs.byear_str)
    # époque B avec 4 décimales
    dt1_utc_obs.precision = 4
    print(dt1_utc_obs.byear)
    print(dt1_utc_obs.byear_str)
    
    ## Attention objet Time au format texte
    dt2_utc_obs.value
    # ne pas oublier d'ajouter t_scale au moment d'écrire dans un csv ou autre
    print(dt2_utc_obs.value + 'UTC')
    
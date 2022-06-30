# -*- coding: utf-8 -*-
"""
Created on Thu Nov  4 22:20:15 2021

@author: dominique

quelques params :
re.IGNORECASE

mots clés Google : 'python re examples'
"""

from datetime import timedelta, datetime, tzinfo, timezone
from astropy import units as u
from astropy.time import Time, TimezoneInfo

date_utc_iso = '2021-09-29T22:43:22.487UTC'
date_utc_acq = '20211008'
heure_utc_acq = '235334.816'

date_utc_iso = '2021-09-29T23:45:12.298UTC'

# diviser les secondes de heure_utc_acq en secondes microsecondes
tempo = heure_utc_acq[4:].split('.')
a_sec   = int(tempo[0])
a_msec  = int(tempo[1]) * 1000

# préparation de la date sous forme d'une liste
dls_lst = [int(date_utc_acq[0:4]), int(date_utc_acq[4:6]), int(date_utc_acq[6:8]),\
           int(heure_utc_acq[0:2]), int(heure_utc_acq[2:4]), a_sec, a_msec]

######################################
# datetime naïve (sans fuseau horaire)
######################################

# à partir de la liste
dt1_utc_obs_naive = datetime(*dls_lst)
print(dt1_utc_obs_naive.isoformat(timespec='microseconds'))

# à partir d'une date iso
dt2_utc_obs_naive = datetime.fromisoformat(date_utc_iso.split('UTC')[0])
print(dt2_utc_obs_naive.isoformat(timespec='microseconds'))

######################################
# datetime Aware (avec fuseau horaire)
######################################

# à partir de la liste
dt1_tz_obs_naive = datetime(*dls_lst)
print('\n')
print(dt1_tz_obs_naive.isoformat(timespec='microseconds'))

# à partir d'une date iso
dt2_tz_obs_naive = datetime.fromisoformat(date_utc_iso.split('UTC')[0])
print(dt2_tz_obs_naive.isoformat(timespec='microseconds'))

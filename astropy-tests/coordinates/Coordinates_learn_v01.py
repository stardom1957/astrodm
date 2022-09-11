# -*- coding: utf-8 -*-
"""
Created on Wed Dec  2 21:46:50 2020

@author: dominique
"""
#%% IMPORTS
from astropy import units as u
from astropy.coordinates import SkyCoord
import math
import numpy as np
from astropy.time import Time, TimezoneInfo, TimeEpochDate, TimeBesselianEpoch
from datetime import datetime

#%% FONCTIONS
def creeDateHeureLocal(dhl):
    decallageUTCdhl = int(dhl.rsplit('UTC')[1])
    utc_dhl = TimezoneInfo(utc_offset=decallageUTCdhl*u.hour)
    # enlever le UTC de la date
    tempo = dhl.split('U')[0]
    # convertir la date et heure en int (en utilisant list comprehension)
    
    lst_int_dhl = [int(i) for i in tempo.split('T')[0].split('-')]
    lst_int_heure_dhl = [int(i) for i in tempo.split('T')[1].split(':')]
    a = lst_int_dhl[0]
    m = lst_int_dhl[1]
    j = lst_int_dhl[2]
    h = lst_int_heure_dhl[0]
    mi = lst_int_heure_dhl[1]
    s = lst_int_heure_dhl[2]
    
    # créer un datetime qui contient l'information de fuseau horaire
    return datetime(a, m, j, h, mi, s, tzinfo=utc_dhl)
    

#%% SkyCoord
print('\n######### SKYCOORD\n')
c1 = SkyCoord(ra='22h29m10.3s', dec='+58d24m54.7s', frame='icrs')
c2 = SkyCoord('22h29m10.3s', '+58d24m54.7s', frame='icrs')
# conversion en chaîne
print('c2 en chaîne : ', c2.to_string('hmsdms'))

# ra en format hms
print('c1= ', c1)
print(c1.ra.hms)
print('c1.ra formaté : {0:>2.0f}h {1:>2.0f}m {2:>4.2f}s'.format(c1.ra.hms.h, c1.ra.hms.m, c1.ra.hms.s))

# dec
print('c2.dec en dms= ', c2.dec.dms)
print('c2.dec formaté : {0:>2.0f}° {1:>2.0f}m {2:>4.2f}"'.format(c2.dec.dms.d, c2.dec.dms.m, c2.dec.dms.s))


#%% quelques unités astropy.units
print('\n######### QUELQUES UNITÉS\n')
angle1 = 23.7*u.degree
print('{0} = {1} = {2}'.format(angle1, angle1.to(u.arcmin), angle1.to(u.arcsec)))
angle2 = 1*u.radian
print('{0} = {1} = {2}'.format(angle2, angle2.to(u.degree), angle1.to(u.arcsec)))
dist1 = 1*u.parsec
print('{0} = {1}'.format(dist1, dist1.to(u.lyr)))

# magnitudes
m1 = -1.1*u.mag
#m2 = -7.1*u.mag
m2 = u.Magnitude(-6.1)
deltam = abs((m1 - m2) * u.mag**-1 )
print('m1 = {0:>2.1f}, m2 = {1:2.1f} :: delta m = {2:>2.2f}'.format(m1, m2, deltam))
#print('différence de luminosité entre m1 et m2 = {0:>2.2f}'.format(2.512 * math.log10(abs(m2 / m1))))
deltal = math.pow(2.512, abs((m1 - m2)* u.mag**-1))
print('différence de luminosité entre m1 et m2 = {0:>2.2f}\n'.format(deltal))

#%% date et heure
'''
 Pour les objets date Time ne tiennent pas compte du fuseau horaire : le temps
 est UTC. Pour faire la conversion du temps local d'observation à la date Besselienne,
 il faut passer par un objet datetime, puis créer un objet Time qui convertit à
 UTC. le paramètre de format byear_str ou format = 'byear_str' donnent la date Besselienne.
'''
print('\n######### DATE ET HEURE\n')
strT1 = '2020-07-03T23:37:00UTC-5'
# créer un datetime qui contient l'information de fuseau horaire
dateHeure1_local = creeDateHeureLocal(strT1)

# créer un objet astropy.Time.Time qui convertit le datetime en UTC
dateHeure1_UTC = Time(dateHeure1_local)

print('dateHeure1_local = {0}'.format(dateHeure1_local))
print('dateHeure1_UTC = {0}\n'.format(dateHeure1_UTC))

strT2 = '2020-12-03T22:55:41UTC-4'
# créer un datetime qui contient l'information de fuseau horaire
dateHeure2_local = creeDateHeureLocal(strT2)

# créer un objet astropy.Time.Time qui convertit le datetime en UTC
dateHeure2_UTC = Time(dateHeure2_local)

print('dateHeure2_local = {0}'.format(dateHeure2_local))
print('dateHeure2_UTC = {0}\n'.format(dateHeure2_UTC))

#%% Époque Besselienne (string)
dateHeure1_UTC.format = 'byear_str'
# aussi dateHeure1_UTC.byear ou .byear_str
#dateHeure2_UTC.format = 'byear_str'
print('dateHeure1_UTC (Bessel) = {0}'.format(dateHeure1_UTC))
print('dateHeure2_UTC (Bessel) = {0}\n'.format(dateHeure2_UTC.byear_str))

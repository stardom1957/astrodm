# -*- coding: utf-8 -*-
"""
Created on Tue Feb  1 21:59:09 2022

@author: dominique
"""
import sys
import os
import matplotlib.pyplot as plt
import astropy.units as u
from pytz import timezone
from astropy.table import Table, QTable
from astropy.coordinates import EarthLocation, SkyCoord
from astropy.io import ascii
from astropy.time import Time, TimeDelta
from astroplan import Observer
from astroplan import FixedTarget
from astroplan.plots import plot_airmass
import pickle
from astroquery.vizier import Vizier as viz
import numpy as np

# insérer le chemin suivant dans sys.path pour trouver le package astrodm
if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesoutils as do

# %% DÉFINITIONS
# pour la recherche WDS
MAX_LIGNES = 5000

# %% FONCTIONS
def utc_a_local(dthUTC):
    """
    Retourne astropy.time.core.Time au format isot en local.
    
    Paramètres positionnel
    dthUTC -- astropy.time.core.Time UTC au format isot
    """
    
    # TODO éventuellement déterminer decallageUTC programmatiquement selon la
    # saison
    # decallageUTC = UTC-5 = différence UTC de 5 heures (en secondes)
    decallageUTC = 18000.0
    delta_timeUTC = TimeDelta(decallageUTC, format='sec')
    return (dthUTC - delta_timeUTC)

def locale_a_utc(dthLocale):
    """
    Retourne astropy.time.core.Time au format isot en UTC.
    
    Paramètres positionnel
    dthUTC -- astropy.time.core.Time locale au format isot
    """
    
    # TODO éventuellement déterminer decallageUTC programmatiquement selon la
    # saison
    # decallageUTC = UTC-5 = différence UTC de 5 heures (en secondes)
    decallageUTC = 18000.0
    delta_timeUTC = TimeDelta(decallageUTC, format='sec')
    return (dthLocale + delta_timeUTC)


def trouve_constellation(raj2000, dej2000):
        coord = SkyCoord(ra=raj2000, dec=dej2000, frame='icrs', unit=(u.hourangle, u.deg))
        return coord.get_constellation(short_name=True)


def rech_wds_zone(ra, dec):
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
    
    viz.CACHE = False
    viz.ROW_LIMIT = MAX_LIGNES
    
    ### soumettre la requête
    return viz.query_constraints(catalog='B/wds/wds',\
                                RAJ2000=ra, DEJ2000=dec)

    # variations avec critère Obs2
    #result = viz.query_constraints(catalog='B/wds/wds', Disc=source, Comp=paire, Obs2='<=2015')
    ##result = viz.query_constraints(catalog='B/wds/wds', Disc=source, Comp=paire, Obs2='2011..2015')



# %% PRINCIPAL

if __name__ == '__main__':
    
    ## TODO charger le fichier *.information.csv du système dans Pandas systeme_df
    
    #
    ## lire le fichier astrodm/observatoires.csv
    boolLireOK, observatoires_df = do.lire_fichier_observatoires()
    if not boolLireOK:
        print('fichier observatoires non trouvé')
        sys.exit()
        
    for idx in observatoires_df.index:
        if observatoires_df.loc[idx, 'nom_obs'] == 'Résidence':
            break
    #longitude = '-73d47m35.4s'
    #latitude = '+45d35m42.3s'
    #elevation = 45 * u.m
    lieu_observation = EarthLocation.from_geodetic(observatoires_df.loc[idx, 'obs_long'],\
                                           observatoires_df.loc[idx, 'obs_lat'],\
                                           observatoires_df.loc[idx, 'alt'])
    
    #
    ## TODO les valeurs d'environnement pourraient provenir d'un fichier csv
    #  situé dans astrodm/environnements, avec une série de valeurs pour chaque saison
    #
    observatoire = Observer(name=observatoires_df.loc[idx, 'nom_obs'],
                   location=lieu_observation,
                   pressure=0.615 * u.bar,
                   relative_humidity=0.50,
                   temperature=0 * u.deg_C,
                   timezone=timezone('US/Eastern'),
                   description="Site personnel, Laval, Québec, Canada")

    
    # heure lever et coucher du Soleil
    tm = Time.now()
    print("\n{0} :".format(observatoire.name))
    print(" Soleil :")
    print("    Lever : {0}UTC-5".format(utc_a_local(observatoire.sun_rise_time(tm, which='nearest')).isot.split('T')[1]))
    print("  Coucher : {0}UTC-5".format(utc_a_local(observatoire.sun_set_time(tm, which='nearest')).isot.split('T')[1]))

    #
    # recherche WDS
    #
    
    systeme = input('Nom du système : ')
    paire = '*'
    print('Paire = *')
    resultat_WDS = None
    if len(systeme) <= 7:
        resultat_WDS =do.rech_wds(systeme, paire)
        
    if len(resultat_WDS) != 0:
        res = resultat_WDS[0]
        str_ra = res['RAJ2000'].item(0)
        str_dec = res['DEJ2000'].item(0)
        nom_systeme = res['Disc'].item(0)
        # créer objet Skycoord
        coordonnees = SkyCoord(ra=str_ra, dec=str_dec, frame='icrs',\
                           unit=(u.hourangle, u.deg))

        #
        # Trouver la constellation à partir des coordonnées!!!
        #
        # NOTE coordonnees.to_string(style='hmsdms')
        print("\nLe système {0}{1} se trouve dans {2}.\n".\
              format(nom_systeme.replace(' ',''),\
                     paire.upper(),\
                     coordonnees.get_constellation(short_name=True)))
        
        cible = FixedTarget(name=nom_systeme, coord=coordonnees)
        dth_maintenant = Time(Time.now(), format='isot') # en utc
        print("{0}UTC = {1}UTC-5".format(dth_maintenant.isot, utc_a_local(dth_maintenant)))
    
        #
        # date observation locale à 5h UTC = 0h heure locale
        # l'heure se centrée sur le graphe de l'airmass
        #
        '''
        Il ne faut pas utiliser dth_observationLocale dans aucune méthode de
        calcul dans astropy.
        
        En effet, bien que nous considérions dth_observationLocale comme
        une dth locale pour le bien de l'affichage, en représentation interne,
        dans astropy, il s'agit d'une heure UTC.
        '''
        dth_observationLocale = Time('2022-02-22T23:59:59')
        dth_observationUTC = locale_a_utc(dth_observationLocale)
    
        print("\nDate observation {0}UTC = {1}UTC-5".\
              format(dth_observationUTC.isot, dth_observationLocale.isot))
        
        # observabilité de la cible
        print("\nObservabilité de {0}".format(systeme))
        plot_airmass(cible, observatoire, dth_observationUTC)
        plt.tight_layout()
        plt.show()
    else:
        print('\n«Système {0}» non trouvé dans WDS.'.format(systeme))

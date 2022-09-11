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
from astropy.time import Time
from astroplan import Observer
from astroplan import FixedTarget
from astroplan.plots import plot_airmass
import pickle
from astroquery.vizier import Vizier as viz
import numpy as np

# insérer le chemin suivant dans sys.path pour trouver le package astrodm
if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesOutils as do

# %% DÉFINITIONS
# pour la recherche WDS
MAX_LIGNES = 5000

# %% FONCTIONS

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
    viz.ROW_LIMIT = 200 # au cas où ?
    global strSource_format_pour_Notes
    # normaliser pour recherche WDS
    strSource = do.norm_WDS_src(src)
    
    # le cas échéant, remplacer 4e car alpha par '?'
    # split sur ' ' puisque strSource est normalisé avec un espace
    spl = strSource.split(' ')
    if len(spl[0]) == 4:
        strSource = spl[0][:3] + '? ' + spl[1]
    
    ### soumettre la requête
    #strSource = 'H 3*'
    #return viz.query_constraints(catalog='B/wds/wds', Disc=strSource, Comp=paire)
    #RA = '>= 00 49 06.29 and <= 00 55 00.00'
    #DE = '>= +57 48 54.7 and <= +62 00 00.0'
    RA = '>= 1.8 and <= 5.0'
    DE = '>= +55.0 and <= +64.0'

    return viz.query_constraints(catalog='B/wds/wds',\
                                RAJ2000=RA, DEJ2000=DE)

    # variations avec critère Obs2
    #result = viz.query_constraints(catalog='B/wds/wds', Disc=source, Comp=paire, Obs2='<=2015')
    ##result = viz.query_constraints(catalog='B/wds/wds', Disc=source, Comp=paire, Obs2='2011..2015')

# %% PRINCIPAL

if __name__ == '__main__':
    
    ## TODO charger le fichier *.information.csv du système dans Pandas systeme_df
    
    #
    ## lire le fichier astrodm/observatoires.csv
    observatoires_df = do.lire_fichier_observatoires()
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
    #
    # TODO éventuellement prendre les valeurs suivantes dans systeme_df?
    #
    str_ra = '00 01 15.85'
    str_dec = '+60 21 19.0'
    nom_systeme = 'STFA254'
    #coord = '05h14m32.27s -08d12m05.9s'
    #coordonnees = SkyCoord('05h14m32.27s', '-08d12m05.9s', frame='icrs')
    coordonnees = SkyCoord(ra=str_ra, dec=str_dec, frame='icrs',\
                           unit=(u.hourangle, u.deg))
    
    #
    # Trouver la constellation à partir des coordonnées!!!
    #
    print("\nLes coordonnées de {0} ({1}) se trouvent dans {2}.".\
          format(nom_systeme, coordonnees.to_string(style='hmsdms'),\
                 coordonnees.get_constellation(short_name=True)))
    cible = FixedTarget(name=nom_systeme, coord=coordonnees)
    
    # TODO time UTC vs local???
    # dth_observation en UTC :: heure locale est UTC-5
    # le graphique suivant sera centré sur cette dth
    dth_observation = Time('2022-02-10T00:00:00')
    local = do.UTCaHeureLocale(dth_observation.isot +'UTC-5')
    print(local.isoformat())
    
    # heure lever et coucher du Soleil
    print("Le {0}, le Soleil se lève à {1} et se couche à {2}.".format(\
        dth_observation.isot.split('T')[0],\
        observatoire.sun_rise_time(dth_observation, which='nearest').isot.split('T')[1],\
        observatoire.sun_set_time(dth_observation, which='nearest').isot.split('T')[1]))
    
    
    
    #plot_airmass(cible, observatoire, dth_observation)
    #plt.tight_layout()
    #plt.show()

    '''
    # conversion d'un pandas df à une table astropy
    # afin de bénéficier des description de colonnes (unités, entre autres)
    #
    # charger objet DoubleSessions
    with open(r'D:\DOCUMENTS\Astronomie\dev\med/STTA254\AB\P2021-023\STTA254_AB_P2021-023_sessions.obj', 'rb') as f:
        s = pickle.load(f)
    
    # et placer le df du sommaire des observations dans df
    df = s.sommaire_obs_df
    # maintenant transformer df en une astropy.table
    observations = QTable.from_pandas(df)
    observations.pprint_all()
    
    info_sys = do.rech_wds('stf60', 'ab')
    reductions_qt = QTable.from_pandas(do.\
        reduction('complete', 'D:\DOCUMENTS\Astronomie\dev\med\STTA254\AB\P2021-023').\
            sommaire_obs_df)
    
    #
    # checherches d'une zone rectangulaire du ciel dans WDS
    #
    
    # secteur d'And
    ra = '>= 22 02 and <= 23 59.9'
    dec = '>= +33 00 and <= +48 00'
    #RA = '>= 1.8 and <= 5.0'
    #DE = '>= +55.0 and <= +64.0'

    t = rech_wds_zone(ra, dec)[0]
    #print(t.colnames)
    print('\n')
    print("Il y a {0} résultats.\n".format(len(t)))
        
    # ajouter colonne constellation et trier sur ADJ2000 et DEJ2000
    t['Const'] = trouve_constellation(t['RAJ2000'], t['DEJ2000'])
    t.sort(keys=('RAJ2000', 'DEJ2000'))
    #t.pprint_all()
    
    # exporter dans un csv
    ascii.write(t, os.getcwd() + r'/out.csv', format='csv', overwrite=True)
    
    # pour filter
    const = 'Peg'
    mask = t['Const'] == const
    r = t[mask]
    r.pprint_all()
    print('\nIl y a {0} enregistrements dans {1}.'.format(len(r), const))
    '''
    

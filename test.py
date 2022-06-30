# -*- coding: utf-8 -*-
"""
Created on Sun Jan 10 10:52:06 2021

@author: dominique
"""

import sys
# insérer le chemin suivant dans sys.path pour trouver le package astro_doubles
if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesOutils_v30 as do

notes = {
    'X..': ['Délais dépassé, à reprendre.'],
    'E..': ['Erreur irrécupérable ou résultats incorrects. P. e. mauvaise paire mesurée.'],
    'C..': ["en cours d'observation."],
    'P..': ['en cours de PLANIFICATION.'],
    'T..': ['Terminé. Réduction complète, avec N=2 recommandé. Observations complétées.'],
    '..M': ['mesure par Microguide.'],
    'L': ['mesure par Lucky Imaging.'],
    '..A': ['mesure par autre méthode, voir fichier _observations.csv.']
}
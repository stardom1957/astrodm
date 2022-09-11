# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 13:46:15 2022

@author: dominique
"""

import sys
import math

# insérer le chemin suivant dans sys.path pour trouver le package astrodm
#if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
#    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
#from astrodm import doublesoutils as do

if __name__ == '__main__':
    """
    Retourne le temps de parcourt (en s) par dérive sidérale pour parcourir la
    distance distance pour un objet ayant une déclinaison d m s.
    
    Paramètres positionnels :
       'dist' int distance en secondes d'arc
       déclinaison de la cible :
         'd' degrées (par défaut 0)
         'm' arc min (par défaut 0)
         's' arc sec (par défaut 0)
    """
    
    m, s = 0, 0
    narg = len(sys.argv)
    if narg == 1:
        print("Calcul du temps de dérive selon la déclinaison.")
        print("Usage : python drive.py distance, d, [m], [s], [] = facultatif")
        sys.exit()
        
    print("Nombre d'arguments : {0}\n".format(narg))

    if narg >= 3:
        distance = float(sys.argv[1].strip(','))
        d = float(sys.argv[2].strip(','))
    else:
        print("Erreur distance ou déclinaison (degrés) non donnés!")
        sys.exit()

    if narg >= 4:
        m = float(sys.argv[3].strip(','))

    if narg == 5:
        s = float(sys.argv[4])
    
    # transformer d m s en notation décimale
    dms = d + (m / 60) + (s / 3600)
    print(" {0} °ms".format(dms))
    
    # constante 15.041084 arcsec par seconde de temps solaire moyen
    # à l'équateur céleste
    #
    temps = abs(distance / (15.041084 * math.cos(math.radians(dms))))
    print(" {0} s".format(temps))

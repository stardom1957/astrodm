# -*- coding: utf-8 -*-
"""
Created on Mon Jul  3 10:46:16 2023

@author: jcdma
"""

import re


def est_un_programme(chemin):
    """
      Retourne True ssi le nom du dernier répertoire du chemin passé en paramètre est
      formaté correctement comme un programme d'observation, par ex. 'P2022-004'.
      
      Par exemple, dans le chemin suivant 
      
     'D:\\DOCUMENTS\\Astronomie\\Data/med\\A   152\\AB\\P2022-020\\' ;
     
     les segments qui se trouvent à la suite de '/med', c.-à-d. : '\\A   152\\' et '\\AB\\'
     ont déjà été trouvés valides comme système et paire respectivement. Donc, le pattern
     'Paaaa-nnn' recherché doit obligatoirement se retrouver à la fin du chemin.
     
     Ici l'on cherche '\\P2022-004\\'
      
    Paramètre positionnel
     chemin -- chemin du répertoire à vérifier.
    """
    
    if not estNan(chemin):
        str_re_pattern = r'(/P[0-9]{4}-[0-9]{3}/)$'
        obj_pat = re.compile(str_re_pattern)
        res = obj_pat.search(chemin.replace('\\', '/'))
        return res is not None
    return False

def estNan(val):
    """ Cette comparaison permet de trouver si une variable contient NaN. """
    return val != val


if __name__ == '__main__':
    str1 = 'D:\\DOCUMENTS\\Astronomie\\Data/med\\A   152\\AB\\P2022-020\\'
    str2 = 'D:\\DOCUMENTS\\Astronomie\\Data/med\\A   152\\AB\\ P2022-020\\'
    str3 = 'D:\\DOCUMENTS\\Astronomie\\Data/med\\A   152\\AB\\ P2022-020P2022-020\\'
    str4 = 'D:\\DOCUMENTS\\Astronomie\\Data/med\\A   152\\AB\\P202-020\\'
    str5 = 'D:\\DOCUMENTS\\Astronomie\\Data/med\\A   152\\AB\\P202a-020\\'
    str6 = 'D:\\DOCUMENTS\\Astronomie\\Data/med\\A   152\\AB\\2022-020\\'
    str7 = ''
    print(est_un_programme(str1))
    print(est_un_programme(str2))
    print(est_un_programme(str3))
    print(est_un_programme(str4))
    print(est_un_programme(str5))
    print(est_un_programme(str6))
    print(est_un_programme(str7))

# -*- coding: utf-8 -*-
"""
Created on Sun Jan 10 10:52:06 2021

@author: dominique
"""
import re

def est_un_programme(chaine):
    '''
      Cette méthode vérifie si la chaine passée en paramètre est valide pour
      un programme d'observation.
      
    Parameters
    ----------
    String chaine :: nom du répertoire (basename) à vérifier.

    Returns
    -------
    
    True | False selon le cas
      
    '''
    #pattern = r'([A-Z]{2}\-[0-9]{2}\-[0-9]{2}b[0-9]{2})'
    #res = filter(re.compile(str_re_pattern).match, l[1])
    #obj_match = obj_pat.match(l[1])

    valide = False
    str_re_pattern = r'P[0-9]{4}-[0-9]{3}'
    obj_pat = re.compile(str_re_pattern)
    res = obj_pat.search(chaine)
    if res != None:
        if len(res.group(0)) == 9:
            valide = True
    return valide, res.group(0)


if __name__ == "__main__":
        
    l = [r'P2021-025',\
         r'D:\DOCUMENTS\Astronomie\dev\med\STF982\AB\P2021-003',\
         r'AC',\
         r'P54-05',\
         r'P2021-25',\
         r'P2021-045q']
    
    for r in l:
        boolP = est_un_programme(r)
        print("{0} {1}".format(boolP))
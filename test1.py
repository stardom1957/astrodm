# -*- coding: utf-8 -*-
"""
Created on Sun Jan 10 10:52:06 2021

@author: dominique
"""
import re

if __name__ == "__main__":
    t = ['D:\\DOCUMENTS\\Astronomie\\dev/med\\BU305\\A,BC',\
         'D:\\DOCUMENTS\\Astronomie\\dev/med\\BU305\\AB',\
         'D:\\DOCUMENTS\\Astronomie\\dev/med\\BU305\\AC',\
         'D:\\DOCUMENTS\\Astronomie\\dev/med\\BU305\\BU305_info_système.csv',\
         'D:\\DOCUMENTS\\Astronomie\\dev/med\\BU305\\NLP']
        
    l = ['A,BC',\
         '\\AB',\
         'AC',\
         'NLP']
    #pattern = r'([A-Z]{2}\-[0-9]{2}\-[0-9]{2}b[0-9]{2})'
    #res = filter(re.compile(str_re_pattern).match, l[1])
    #obj_match = obj_pat.match(l[1])

    str_re_pattern = r'[A-Z]{2}'
    obj_pat = re.compile(str_re_pattern)
    for p in l:
        if ',' not in p:
            res = obj_pat.search(p)
            if res != None:
                print('paire = {}'.format(res.group(0)))
            else:
                print('rien trouvé')
        else:
            print('paire = {}'.format(p))
    
    '''
    for ob in t:
        #res = filter(re.compile(str_re_pattern).match, ob)
        res = filter(re.compile(str_re_pattern).search, ob)
        #obj_match = obj_pat.match(ob)
        #if obj_match != None:
        #    res = obj_match.group(0)
        #    print(res)
        #else:
        print(res)
   '''
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 28 16:09:19 2022

@author: dominique
"""
import sys
# %% FONCTIONS
def interval_de_sessions(listeDeTuples):
    if len(listeDeTuples) > 1:
        delai = abs(listeDeTuples[len(listeDeTuples)-1][1] - listeDeTuples[0][1])
        if delai > 7:
            #listeDeTuples.pop(len(listeDeTuples)-1)
            listeDeTuples.pop(0)
            return interval_de_sessions(listeDeTuples)
        else:
            inf = listeDeTuples[0][0]
            sup = listeDeTuples[len(listeDeTuples)-1][0]
            print(inf, sup)
            return inf, sup


# %% PRINCIPAL
if __name__ == "__main__":
    lst_tup_dates_asc = [(1,12), (2,14), (3,17), (4,19), (5,25)]
    lst_tup_dates_asc.sort(key=lambda tup: tup[1], reverse=False)
    print(lst_tup_dates_asc)
    print('Intervales asc')
    print(interval_de_sessions(lst_tup_dates_asc))
    sys.exit()
    while len(lst_tup_dates_asc) != 1:
        print(interval_de_sessions(lst_tup_dates_asc))
        lst_tup_dates_asc.pop(0)

    sys.exit()
    lst_tup_dates_desc = [(1,12), (2,14), (3,17), (4,19), (5,25)]
    lst_tup_dates_desc.sort(key=lambda tup: tup[1], reverse=True)
    print('\nIntervale desc')
    print(lst_tup_dates_desc)
    liste2 = interval_de_sessions(lst_tup_dates_desc)
    print(liste2)

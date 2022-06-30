# -*- coding: utf-8 -*-
"""
Created on Mon Feb 28 16:09:19 2022

@author: dominique
"""

import sys
# %% FONCTIONS
def interval_de_sessions(listeDeTuples, inf, sup):
    delai = abs(listeDeTuples[sup][1] - listeDeTuples[inf][1])
    if delai > 7 and not (inf == sup):
        return interval_de_sessions(listeDeTuples, inf+1, sup)
    else:
        return inf, sup


# %% PRINCIPAL
if __name__ == "__main__":
    lst_tup_dates_asc = [(1,12), (2,14), (3,17), (4,25)]
    lst_tup_dates_asc.sort(key=lambda tup: tup[1], reverse=False)
    print('\nIntervale asc')
    print(lst_tup_dates_asc)
    interval1 = interval_de_sessions(lst_tup_dates_asc, 0, len(lst_tup_dates_asc)-1)
    print(interval1)
    sys.exit()

    lst_tup_dates_desc = [(1,12), (2,14), (3,17), (4,25)]
    lst_tup_dates_desc.sort(key=lambda tup: tup[1], reverse=True)
    print('\nIntervale desc')
    print(lst_tup_dates_desc)
    liste2 = interval_de_sessions(lst_tup_dates_desc)
    print(liste2)

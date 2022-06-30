# -*- coding: utf-8 -*-
"""
Created on Mon Feb 28 16:09:19 2022

@author: dominique
"""
# %% FONCTIONS
def interval_de_sessions(listeDeTuples):
    borne_sup = len(listeDeTuples) - 1
    delai = abs(listeDeTuples[borne_sup][1] - listeDeTuples[0][1])
    if delai > 7 and len(listeDeTuples) != 1:
        listeDeTuples.pop(0)
        return interval_de_sessions(listeDeTuples)
    else:
        return listeDeTuples


# %% PRINCIPAL
if __name__ == "__main__":
    lst_tup_dates_asc = [(1,12), (2,14), (3,17), (4,25)]
    lst_tup_dates_asc.sort(key=lambda tup: tup[1], reverse=False)
    print('\nIntervale asc')
    print(lst_tup_dates_asc)
    liste1 = interval_de_sessions(lst_tup_dates_asc)
    print(liste1)

    lst_tup_dates_desc = [(1,12), (2,14), (3,17), (4,25)]
    lst_tup_dates_desc.sort(key=lambda tup: tup[1], reverse=True)
    print('\nIntervale desc')
    print(lst_tup_dates_desc)
    liste2 = interval_de_sessions(lst_tup_dates_desc)
    print(liste2)

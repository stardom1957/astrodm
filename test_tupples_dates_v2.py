# -*- coding: utf-8 -*-
"""
Created on Mon Feb 28 16:09:19 2022

@author: dominique
"""
# %% FONCTIONS
def interval_de_sessions(listeDeTuples):
    borne_sup = len(listeDeTuples) - 1
    delai = listeDeTuples[borne_sup][1] - listeDeTuples[0][1]
    if delai > 7 and len(listeDeTuples) != 1:
        listeDeTuples.pop(0)
        return interval_de_sessions(listeDeTuples)
    else:
        return len(listeDeTuples)-1, borne_sup


# %% PRINCIPAL
if __name__ == "__main__":
    lst_tup_dates = [(1,12), (2,14), (3,23), (4,25)]
    # trier la liste des tuples sur la date (index 1)
    lst_tup_dates.sort(key=lambda tup: tup[1], reverse=False)
    print(lst_tup_dates)

    session_inf, session_sup = interval_de_sessions(lst_tup_dates)
    print(session_inf+1, session_sup+1)
    
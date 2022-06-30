# -*- coding: utf-8 -*-
"""
Created on Mon Feb 28 16:09:19 2022

@author: dominique
"""
import pandas as pd
import sys
from astrodm import doublesOutils as do
# %% FONCTIONS
def produire_liste_delais(liste_tup_dates):
    """
    Parameters
    ----------
    lst_dates : TYPE
        DESCRIPTION.

    Returns
    -------
     lst_des_delais

    """
    if len(liste_tup_dates) != 1:
        # trier la liste des tuples sur la date (index 1)
        liste_tup_dates.sort(key=lambda tup: tup[1], reverse=False)
        lst_intervalles = list()
    
        fin = len(liste_tup_dates) - 1
        for r in range(0, fin):
            debut = r
            fin = debut + 1
            while fin < len(liste_tup_dates):
                delai = int(do.diff_dt(liste_tup_dates[debut][1], liste_tup_dates[fin][1]).value)
                #t = interval_de_sessions(liste_tup_dates, debut, fin)
                if delai != None:
                    lst_intervalles.append((debut, fin, delai))
                fin += 1
            
        # créer une nouvelle liste des tuples avec le delai entre chaque couple
        tempo = list()
        for couple in lst_intervalles:
            date1 = liste_tup_dates[couple[0]]
            date2 = liste_tup_dates[couple[1]]
            #delai = abs(date2[1] - date1[1])
            delai = int(do.diff_dt(date2[1], date1[1]).value)
            tempo.append([date1, date2, delai])
            
        # retourner liste triée sur délai et trouver le miminum
        tempo.sort(key=lambda tup: tup[2], reverse=False)
    else:
        # il y une seule session, alors
        # créer une liste 'artificielle' de la sorte
        # [(1, '2021-10-12'), ('sans objet', 0)]
        tempo = list()
        date1 = liste_tup_dates[0][1]
        date2 = 'sans objet'
        delai = 0
        tempo.append([date1, date2, delai])
        
    return tempo
    


# %% PRINCIPAL
if __name__ == "__main__":
    MAX_DELAI_ENTRE_OBSERVATIONS = 7

    lst_tup_dates = [(1,'2021-10-07'), (2,'2021-10-09'), (3,'2021-10-17'), (4,'2021-10-29'), (5,'2021-10-31')]
    print('Dates')
    print(lst_tup_dates)
    liste_des_delais_sessions = produire_liste_delais(lst_tup_dates)

    # liste_des_delais_sessions[0] représente le délai minimum

    date1 = liste_des_delais_sessions[0][0]
    date2 = liste_des_delais_sessions[0][1]
    delai = liste_des_delais_sessions[0][2]
    nombre_de_sessions = abs(date2[0] - date1[0]) + 1

    print("\nListe triée des délais :")
    print(*liste_des_delais_sessions, sep='\n')
    print('\n')
    print('Minimum : ', liste_des_delais_sessions[0])
    print(" ... entre {0} et {1}, délai de {2} jours.".\
          format(date1, date2, delai))
    print(" ... donc {0} sessions valides espacées de {1} jours\n".\
          format(nombre_de_sessions, delai))

    #
    # produire un dataframes des groupes d'observations
    #
    lstCol = ['Groupe', 'Dates', 'delai_entre_N (j)', 'Sessions (N)']
    groupes_de_sessions_df = pd.DataFrame(list(), columns=lstCol)
    int_choix = 1
    for groupe in liste_des_delais_sessions:
        delai = groupe[2]
        if delai <= MAX_DELAI_ENTRE_OBSERVATIONS:
            str_choix = '(' + str(int_choix) + ')'
            dates = list()
            for idx in range(groupe[0][0], groupe[1][0]+1):
                dates.append(lst_tup_dates[idx-1][1])
            #dates = groupe[0] + groupe[1]
            sessions = list()
            for i in range(groupe[0][0], groupe[1][0]+1):
                sessions.append(i)
            data = [str_choix, dates, delai, sessions]
            # ajouter data à la fin du df ...index.size
            groupes_de_sessions_df.loc[groupes_de_sessions_df.index.size] = data
            int_choix += 1
            

    print(groupes_de_sessions_df.to_string(index=False))

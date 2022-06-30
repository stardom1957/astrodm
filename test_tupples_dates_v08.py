# -*- coding: utf-8 -*-
"""
Created on Mon Feb 28 16:09:19 2022

@author: dominique
"""
import sys
# %% FONCTIONS
def interval_de_sessions(lst, inf, sup):
    delai = abs(lst[inf][1] - lst[sup][1])
    if delai > MAX_DELAI_ENTRE_OBSERVATIONS:
        #return 0, 0
        pass
    else:
        return inf, sup


# %% PRINCIPAL
if __name__ == "__main__":
    MAX_DELAI_ENTRE_OBSERVATIONS = 7

    lst_tup_dates = [(1,12), (2,14), (3,17), (4,19), (5,26)]
    # trier la liste des tuples sur la date (index 1)
    lst_tup_dates.sort(key=lambda tup: tup[1], reverse=False)
    print('Dates')
    print(lst_tup_dates)

    lst_intervalles = list()
    fin = len(lst_tup_dates) - 1
    for r in range(0, fin):
        debut = r
        fin = debut + 1
        while fin < len(lst_tup_dates):
            t = interval_de_sessions(lst_tup_dates, debut, fin)
            if t != None:
                lst_intervalles.append(t)
            fin += 1
        
    # créer une nouvelle liste des tuples avec le delai entre cjaque couple
    liste_des_delais = list()
    for couple in lst_intervalles:
        date1 = lst_tup_dates[couple[0]]
        date2 = lst_tup_dates[couple[1]]
        delai = abs(date2[1] - date1[1])
        liste_des_delais.append([date1, date2, delai])
        
    # trier cette liste sur délai et trouver le miminum
    liste_des_delais.sort(key=lambda tup: tup[2], reverse=False)
    minimum = min(*liste_des_delais)

    date1 = minimum[0]
    date2 = minimum[1]
    delai = minimum[2]
    nombre_de_sessions = abs(date2[0] - date1[0]) + 1

    print("\nRésultats :")
    print(liste_des_delais)
    print('\n')
    print(minimum)
    
    print("Le plus petit interval est entre {0} et {1} et est de {2} jours.".\
          format(date1, date2, delai))
    print("Il y a donc {0} sessions valides espacées de {1} jours".\
          format(nombre_de_sessions, delai))


    sys.exit()
    print("\nRésultats :")
    print('Intervals inférieurs à {0} jours :'.format(MAX_DELAI_ENTRE_OBSERVATIONS))
    print(lst_intervalles)
    maxinter = 7
    couple = (0, 0)
    # trouver le couple minimal d'observations avec l'intervalle
    # dont l'interval n'excède pas 7 jours
    #
    for inter in lst_intervalles:
        diff = inter[1] - inter[0]
        if diff <= maxinter:
            maxinter = diff
            couple = inter

    date1 = lst_tup_dates[couple[0]]
    date2 = lst_tup_dates[couple[1]]
    intervalle_en_jours = abs(date2[1] - date1[1])
    nombre_de_sessions = abs(date2[0] - date1[0]) + 1
    print("Le plus petit interval est entre {0} et {1} et est de {2} jours.".\
          format(date1, date2, intervalle_en_jours))
    print("Il y a donc {0} sessions valides sur {1} jours".\
          format(nombre_de_sessions, intervalle_en_jours))

    sys.exit()
    #
    # second run reversed
    #
    print('\n\n')
    lst_tup_dates = [(1,12), (2,14), (3,17), (4,19), (5,26)]
    # trier la liste des tuples sur la date (index 1)
    lst_tup_dates.sort(key=lambda tup: tup[1], reverse=True)
    print('Dates inversées')
    print(lst_tup_dates)

    lst_intervalles = list()
    fin = len(lst_tup_dates) - 1
    for r in range(0, fin):
        debut = r
        fin = debut + 1
        while fin < len(lst_tup_dates):
            t = interval_de_sessions(lst_tup_dates, debut, fin)
            if t != None:
                lst_intervalles.append(t)
            fin += 1
        
    print("\nRésultats :")
    print('Intervals inférieurs à {0} jours :'.format(MAX_DELAI_ENTRE_OBSERVATIONS))
    print(lst_intervalles)
    maxinter = 7
    couple = (0, 0)
    # trouver le couple minimal d'observations avec l'intervalle
    # dont l'interval n'excède pas 7 jours
    #
    for inter in lst_intervalles:
        diff = inter[1] - inter[0]
        if diff <= maxinter:
            maxinter = diff
            couple = inter

    date1 = lst_tup_dates[couple[0]]
    date2 = lst_tup_dates[couple[1]]
    intervalle_en_jours = abs(date2[1] - date1[1])
    nombre_de_sessions = abs(date2[0] - date1[0]) + 1
    print("Le plus grand interval est entre {0} et {1} et est de {2} jours.".\
          format(date1, date2, intervalle_en_jours))
    print("Il y a donc {0} sessions valides sur {1} jours".\
          format(nombre_de_sessions, intervalle_en_jours))

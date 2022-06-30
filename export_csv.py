# -*- coding: utf-8 -*-
"""
Created on Sat Nov 13 11:52:35 2021

@author: dominique

tests sur les exceptions

"""
import pandas as pd
# %% PRINCIPAL
if __name__ == "__main__":
    # on est en mode interactif
    '''

    # trouver dans quel enregistrement id_masque se trouve dans master_masques_cal_df
    for ix_m in range(0, master_masques_cal_df.index.stop):
        if id_masque == master_masques_cal_df.loc[ix_m,'id_masque']:
            masque_trouve = True
            print("masque {0} trouvé à l'enr {1}".format(id_masque, ix_m))
            break
   '''
   
    # lire master_calibrations_e.csv
    chemin_dossier_cal = 'D:\\DOCUMENTS\\Astronomie\\dev\\cal_e\\'
    master_calibrations_e_df = pd.read_csv(chemin_dossier_cal + 'master_calibrations_e.csv')
    
    index_cal_e = '2021-10-08b03'
    # place les info de index_cal_e trouvées dans master_calibrations_e_df dans info_index_cal_e_df
    idx_to_drop = (master_calibrations_e_df.loc[master_calibrations_e_df.index_cal_e==index_cal_e]).index

    
    # expurger toutes les occurences de index_cal_e du df
    # df.drop(df[df.score < 50].index, inplace=True)
    # ajouter les infos du nouvel index_cal_e
    
    # trier le df
    
    # exporter le df en csv
    
    

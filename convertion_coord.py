# -*- coding: utf-8 -*-
"""
Created on Fri Sep 15 00:16:31 2023

@author: jcdma
"""

#%% IMPORTS
# insérer le chemin suivant dans sys.path pour trouver le package astro_doubles
from tkinter import Tk
from tkinter.filedialog import askopenfile
import os

# %% FONCTIONS
def convertir(c):
    alpha, delta =  c.split(' ')
    alpha_h, alpha_m, alpha_s = alpha.split(':')
    delta_d, delta_m, delta_s = delta.split(':')
    
    alpha_decimal = ((((float(alpha_s) / 60) + float(alpha_m)) / 60) + float(alpha_h)) * 15
    alpha_decimal_str = "{0:.5f}".format(alpha_decimal)
    
    dec_decimal = (((float(delta_s)/60) + float(delta_m)) / 60) + float(delta_d)
    tempo = '-'
    if dec_decimal > 0:
        tempo = '+'
    dec_decimal_str = tempo + "{0:.5f}".format(dec_decimal)
    return alpha_decimal_str, dec_decimal_str

def selectionner_fichier_contour():
    """ Sélectione le fichier de contour de la constellation (txt). """
    root = Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()
    fichier = askopenfile(mode ='r', filetypes =[('Fichiers contour', '*.txt')],\
     title = 'Sélectionnez le fichier de contour')
    return fichier.name

# %% INITIALIATIONS
# indicateurs ascension droite et déclinaison
ad = 0
dec = 1
# %% PRINCIPAL
if __name__ == '__main__':
    # c = '08:59:56.7096350 +81:40:19.667414'
    # print(convertir(c))
    # ncfl : nom complet fichier lot
    #
    ncfc = selectionner_fichier_contour()
    print("\n*** Traitement du fichier de contour «{0}». ***".format(os.path.basename(ncfc)))

    # lire le fichier de contour de la constellation
    cs = list()
    if ncfc is not None:
        with open(ncfc) as f:
            lignesLues = f.readlines()
        f.close()

    '''
    Chaque ligne de lignesLues contient une ascension droite et une déclinaison
    Format de lignesLues
    lignesLues = [
        '08:59:56.7096350 +81:40:19.667414',
        '00:12:27.4541824 +78:38:46.888178',
        ...
        ]
    '''
    
    '''
    for c in lignesLues:
        print(*convertir(c))
    '''
        
    #
    # ajouter les conversions décimales dans un nouveau fichier
    # sous la forme '08:59:56.7096350 +81:40:19.667414 ---> 134.98629, +81.67213'
    #
    tst = lignesLues[0].strip('\n') + ' ---> ' + '134.98629' + ', ' + '+81.67213'
    conversions_lst = list()
    liste_coord_en_ligne = ""
    for l in lignesLues:
        conv = convertir(l)
        # tempo = l.strip('\n') + ' ---> ' + conv[ad] + ', ' + conv[dec]
        conversions_lst.append(l.strip('\n') + ' ---> ' + conv[ad] + ', ' + conv[dec])
        liste_coord_en_ligne = liste_coord_en_ligne + conv[ad] + ', ' + conv[dec] + ', '
    liste_coord_en_ligne = liste_coord_en_ligne.rstrip(', ')
    
    for c in conversions_lst:
        print(c)

    print('\nVoici la liste complète des coordonnées pour la fonction POLYGON :')
    print(liste_coord_en_ligne)
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 16:35:23 2020

@author: Dominique Martel

version 31

"""
# %% imports
import sys
from os import path
import os
from tkinter import Tk
from tkinter.filedialog import askdirectory

# %% Fonctions
def select_inter_fichiers():
    '''
    Type d'observation 'ech'
        L'utilisateur choisi le dossier de tête dans /cal_e, par ex. /2021-10-08b02 et on fait le reste.
        On en profite pour déterminer index_cal_e à partir du nom du répertoire de tête choisi.
    
    Type de réduction complète
        L'utilisateur choisi le répertoire de tête du programme d'observation de la paire et on fait
        le reste en itérant dans N1, N2, ..., etc

    Parameters
    ----------
     aucun

    Returns
    -------
     tupple type_observation et dossierDeTete.
    '''
    #debug global nom_complet_fich_log_reduc, ch_dossier_reduc, ch_dossier_reduc

    # sélectionner le dossier de tête
    titre = "Sélectionner répertoire de l'observation (échelle ou programme)"
    dossierDeTete = askdirectory(initialdir=os.getcwd(), title = titre, parent=root)
    
    # trouver le type d'observation par le contexter
    if 'cal_e' in path.dirname(dossierDeTete):
        return 'ech', dossierDeTete
    else:
        # il s'agit probablement* une observation complète
        # * sera validé plus loin
        return 'complete', dossierDeTete


# %% PRINCIPAL
if __name__ == "__main__":
# insérer le chemin suivant dans sys.path pour trouver le package astrodm
    if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
        sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
    from astrodm import doublesoutils as do

    # for tkinter
    global root, res
    root = Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()

    # L'usager pointe vers le dossier de tête soit de l'échelle ou du programme
    # d'observation de la paire; là où se trouvent N1, N2, etc.
    # Dans le cas d'une observation d'échelle,
    # cheminDeTeteProgramme == chemin du dossier de calibration E
    # to type observation, chProg chemin prog d'observation
    to, chProg = select_inter_fichiers()
    s = do.post_reduction(type_session=to, ch_prog=chProg)
    
    #################################################
    #        IMPRESSION DES RAPPORTS
    #################################################
    # rapport liste complète
    if s is not None:
        if s.typeSession == 'complete' and s.reductionExecutee:
            s.imprimerRapport('c')
            # rapport moyennes (pour publication)
            s.imprimerRapport('m')
        
            print("\nPour plus de détails exécutez :")
            print("  s.liste_attributs()")
            print("  s.imprimerRapport('x'), avec x: 'c' | 'l' | 'm' ou")
            print("  s.hier() pour sortie au terminal ou;")
            print("  s.hier(sortie='fichier') pour sortie vers ./out.txt")
            sys.exit()
        if s.typeSession == 'complete' and not s.reductionExecutee:
            print("Réduction non complétée : consultez le fichier «post-réduction.log» dans le dossier de programme!")
            sys.exit()
        if s.typeSession == 'ech' and s.reductionExecutee:
            print("Réduction complétée : consultez le fichier «post-réduction.log» dans le dossier d'échelle!")
            sys.exit()
        if s.typeSession == 'ech' and not s.reductionExecutee:
            print("Réduction non complétée : consultez le fichier «post-réduction.log» dans le dossier d'échelle!")



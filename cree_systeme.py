# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 16:31:40 2020
   Ce module crée le dossier de base et le fichier _info_système.csv pou
   le système passé en paramètre. Certaines informations au sujet du stystème
   sont fournies par l'usager alors que d'autres sont tirées du WDS par le
   biais de astroquery.

@author: dominique
"""

#%% IMPORTS
import os
#import glob
import pandas as pd
#import numpy as np
from tkinter import Tk
#from tkinter.filedialog import askdirectory
from tkinter.filedialog import askopenfile
import sys
import shutil

# insérer le chemin suivant dans sys.path pour trouver le package astro_doubles
if 'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, 'D:\DOCUMENTS\Astronomie\dev')
from astrodm import doublesoutils as do
# %% INITIALISATIONS
### pandas options d'affichage des tables
pd.set_option('display.expand_frame_repr', True)
pd.set_option('display.colheader_justify', 'right')
pd.set_option('display.max_colwidth', 100)
pd.set_option('display.max_column', 15)
pd.set_option('display.width', 200)
pd.set_option('display.max_row', 10000)
pd.set_option("display.precision", 1)

# %% FONCTIONS
def estNan(val):
    return val != val

def traiter_obj_sys(obj_s, cahier=True):
    """
    Traite un objet système créé interactivement par une recherche dans WDS,
    imprime les résultats avec note pour aider la validation

    Paramètre positionnel
     obj_s -- astrodm objet Systeme
     
    Paramètre keyword
     cahier -- Boolean indique si enregistrement cahier Jupyter
      True par défaut
    """
    
    print('\nInformations WDS :\n')
    do.info_src_wds(obj_s.nom, '*', True)
    
    # imprimer le df pour validation
    print('\n' + '*' * 15 + ' DataFrame information_df '+ '*' * 15 + ' :\n')
    print('-' * 104)
    print(obj_s.informations_df)
    print('-' * 104)
    
    # saisir intention de modifier information_de
    rep = input("Modifier information_df (o|n) ? ").upper()
    if rep.upper() == 'O':
        bool_modif = True
        while bool_modif:
            # seuls :
            # id_system_alt1, id_system_alt2 et remarques peuvent être modifiés
            # soit index 4, 5 et 7 (zero based)
            #
            lst_modif = (4,5,7,8)
            # présenter les données
            i = 1
            # lister les index
            print("Index")
            print("{0} {1:>16} {2}".format(0, 'terminé', ''))
            for k in range(0, len(obj_sys.informations_df.keys())):
                if k in lst_modif:
                    print("{0} : {1:>16} = {2}".format(k, obj_s.informations_df.keys()[k], obj_s.informations_df.iloc[0,k]))
                    i += 1

            # boucle de modification
            try:
                rep = int(input("Index : "))
            except ValueError:
                print("Entrée doit être un entier.")
                
            # arrêter la modification si en dehors de l'intervalle
            #debug if rep > 0 and rep <= len(obj_s.informations_df.keys()) and int(rep) in lst_modif:
            if int(rep) in lst_modif:
                print("{0} = {1}".format(obj_s.informations_df.keys()[rep], obj_s.informations_df.iloc[0,rep]))
                data = input(obj_s.informations_df.keys()[rep] + ' = ')
                obj_s.informations_df.loc[0, obj_s.informations_df.keys()[rep]] = data
            elif int(rep) == 0:
                bool_modif = False
            else:
                print('Entrée incorrecte!')
    
    # s'assurer que les attribut chaînes sont entre guillemets
    obj_s.normalise_attributs_chaines()
    print(obj_s.informations_df)

    ### saisir intention enregistrement sur disque
    print('\nLes actions suivantes seront exécutés :')
    print('  si NÉCESSAIRE, création du dossier : «' + os.path.dirname(obj_s.ncfinfo_systeme) + '»')
    print('    ... écriture du DataFrame information_df dans le fichier «' +\
          os.path.basename(obj_s.ncfinfo_systeme) +'»')
    
    if cahier:    
        print('  création du dossier : «' + os.path.dirname(obj_s.ncfinfo_systeme) + '/planif»')
        print('    ... création du cahier de notes «systeme-notes.ipynb»')
    
    rep = input("Enregistrer les données sur disque (o|n) ? ").upper()
    if 'O' in rep:
        enregistrer_sur_disque(obj_s, cahier)
    else:
        print("Pas d'enregistrement.")


def enregistrer_sur_disque(objet_systeme, traitement_en_lot=False, cahier=True):
    """
    Créer structure des répertoires d'un système et enregistrer info-systeme.csv.
    
    Également crée cahier Jupyter dans ./med-planification

    Paramètre positionnel
     objet_systeme -- astrodm objet Systeme
     
    Paramètre keyword
     traitement_en_lot -- Boolean indique si traitement en lot
      False par défaut
     cahier -- Boolean si True copie du cahier Jupyter lab modèle dans
     dossier
    """
    assert objet_systeme != None, 'Rien à enregister sur disque!'

    ### création du répertoire du système et planif
    # il n'y a pas de mal à tenter de créer des répertoires même s'ils existes
    dir_systeme = os.path.dirname(objet_systeme.ncfinfo_systeme)
    os.makedirs(dir_systeme, exist_ok=True)
    os.makedirs(dir_systeme + "/planif/", exist_ok=True)
    
    ### vérification de la présence d'un fichier information système
    bool_fichier_info_existe = os.path.exists(objet_systeme.ncfinfo_systeme)

    #    
    # Lors du traitement en lot, s'il existe un fichier information système
    # le traitement doit se faire normalement afin de mettre les informations du
    # système à jour, sauf pour le cahier Jupyter qui doit être préservé.
    #

    if bool_fichier_info_existe and traitement_en_lot:
        #debug return False
        cahier = False

    #
    # Dans le cas où fichier info n'existe pas, le traitement est le même
    # avec ou sans traitement en lot
    #

    if not bool_fichier_info_existe:
        objet_systeme.informations_df.to_csv(objet_systeme.ncfinfo_systeme,\
                                    index=False, encoding='utf-8')
        # copier fichier modèle cahier de notes et renommer avec nom du
        # système
        if cahier:
            source = ncf_cahier_modele
            #destination = dir_systeme + "/med-planification/" + objet_systeme.nom + '_notes.ipynb'
            destination = dir_systeme + "/planif/systeme-notes.ipynb"
            shutil.copy(source, destination)
        return True
    else:
        #
        # Dans le cas où fichier info existe et seulement en dehors du traitement
        # en lot, on doit offrir à l'usager la possibilité d'enregistrer ou non
        #

        rep = 'O'
        if not traitement_en_lot:
            # demander pour mise à jour
            rep = input('Le fichier «{0}» existe déjà ! Écraser ? (o/n) : '.\
                        format(objet_systeme.ncfinfo_systeme)).upper()
        if 'O' in  rep:
            objet_systeme.informations_df.to_csv(objet_systeme.ncfinfo_systeme,\
                                         index=False, encoding='utf-8')
            print('Fichier information système enregistré.')
            return True
        else:
            print("Enregistrement annulé par l'usager.")
            return False
        
   
def selectionner_et_lire_info_systeme():
    global bool_informations_df_OK
   
    ### Sélectionner répertoire source
    root = Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()
    
    # sélectionner le fichier des informations de la source
    ncfi = askopenfile(mode ='r', filetypes =[('Fichiers «info-systeme»', '*.csv')],\
     title = 'Sélectionnez le fichier information système')

    # trouver racine du répertoire système
    rrs = os.path.dirname(ncfi.name)
    return rrs
    
def selectionner_fichier_lot():
    ### Sélectionner fichier lot
    root = Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()
    ncf = askopenfile(mode ='r', filetypes =[('Fichiers lot', '*.ods')],\
     title = 'Sélectionnez le fichier du lot')
    return ncf.name
    
    


# %% Réglages de l'environnement d'exécution
### pandas options d'affichage des tables
pd.set_option('display.expand_frame_repr', True)
pd.set_option('display.colheader_justify', 'right')
pd.set_option('display.max_colwidth', 50)
pd.set_option('display.max_column', 30)
pd.set_option('display.width', 120)


# %% INITIALISATIONS
dossier_des_modeles = os.getcwd() + r'/modeles'
ncf_cahier_modele = dossier_des_modeles + r'/systeme-notes.ipynb'

# %% PRINCIPAL
if __name__ == '__main__':
    # imprimer le menu et saisir intention
    print("{0} {1:>30} {2}".format(0, 'Quitter', ''))
    print("{0} {1:>30} {2}".format(1, 'Lire et modifier un fichier information', ''))
    print("{0} {1:>30} {2}".format(2, 'Saisir ID système (découvreur)', ''))
    print("{0} {1:>30} {2}".format(3, "Traitement d'un lot (Excel)", ''))

    rep = input("Votre choix (2 par défaut): ") or '2'
    if rep.isdigit():
        irep = int(rep)
        if irep == 0:
            print("Au revoir!")
            sys.exit()
        elif irep > 3:
            print("Mauvaise réponse {0}".format(irep))
            sys.exit()
    else:
        print("{0} :: pas un chiffre!".format(rep))
        sys.exit()


    if irep == 1:
        # lecture d'un fichier système
        racine_repertoire_systeme = selectionner_et_lire_info_systeme()
        obj_sys = do.Systeme(chemin_systeme=racine_repertoire_systeme)
        traiter_obj_sys(obj_sys, cahier=False)
        
    elif irep == 2:
        # 'Saisir ID système'
        racine_repertoire_systeme = os.getcwd() + r'/med/'

        # accepter et valider nom du système
        nom_sys_WDS = input("Nom du système : ")
        if not do.valide_nom_systeme(nom_sys_WDS)[0]:
            print('Nom du système non valide')
            sys.exit()
        
        # créer objet Systeme avec l'information de base
        obj_sys = do.Systeme(chemin_systeme=racine_repertoire_systeme,\
                    nom_systeme_WDS=nom_sys_WDS,\
                       id_sys_alt1='', id_sys_alt2='', WDSdr='non',\
                           remarques='')

        # vérifier si le dossier du système existe déjà afin d'éviter de
        # détruire le cahier Jupyter le cas échéant
        #
        if os.path.exists(obj_sys.ncfinfo_systeme):
            rep = input('ATTENTION. Le dossier du système existe déjà! Continuer (o|n) ? ')
            if rep.upper() == 'N':
                print('Bye!')
                sys.exit()
            else:
                traiter_obj_sys(obj_sys, cahier=False)
        else:
            traiter_obj_sys(obj_sys, cahier=True)

    #
    # traitement en lot
    #
    elif irep == 3:
        racine_repertoire_systeme = os.getcwd() + r'/med/'

        # ncfl : nom complet fichier lot
        ncfl = selectionner_fichier_lot()
        print("\n*** Traitement du lot «{0}». ***".format(os.path.basename(ncfl)))

        # journalisation des résultats, erreurs, etc
        # création du systag pour rendre nom fichier unique
        systag = do.produire_systag()

        # nom complet du fichier de journalisation composé à partir de ncfl et
        # du systag
        ncfl_journal = os.path.dirname(ncfl) + '/Traitement_lot_' + os.path.basename(ncfl).split('.')[0] + '_' + systag + '.log'
        # lire ncfl dans un pandas df
        lot_df = pd.read_excel(ncfl, engine="odf")

        #    
        # création du journal sous forme de list
        #
        lst_journal = list()
        lst_journal.append("Journal du traitement de «" + os.path.basename(ncfl) + '»\n')
        tempo = "    Comprenant {0} systèmes.\n\n".format(len(lot_df))
        print(tempo)
        lst_journal.append(tempo)

        
        lot_choisis = lot_df.query("choisir == 1")
        lot_non_choisis = lot_df.query("choisir == 0")
        
        tempo = "{0} systèmes choisis :".format(len(lot_choisis))
        print(tempo)
        lst_journal.append(tempo + '\n')
        
        tempo = ''
        for idx in lot_choisis.index:
            tempo = tempo + lot_choisis.loc[idx,'id_system'] + ', '
            
        lst_journal.append(tempo.rstrip(', '))
        print(tempo.rstrip(', '))
            
        print("\n\n{0} systèmes non choisis :".format(len(lot_non_choisis)))
        lst_journal.append("\n\n{0} systèmes non choisis :\n".format(len(lot_non_choisis)))
        
        tempo = ''
        for idx in lot_non_choisis.index:
            tempo = tempo + lot_non_choisis.loc[idx,'id_system'] + ', '

        
        lst_journal.append(tempo.rstrip(', ') + '\n')
        print(tempo.rstrip(', ') + '\n')
        
        #
        # traitement des systèmes choisis
        #
        print('\n')
        lst_journal.append("\n")

        for idx in lot_choisis.index:
            tempo = "Traitement de {0:<7} ".format(lot_choisis.loc[idx,'id_system'])
            print(tempo)
            lst_journal.append(tempo + '\n')

            # valide système
            # tupple systeme_check = (True, résultat de recherche WDS)
            #   ou (False, None)
            systeme_check = do.valide_nom_systeme(lot_choisis.loc[idx].id_system)
            if systeme_check[0]:
                # placer les valeurs dans des variables temporaires
                nom = lot_choisis.loc[idx,'id_system']
                # d'abord remplacer les NaN par '' dans enregistrement
                if estNan(lot_choisis.loc[idx].id_system_alt1):
                    alt1 = ''
                else:
                    alt1 = lot_choisis.loc[idx].id_system_alt1
                    
                if estNan(lot_choisis.loc[idx].id_system_alt2):
                    alt2 = ''
                else:
                    alt2 = lot_choisis.loc[idx].id_system_alt2

                # .WDSdr = non | OUI
                if estNan(lot_choisis.loc[idx].WDSdr):
                    WDSdr_val = 'non'
                else:
                    if lot_choisis.loc[idx].WDSdr == 'oui' or lot_choisis.loc[idx].WDSdr == 'OUI':
                       WDSdr_val = 'OUI'
                    else:
                       WDSdr_val = 'non'

                if estNan(lot_choisis.loc[idx].remarques):
                    rem = ''
                else:
                    rem = lot_choisis.loc[idx].remarques
                
                # créer objet Systeme
                obj_sys = do.Systeme(chemin_systeme=racine_repertoire_systeme,\
                            nom_systeme_WDS=lot_choisis.loc[idx].id_system,\
                               id_sys_alt1=alt1,\
                               id_sys_alt2=alt2,\
                                   WDSdr=WDSdr_val, remarques=rem)
                    
                # inscrire le nom du système dans le journal
                print("  système {0} traité!\n".format(lot_choisis.loc[idx].id_system))
                lst_journal.append("  système {0} traité!\n".format(lot_choisis.loc[idx].id_system))
                
                if not enregistrer_sur_disque(obj_sys, traitement_en_lot=True):
                    # ajouter message d'erreur dans journal
                    #lst_journal.append("Système {0} : _info_système.csv existe déjà!\n".format(lot_choisis.loc[idx].id_system))
                    print("Système {0} : info-systeme.csv existe déjà!\n".format(lot_choisis.loc[idx].id_system))
                    lst_journal.append("Système {0} : info-systeme.csv existe déjà!\n".format(lot_choisis.loc[idx].id_system))

            else:
                # placer message d'erreur dans journal
                tempo = "Système {0} : ne semble pas valide!\n".\
                                   format(lot_choisis.loc[idx].id_system)
                lst_journal.append(tempo)
                print(tempo)

        # écrire le journal sur disque
        with open(ncfl_journal, 'w', encoding='UTF-8') as f:
            f.writelines(lst_journal)
            
        print("Le journal est dans «{0}»".format(ncfl_journal))
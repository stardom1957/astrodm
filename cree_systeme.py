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
pd.set_option('display.width', 240)
pd.set_option('display.max_row', 10000)
pd.set_option("display.precision", 1)

# %% FONCTIONS
def creer_dossier_paire_et_prog(objet_systeme, paire='PPL', programme='Paaaa-nnn'):
    """
    Créer structure des répertoires d'une paire, selon lemodèle paire/programme.
    
    Paramètre positionnel
     objet_systeme -- astrodm objet Systeme
     
    Paramètre keyword
     paire : désignation de la paire. Par ex. AB
     programme : par ex P2023-025
     
    Retourne : True | False selon enregistrement ok
    """
    if objet_systeme == None:
        tempo = "creer_dossier_paire_et_prog) Erreur ! Objet système manquant ou non valide !"
        print(tempo)
        lst_journal.append(tempo + '\n')
        return False
    
    # dossier du système
    dir_systeme = os.path.dirname(objet_systeme.ncfinfo_systeme)
    
    try:
        ### création du répertoire de la paire dans le dossier du système
        os.makedirs(dir_systeme + "/" + paire.upper(), exist_ok=True)
    except FileNotFoundError:
        tempo = "creer_dossier_paire_et_prog) Erreur ! Création du dossier de la paire impossible !"
        print(tempo)
        lst_journal.append(tempo + '\n')
        return False

    try:
        ### création du répertoire du programme  dans le dossier de la paire
        os.makedirs(dir_systeme + "/" + paire + '/' + programme.upper(), exist_ok=True)
    except FileNotFoundError:
        tempo = "creer_dossier_paire_et_prog) Erreur ! Création du dossier du programme impossible !"
        print(tempo)
        lst_journal.append(tempo + '\n')
        return False

    return True


def cree_dossier_systeme(sys_df):
    """ Crée les dossiers du système passé en paramètres
    
    Paramètres positionnels
     sys_df un Dataframe Pandas contenant les informations du système
     
    Retourne
     un objet doublesoutils.systeme ou None
    """
    # valide système
    # tupple systeme_check = (True, résultat de recherche WDS)
    #   ou (False, None)
    #
    systeme_check = do.valide_nom_systeme(sys_df['id_system'].item())
    if systeme_check[0]:
        # placer les valeurs dans des variables temporaires
        # si nécessaire, remplacer les NaN par ''
        #
        nom_systeme = sys_df['id_system'].item()
        
        if estNan(sys_df['id_system_alt1'].item()):
            alt1 = ''
        else:
            alt1 = sys_df['id_system_alt1'].item()
            
        if estNan(sys_df['id_system_alt2'].item()):
            alt2 = ''
        else:
            alt2 = sys_df['id_system_alt2'].item()

        # .WDSdr = non | OUI
        if estNan(sys_df['WDSdr'].item()):
            WDSdr_val = 'non'
        else:
            if sys_df['WDSdr'].item() == 'oui' or sys_df['WDSdr'].item() == 'OUI':
               WDSdr_val = 'OUI'
            else:
               WDSdr_val = 'non'

        if estNan(sys_df['remarques'].item()):
            rem = ''
        else:
            rem = sys_df['remarques'].item()
        
        # créer objet Systeme
        obj_sys = do.Systeme(chemin_systeme=racine_repertoire_systeme,\
                    nom_systeme_WDS=nom_systeme, id_sys_alt1=alt1, id_sys_alt2=alt2,\
                           WDSdr=WDSdr_val, remarques=rem)
            
        # renseigner le log
        lst_journal.append("  Création du dossier du système terminée !\n")
        
        enregistre_sur_disque_ok = enregistrer_systeme_sur_disque(obj_sys, traitement_en_lot=True)
        
        if not enregistre_sur_disque_ok:
            # ajouter message d'erreur dans journal
            #lst_journal.append("Système {0} : _info_système.csv existe déjà!\n".format(lot_choisis_df.loc[idx].id_system))
            print("Système {0} : info-systeme.csv non modifié !\n".format(sys_df['id_system'].item()))
            lst_journal.append("Système {0} : info-systeme.csv non modifié !\n".format(sys_df['id_system'].item()))

        print("  Création du dossier du système terminée !")
        return obj_sys

    else:
        # placer message d'erreur dans journal
        tempo = "Système {0} : ne semble pas valide!\n".\
                           format(sys_df['id_system'].item())
        lst_journal.append(tempo)
        print(tempo)
        return None



def estNan(val):
    return val != val

def traiter_obj_sys(obj_s, copier_cahier=True):
    """
    Traite un objet système créé interactivement par une recherche dans WDS,
    imprime les résultats avec note pour aider la validation

    Paramètre positionnel
     obj_s -- astrodm objet Systeme
     
    Paramètre keyword
     copier_cahier -- Boolean indique si enregistrement cahier Jupyter
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
    
    if copier_cahier:    
        print('  création du dossier : «' + os.path.dirname(obj_s.ncfinfo_systeme) + '/planif»')
        print('    ... création du cahier de notes «systeme-notes.ipynb»')
    
    rep = input("Enregistrer les données sur disque (o|n) ? ").upper()
    if 'O' in rep:
        enregistrer_systeme_sur_disque(obj_s, copier_cahier)
    else:
        print("Pas d'enregistrement.")


def enregistrer_systeme_sur_disque(objet_systeme, traitement_en_lot=False, copier_cahier=True):
    """
    Créer structure des répertoires d'un système et enregistre info-systeme.csv.
    
    Également crée cahier Jupyter dans ./med-planification

    Paramètre positionnel
     objet_systeme -- astrodm objet Systeme
     
    Paramètre keyword
     traitement_en_lot -- Boolean indique si traitement en lot
      False par défaut
     copier_cahier -- Boolean si True copie du cahier Jupyter lab modèle dans
     dossier
     
    Retourne : True | False selon enregistrement ok
    """
    assert objet_systeme != None, '(enregistrer_systeme_sur_disque) Erreur ! Objet système manquant ou non valide !'

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
        copier_cahier = False

    #
    # Dans le cas où fichier info n'existe pas, le traitement est le même
    # avec ou sans traitement en lot
    #

    if not bool_fichier_info_existe:
        objet_systeme.informations_df.to_csv(objet_systeme.ncfinfo_systeme,\
                                    index=False, encoding='utf-8')
        # copier fichier modèle cahier de notes et renommer avec nom du
        # système
        if copier_cahier:
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
            if not traitement_en_lot:
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

    rep = input("Votre choix (3 par défaut): ") or '3'
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
        # enlever les lignes vides (nan ...) qui correspondent au lignes blanches dans excel
        #
        lignes_vides_serie = lot_df['id_system'].apply(estNan)
        lot_complet_df = lot_df.drop(lot_df.loc[lignes_vides_serie].index).reset_index(drop=True)
        
        #    
        # création du journal sous forme de liste
        #
        lst_journal = list()
        lst_journal.append("*** Journal du traitement de «" + os.path.basename(ncfl) + '» ***\n')
        tempo = "qui comprend {0} enregistrements de données.\n".format(len(lot_complet_df))
        print(tempo)
        lst_journal.append(tempo + '\n')

        # filter les enregistrements avec la colonne choisir (0|1)
        lot_choisis_df = lot_complet_df.query("choisir == 1")
        lot_non_choisis_df = lot_complet_df.query("choisir == 0")
        
        # créer un set des id_system's choisis
        s_choisis_set = set()
        for idx in lot_choisis_df.index:
            s_choisis_set.add(lot_choisis_df.loc[idx, 'id_system'])

        tempo = "{0} systèmes choisis :".format(len(s_choisis_set))
        print(tempo)
        print(s_choisis_set)
        lst_journal.append(tempo + '\n')
        
        # placer le contenu de s_choisis_set dans le log
        #
        tempo = "{"
        for i in range(len(list(s_choisis_set))):
            tempo = tempo + "'" + list(s_choisis_set)[i] + "', "
        tempo = tempo.rstrip(", ")
        tempo = tempo + "}\n"
        lst_journal.append(tempo)            

        # créer un set des id_system's non choisis
        s_non_choisis_set = set()
        for idx in lot_non_choisis_df.index:
            s_non_choisis_set.add(lot_non_choisis_df.loc[idx, 'id_system'])

        tempo = "\n{0} systèmes non choisis :".format(len(s_non_choisis_set))
        print(tempo)
        print(s_non_choisis_set)
        print()
        lst_journal.append(tempo + '\n')
        
        # placer le contenu de s_non_choisis_set dans le log
        tempo = "{"
        for i in range(len(list(s_non_choisis_set))):
            tempo = tempo + "'" + list(s_non_choisis_set)[i] + "', "
        tempo = tempo.rstrip(", ")
        tempo = tempo + "}\n"
        lst_journal.append(tempo)            
            
        #
        # sélectionner et traiter chaque système présent dans s_choisis_set
        #
        lst_journal.append("\n")
        for nom_systeme in s_choisis_set:
            systeme_courant_df = lot_choisis_df.query("id_system == '" + nom_systeme + "'")
            tempo = "Traitement de {0:<7} :".format(systeme_courant_df.iloc[0].id_system)
            print(tempo)
            #debug print(systeme_courant_df)
            
            lst_journal.append(tempo + '\n')
            #debug lst_journal.append(systeme_courant_df)

            # déterminer index de l'enregistrement système
            idx_systeme = systeme_courant_df.query("paire == 'système'").index
            if len(idx_systeme) == 0:
                tempo = "  {0:<7} : pas d'enregistrement système dans le fichier du lot.".format(systeme_courant_df.iloc[0].id_system)
                print(tempo + "\n")
                lst_journal.append(tempo)
            else:
                # créer le dossier du système
                objet_systeme_courant = cree_dossier_systeme(systeme_courant_df.loc[idx_systeme])
                
                # enlever l'enr de système dans systeme_courant_df
                #
                paires_df = systeme_courant_df.drop(index=idx_systeme)

                # créer le dossier de chaque paire et le sous-dossier de programme d'observation dans ce dossier
                #
                
                # voir enregistrer_systeme_sur_disque
                print("  Dossiers des paires et programmes :")
                for idx in paires_df.index:
                    pr = paires_df.loc[idx].paire
                    prog = paires_df.loc[idx].programme
                    OKres = creer_dossier_paire_et_prog(objet_systeme_courant, paire=pr, programme=prog)
                    tempo = "  {0:>5} / {1} ".format(pr, prog)
                    if OKres:
                        tempo = tempo + 'CRÉÉ'
                    else:
                        tempo = tempo + 'ERREUR'
                    print(tempo)
                    lst_journal.append(tempo + '\n')
                print()

                """
                lst_journal.append("  Dossiers des paires et programmes :\n")
                # placer le contenu de paires_df.paire dans le log
                #
                for idx in paires_df.index:
                    tempo = "  {0:>5} / {1}".format(paires_df.loc[idx].paire, paires_df.loc[idx].programme)
                    lst_journal.append(tempo + '\n')
                lst_journal.append('\n')
                """
                
        
        # compéter et écrire le journal sur disque
        #
        lst_journal.append("*** Traitement terminé ! ***")
        with open(ncfl_journal, 'w', encoding='UTF-8') as f:
            f.writelines(lst_journal)
            
        print("\n*** Traitement terminé ! ***")
        print("Le journal est dans «{0}»".format(ncfl_journal))
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 16:31:40 2020
   Ce module crée le dossier de base et le fichier _info_système.csv pou
   le système passé en paramètre. Certaines informations au sujet du stystème
   sont fournies par l'usager alors que d'autres sont tirées du WDS par le
   biais de astroquery.
   
   Le module supporte uniquement le traitement en lot (fichier Excel).

@author: dominique
"""

#%% IMPORTS
# insérer le chemin suivant dans sys.path pour trouver le package astro_doubles
import sys
import os
from tkinter import Tk
from tkinter.filedialog import askopenfile
import shutil
import pandas as pd

if r'D:\DOCUMENTS\Astronomie\dev' not in sys.path:
    sys.path.insert(0, r'D:\DOCUMENTS\Astronomie\dev')
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
def creer_dossier_paire_et_prog(objet_systeme, paire='PPL', programme='P0000-000'):
    """
    Créer structure des répertoires d'une paire, selon lemodèle paire/programme.
    
    Paramètre positionnel
     objet_systeme -- astrodm objet Systeme
     
    Paramètre keyword
     paire : désignation de la paire. Par ex. AB
     programme : par ex P2023-025
     
    Retourne : True | False selon enregistrement ok
    """
    tempo = "  (creer_dossier_paire_et_prog) Erreur ! Objet système manquant ou non valide !"
    if objet_systeme is None:
        print(tempo)
        lst_journal.append(tempo + '\n')
        return False

    # dossier du système
    dir_systeme = os.path.dirname(objet_systeme.ncfinfo_systeme)
    if not mode_validation:
        try:
            ### création du répertoire de la paire dans le dossier du système
            os.makedirs(dir_systeme + "/" + paire.upper(), exist_ok=True)
        except FileNotFoundError:
            tempo = "  (creer_dossier_paire_et_prog) Erreur ! Création du dossier de la paire impossible !"
            print(tempo)
            lst_journal.append(tempo + '\n')
            return False
    
        try:
            ### création du répertoire du programme  dans le dossier de la paire
            os.makedirs(dir_systeme + "/" + paire + '/' + programme.upper(), exist_ok=True)
        except FileNotFoundError:
            tempo = "  (creer_dossier_paire_et_prog) Erreur ! Création du dossier du programme impossible !"
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
        nom_sys = sys_df['id_system'].item()

        if do.estNan(sys_df['id_system_alt1'].item()):
            alt1 = ''
        else:
            alt1 = sys_df['id_system_alt1'].item()

        if do.estNan(sys_df['id_system_alt2'].item()):
            alt2 = ''
        else:
            alt2 = sys_df['id_system_alt2'].item()

        # .WDSdr = non | OUI
        if do.estNan(sys_df['WDSdr'].item()):
            WDSdr_val = 'non'
        else:
            if sys_df['WDSdr'].item() == 'oui' or sys_df['WDSdr'].item() == 'OUI':
                WDSdr_val = 'OUI'
            else:
                WDSdr_val = 'non'

        if do.estNan(sys_df['remarques'].item()):
            rem = ''
        else:
            rem = sys_df['remarques'].item()

        # créer objet Systeme
        #
        obj_sys = do.Systeme(chemin_systeme=racine_repertoire_systeme,\
                    nom_systeme_WDS=nom_sys, id_sys_alt1=alt1, id_sys_alt2=alt2,\
                           WDSdr=WDSdr_val, remarques=rem)

        if not mode_validation:
            enregistrer_systeme_sur_disque(obj_sys)
        lst_journal.append("  '{0}' OK :\n".format(obj_sys.nom))

        # renseigner le log
        #
        print("  '{0}' OK :".format(obj_sys.nom))
        return obj_sys

    # le système est non valide
    # placer message d'erreur dans journal
    #
    tempo = "Système {0} : ne semble pas valide!\n".\
                       format(sys_df['id_system'].item())
    lst_journal.append(tempo)
    print(tempo)
    return None



def enregistrer_systeme_sur_disque(objet_systeme):
    """
    Créer structure des répertoires d'un système et enregistre info-systeme.csv.
    
    Également crée cahier Jupyter dans ./med-planification

    Paramètre positionnel
     objet_systeme -- astrodm objet Systeme
     
    Paramètre keyword
     copier_cahier -- Boolean si True copie du cahier Jupyter lab modèle dans
                      dossier
    """
    assert objet_systeme is not None, '(enregistrer_systeme_sur_disque) Erreur ! Objet système manquant ou non valide !'

    ### création du répertoire du système et planif
    # il n'y a pas de mal à tenter de créer des répertoires même s'ils existent
    #
    dir_systeme = os.path.dirname(objet_systeme.ncfinfo_systeme)
    os.makedirs(dir_systeme, exist_ok=True)
    os.makedirs(dir_systeme + "/planif/", exist_ok=True)

    '''    
    L'objet objet_systeme.informations_df est toujours écrit dans le fichier
    information système (csv). Par contre, s'il existaint déjà un fichier information système
    dans le dossier du système (bool_fichier_info_existe == True), alors il y a
    déjà eu un traitement pour ce système et l'on doit éviter de copier le
    modèle de cahier Jupyter Lab afin de préserver celui qui se
    trouve dans le répertoire (ce dernier pourrait avoir été modifié par l'usager).
    
    Sinon, le modèle de cahier Jupyter est copié.
    '''

    bool_fichier_info_existe = os.path.exists(objet_systeme.ncfinfo_systeme)
    if bool_fichier_info_existe:
        copier_cahier=False
    else:
        copier_cahier=True

    objet_systeme.informations_df.to_csv(objet_systeme.ncfinfo_systeme,\
                                index=False, encoding='utf-8')

    # copier fichier modèle Jupyter Lab
    #
    if copier_cahier:
        source = ncf_cahier_modele
        destination = dir_systeme + "/planif/systeme-notes.ipynb"
        shutil.copy(source, destination)


def selectionner_fichier_lot():
    """ Sélectione le fichier lot (ods) sur disque. """
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
    #
    # demander pour le mode de validation seulement
    # c'est-à-dire aucun dossier créé, lseulement le log
    #
    rep = input("Mode VALIDATION (o|n) o par défaut :") or 'o'
    mode_validation = True
    if rep.upper() == 'N':
        mode_validation = False
    racine_repertoire_systeme = os.getcwd() + r'/med/'

    # ncfl : nom complet fichier lot
    #
    ncfl = selectionner_fichier_lot()
    print("\n*** Traitement du lot «{0}». ***".format(os.path.basename(ncfl)))

    # journalisation des résultats, erreurs, etc
    # création du systag pour rendre nom fichier unique
    #
    systag = do.produire_systag()

    # nom complet du fichier de journalisation composé à partir de ncfl et
    # du systag
    #
    ncfl_journal = os.path.dirname(ncfl) + '/Traitement_lot_' +\
        os.path.basename(ncfl).split('.')[0] + '_' + systag + '.log'

    # lire fichier lot dans un df
    #
    lot_df = pd.read_excel(ncfl, engine="odf")

    #
    # enlever les lignes vides (nan ...) qui correspondent au lignes blanches dans excel
    #
    lignes_vides_serie = lot_df['id_system'].apply(do.estNan)
    lot_complet_df = lot_df.drop(lot_df.loc[lignes_vides_serie].index).reset_index(drop=True)

    # créer le journal sous forme de liste
    #
    lst_journal = []
    lst_journal.append("*** Journal du traitement de «" + os.path.basename(ncfl) + '» ***\n')
    tempo = "qui comprend {0} enregistrements de données.\n".format(len(lot_complet_df))
    print(tempo)
    lst_journal.append(tempo + '\n')

    # filtrer les enregistrements avec la colonne choisir (0|1)
    #
    lot_choisis_df = lot_complet_df.query("choisir == 1")
    lot_non_choisis_df = lot_complet_df.query("choisir == 0")

    # créer un set des id_system's non choisis
    #
    s_non_choisis_set = set()
    for idx in lot_non_choisis_df.index:
        s_non_choisis_set.add(lot_non_choisis_df.loc[idx, 'id_system'])

    tempo = "\n{0} systèmes non choisis :".format(len(s_non_choisis_set))
    print(tempo)
    if len(s_non_choisis_set) != 0:
        print(s_non_choisis_set)
    print()
    lst_journal.append(tempo + '\n')

    # placer le contenu de s_non_choisis_set dans le log
    #
    tempo = "{"
    for i in range(len(list(s_non_choisis_set))):
        tempo = tempo + "'" + list(s_non_choisis_set)[i] + "', "
    tempo = tempo.rstrip(", ")
    tempo = tempo + "}\n"
    lst_journal.append(tempo)

    # créer un set des id_system choisis
    #
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

    # indiquer le mode de validation
    #
    if mode_validation:
        tempo = 12 * "*" + " MODE VALIDATION - AUCUN DOSSIERS CRÉÉ " + 12 * '*'
        print('\n' + tempo + '\n')
        lst_journal.append('\n' + tempo + '\n')

    # sélectionner et traiter chaque système présent dans s_choisis_set
    #
    lst_journal.append("\n")
    for nom_systeme in s_choisis_set:
        systeme_courant_df = lot_choisis_df.query("id_system == '" + nom_systeme + "'")
        tempo = "{0:<7} :".format(systeme_courant_df.iloc[0].id_system)
        print(tempo)

        lst_journal.append(tempo + '\n')

        # déterminer index de l'enregistrement système
        #
        idx_systeme = systeme_courant_df.query("paire == 'système'").index
        if len(idx_systeme) == 0:
            tempo = "  {0:<7} : pas d'enregistrement système dans le fichier du lot."\
                .format(systeme_courant_df.iloc[0].id_system)
            print(tempo + "\n")
            lst_journal.append(tempo)
        else:
            # créer le dossier du système
            #
            objet_systeme_courant = cree_dossier_systeme(systeme_courant_df.loc[idx_systeme])

            # enlever l'enr de système dans systeme_courant_df
            #
            paires_df = systeme_courant_df.drop(index=idx_systeme)

            # créer le dossier de chaque paire et le sous-dossier de programme d'observation dans ce dossier
            #
            #debug print("  Dossiers des paires et programmes :")
            #debug lst_journal.append("  Dossiers des paires et programmes :" + '\n')
            for idx in paires_df.index:
                pr = paires_df.loc[idx].paire
                prog = paires_df.loc[idx].programme
                if not do.estNan(pr) and not do.estNan(prog) and do.est_un_programme(prog.upper()):
                    OKres = creer_dossier_paire_et_prog(objet_systeme_courant, paire=pr, programme=prog)
                    tempo = "    '{0}' / '{1}' ".format(pr, prog)
                    if OKres:
                        tempo = tempo + 'CRÉÉ'
                    else:
                        tempo = tempo + 'ERREUR'
                    print(tempo)
                    lst_journal.append(tempo + '\n')
                else:
                    tempo = "    '{0}' / '{1}' <--- paire / programme non valides !".format(pr, prog)
                    print(tempo)
                    lst_journal.append(tempo + '\n')
            print()
            lst_journal.append('\n')


    # compéter le log et l'écrire sur disque
    #

    print("Le journal est dans «{0}»".format(ncfl_journal))

    # indiquer de nouveau le mode de validation
    #
    if mode_validation:
        tempo = 12 * "*" + " MODE VALIDATION - AUCUN DOSSIERS CRÉÉ " + 12 * '*'
        print('\n' + tempo + '\n')
        lst_journal.append('\n' + tempo + '\n')

    lst_journal.append("*** Traitement terminé ! ***")
    with open(ncfl_journal, 'w', encoding='UTF-8') as f:
        f.writelines(lst_journal)

    print("\n*** Traitement terminé ! ***")

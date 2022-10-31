Help on module doubleslistes:

NAME
    doubleslistes

DESCRIPTION
    # -*- coding: utf-8 -*-
    #! /usr/bin/env python
    ############
    # version 10
    ############

FUNCTIONS
    est_un_programme(chemin)
          Retourne True | False si le chemin passé en paramètre est un programme
          d'observation valide selon le format Paaaa-nnn; où aaaa = année
          et nnn = 000 à 999 (par ex. P2022-004).
          
        Paramètre positionnel
         chemin -- chemin du répertoire à vérifier.
    
    est_une_paire(chaine)
        Retourne un Tupple (True, paire) si la chaine (nom d'un répertoire) passée
        en paramètre «semble» être une paire valide. La valeur paire est extraire
        de chaine pour servir à une forme de normalisation.
        
        Retourne (False, 'aucune') si chaine ne «semble» pas être une paire valide.
          
        Paramètre positionnel
         chaine -- String nom de du répertoire (basename) à vérifier.
    
    imprime_liste_programmes(chemin='', tri=0, impr_table_etat=True, sortie='T')
        Imprime un rapport détaillé des programmes d'observation et retourne un
        Pandas DataFrame contenant la liste triée des programmes d'observation
        et leurs états.
        
        Paramètres Keyword
         chemin          -- String chemin du répertoire de tête des systèmes
         tri             -- Int ordre de tri de 1 à 4, selon dictionnaire
                            liste_de_tri_prog
         impr_table_etat -- Boolean imprime légende des états (par défaut True)
         sortie          -- Car 'T' pour terminal ou 'D' pour disque
        
        Returns
        -------
        programmes_df : pandas.core.frame.DataFrame
    
    imprime_liste_reductions(chemin='', tri=0, impr_table_etat=True, sortie='T')
        Imprime un rapport détaillé des programmes d'observations et retourne un
        Pandas DataFrame trié contenant la liste des programmes d'observations.
        
        Paramètres Keyword
         chemin          -- String chemin de tête des systèmes (par défaut '')
         tri             -- Int ordre de tri de 1 à 4, selon dictionnaire
                            liste_de_tri_prog
         impr_table_etat -- Boolean imprime légende des états (par défaut True)
         sortie          -- T (terminal) ou F (fichier)
    
    liste_info_systemes(sortie='terminal')
        Retourne un pandas dataframe des info_systemes.csv lus dans ./med.
    
    produire_liste_progammes(ch)
        Parcoure le chemin ch et retourne un pandas dataframe des programmes
        d'observations.
        
        Paramètre positionnel
        ch -- String chemin complet de la tête du répertoire des systèmes.
    
    produit_liste_reductions(chemin_des_systemes)
        Balais chemin_des_systemes et retourne une liste (List) des noms complets des fichiers
        *.obj trouvés.
        
        Paramètre positionnel
         chemin_des_systemes -- String chemin complet de la tête du répertoire des systèmes.
    
    trouverFichierObjetSessions(ch)
        Retourne le nom du fichier log de réduction (REDUC) RLog_*.txt 
        si présent dans le chemin passé en paramètre une chaîne vide sinon.
        
        Paramètre positionnel :
        ch -- String chemin du dossier d'où commencer la recherche.
    
    version()
        # %% FONCTIONS

DATA
    liste_de_tri_prog = [['obs_prog', 'id_system'], ['id_system', 'obs_pro...
    liste_de_tri_reduc = [['obs_prog', 'id_system'], ['id_system', 'obs_pr...
    maintenant = <Time object: scale='utc' format='datetime' value=2022-10...
    nversion = 20

FILE
    d:\documents\astronomie\dev\astrodm\doubleslistes.py



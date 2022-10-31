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
          Retourne True | False si le chemin pass� en param�tre est un programme
          d'observation valide selon le format Paaaa-nnn; o� aaaa = ann�e
          et nnn = 000 � 999 (par ex. P2022-004).
          
        Param�tre positionnel
         chemin -- chemin du r�pertoire � v�rifier.
    
    est_une_paire(chaine)
        Retourne un Tupple (True, paire) si la chaine (nom d'un r�pertoire) pass�e
        en param�tre �semble� �tre une paire valide. La valeur paire est extraire
        de chaine pour servir � une forme de normalisation.
        
        Retourne (False, 'aucune') si chaine ne �semble� pas �tre une paire valide.
          
        Param�tre positionnel
         chaine -- String nom de du r�pertoire (basename) � v�rifier.
    
    imprime_liste_programmes(chemin='', tri=0, impr_table_etat=True, sortie='T')
        Imprime un rapport d�taill� des programmes d'observation et retourne un
        Pandas DataFrame contenant la liste tri�e des programmes d'observation
        et leurs �tats.
        
        Param�tres Keyword
         chemin          -- String chemin du r�pertoire de t�te des syst�mes
         tri             -- Int ordre de tri de 1 � 4, selon dictionnaire
                            liste_de_tri_prog
         impr_table_etat -- Boolean imprime l�gende des �tats (par d�faut True)
         sortie          -- Car 'T' pour terminal ou 'D' pour disque
        
        Returns
        -------
        programmes_df : pandas.core.frame.DataFrame
    
    imprime_liste_reductions(chemin='', tri=0, impr_table_etat=True, sortie='T')
        Imprime un rapport d�taill� des programmes d'observations et retourne un
        Pandas DataFrame tri� contenant la liste des programmes d'observations.
        
        Param�tres Keyword
         chemin          -- String chemin de t�te des syst�mes (par d�faut '')
         tri             -- Int ordre de tri de 1 � 4, selon dictionnaire
                            liste_de_tri_prog
         impr_table_etat -- Boolean imprime l�gende des �tats (par d�faut True)
         sortie          -- T (terminal) ou F (fichier)
    
    liste_info_systemes(sortie='terminal')
        Retourne un pandas dataframe des info_systemes.csv lus dans ./med.
    
    produire_liste_progammes(ch)
        Parcoure le chemin ch et retourne un pandas dataframe des programmes
        d'observations.
        
        Param�tre positionnel
        ch -- String chemin complet de la t�te du r�pertoire des syst�mes.
    
    produit_liste_reductions(chemin_des_systemes)
        Balais chemin_des_systemes et retourne une liste (List) des noms complets des fichiers
        *.obj trouv�s.
        
        Param�tre positionnel
         chemin_des_systemes -- String chemin complet de la t�te du r�pertoire des syst�mes.
    
    trouverFichierObjetSessions(ch)
        Retourne le nom du fichier log de r�duction (REDUC) RLog_*.txt 
        si pr�sent dans le chemin pass� en param�tre une cha�ne vide sinon.
        
        Param�tre positionnel :
        ch -- String chemin du dossier d'o� commencer la recherche.
    
    version()
        # %% FONCTIONS

DATA
    liste_de_tri_prog = [['obs_prog', 'id_system'], ['id_system', 'obs_pro...
    liste_de_tri_reduc = [['obs_prog', 'id_system'], ['id_system', 'obs_pr...
    maintenant = <Time object: scale='utc' format='datetime' value=2022-10...
    nversion = 20

FILE
    d:\documents\astronomie\dev\astrodm\doubleslistes.py



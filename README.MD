# Package astrodm

## INTRODUCTION

Le package astrodm; [**a**stronomie **d**oubles **m**esures] contient un seul module : **doublesoutils**, écrit en langage Python. Ce module comprend différentes classes d'objets qui exposent des méthodes et des attributs qui visent à assister l'observateur dans la planification et le suivi des observations ainsi que la réduction des mesures de l'angle de position ( $\theta$ ) et la séparation ( $\sigma$ ) des étoiles doubles.

astrodm propose également des scripts d'exploitation qui permettent de produire différentes listes afin d'assister à la planification et au suivi, au jour le jour des observations.

### Mode d'exploitation du package

Ce package ne nécessite aucune installation (voir figure 1) car il est destiné à être exécuté dans un IDE, par exemple Anaconda. Chaque script d'exploitation indiqué plus bas, lorsqu'exécuté dans le terminal d'un tel IDE, comprend un point d'entrée qui prépare l'environnement d'exécution pour l'importation du package astrodm. Lorsqu'un script se termine, l'espace de noms (variables) est complètement préservé. De cette façon, certaines variables qui contiennent des objets demeurent disponibles avec leur méthodes et leurs attributs. Par exemple, le contenu d'une liste pourra être modifié et trié différemment.

### Emplacement du package

![Figure 1 : Emplacement du package astrodm.](astrodm-doc/images/emplacement-package.jpg)

**Figure 1** : Emplacement du package astrodm.

### Les scripts d'exploitation

La figure 2 donne la liste des scripts et montre également l'emplacement des scripts d'exploitation. Il est recommandé d'exécuter les scripts dans le même répertoire qui contient les sous-répertoires **med** et **modeles**.  Dans ce repo, le répertoire **data** respecte cette configuration. Certains scripts exploitent automatiquement le contenu des sous-répertoires **med** et **modeles** situés dans **data**, alors que d'autres scripts permettent la sélection interactive de fichiers sans d'autres répertoires.

![Figure 2 : ](astrodm-doc/images/scripts-exploitation.jpg)

**Figure 2** : Emplacement des scripts d'exploitation dans le répertoire data. Les répertoires **med** et **modeles** sont automatiquement exploités par certains scripts.

### Observation des étoiles doubles - sommaire des flux de travail

Le méthodologie de travail se décline en six flux de travail :

 1. Planification, recherche et production des listes d'observation
 2. Préparation des sessions d'observations (astroplan)
 3. Acquisition des données
 4. Pré-réduction des données d'observations
 5. Post-réduction des données d'observations
 6. Publication des résultats

![Figure 3](astrodm-doc/images/astrodm-flux.jpg)
**Figure 3** : Cheminement des six flux de travail d'observation d'étoiles doubles.

### Petit lexique

Quelques notes concernant le vocabulaire utilisé dans ce repo.

* WDS : le Washington Doubles Star Catalog.
* Système : un système d'étoiles doubles (ou multiples) en général, selon la désignation de découvreur du WDS (Discoverer & Number); par ex. STTA 254 ou STF 60.
* paire : désignation de la paire, par ex. AB, A,BC selon l'appartenance dans le catalogue WDS.

## 1.0 Travail de planification et recherche

### Description du travail de planification et de recherche

Ce flux de travail commence d'abord par la création, à l'aide d'un script, de la structure de répertoires et des fichiers de bases qui appartiennent au système (figure 4).  Les recherches au sujet du système se poursuivent dans les bases de données en-ligne, les livres et les site web pour documenter le système étudié. Les notes issues de ce travail sont consignées dans un cahier Jupyter Lab (figure 5) qui se trouve dans le répertoire **planif** du système.

Ce travail permettra par la suite d'identifier les paires qui méritent d'être observées au sein du système étudié.

La figure 4 montre le répertoire du système STTA254 : un sous-répertoire est créé pour chaque paire sélectionnée pour ce système et finalement un autre sous-répertoire nommé avec le numéro du programme d'observation est créé afin d'assigner ce programme d'observation à cette combinaison système-paire. C'est ce programme d'observation qui facilitera le suivi de toutes les activités d'acquisition de données d'observations et de pré/post-réductions des données.

![Figure 4](astrodm-doc/images/systeme-stta254-structure-repertoires.jpg)

**Figure 4** : Structure des répertoires du système WDS STTA254. Le programme d'observation P2021-023 est assigné à la paire AB.

![Figure 5](astrodm-doc/images/systeme-contenu-planif.jpg)

**Figure 5** : Contenu du sous-répertoire **planif** du système WDS STTA254. Le cahier Jupyter Lab « systeme-notes.ipynb » contient les notes de recherche du système.

## 1.1 - Création de la structure de base des répertoires d'un système

* Script : cree_systeme.py
* Mode : IDE (SPYDER), menus et autres intéractions.
* Sortie : au terminal IPython pour les interractions.
* Retourne : Sous-répertoires créés dans le répertoire **med**.
* Fonctionnalités supplémentaire :
* * Seuls les systèmes valides (qui existent dans le WDS) peuvent être créés.
* * Seulement lors de création initiale du dossier, le script copie le modèle du cahier Jupyter «système_notes.ipynb»’ dans dossier planif du système. Ce fichier sert de modèle pour les cahiers d’observation qui se trouveront dans le dossier de chaque paire / programme.

![Figure 6](astrodm-doc/images/cree-systeme-menu.jpg)

**Figure 6** : Menu du script cree-systeme.py

### PROCÉDURE

* 1.1.1 Option 1 - Sélection, lecture et modification d'un fichier information de système : lit un fichier *_info_système.csv et permet de le modifier.

* 1.1.2 Option 2 Saisie de l'ID WDS du système : pour créer un système à neuf. Vérifie si dossier existe déjà et demande de confirmer exécution.

  ATTENTION si exécution confirmée, les informations originales seront écrasées.

* 1.1.3 Option 3 - Traitement d'un lot dans une feuille de calcul.

Voir figure 7.

  * SÉLECTION interactive du fichier lot (*.ods) dans .\data\med-planification\LOTS.
  * Colonne A et E obligatoires; INSCRIRE 1 dans la colonne « choisir » (E).
  * Si le fichier info-systeme du système existe déjà, tout le contenu sera mis à jour.
  * Le fichier lot peut être utilisé autant de fois que désiré.
  * Le log de chaque exécution se trouve dans .\data\med-planification\LOTS.

![Figure 7](astrodm-doc/images/structure-fichier-lot.png)

**Figure 7** : Exemple de la structure d'un fichier de traitement en lot. Seules les colonnes A et E sont obligatoires. Inscrire 1 dans la colonne « choisir » pour assurer le traitement.

## 1.2 - Création des listes de suivi

* 1.2.1 Liste des fichiers d'information des systèmes pour l'ensemble du répertoire **med**

  * Script : _Liste_info_systemes.py_
  * Mode : IDE (SPYDER), par sélection de l'ordre de tri dans un menu.
  * Sortie : au terminal IPython ou capture dans un fichier texte.
  * Retourne : la variable _info-systèmes_df_ qui contient la liste sous forme d'un dataframe Pandas.
  * Fonctionnalités supplémentaires : les méthodes suivantes du dataframe Pandas permettent de changer la sélection et l'ordre de tri. TODO.
  * Pour exemples voir <https://github.com/stardom1957/med-planification/tree/main/LISTES>, fichiers qui commencent par « info-sys-par( ».

#### 1.2.2 Liste des programmes d'observation et de leurs états

* Script : _liste_programmes.py_
* Mode : IDE (SPYDER), par sélection de l'ordre de tri dans un menu.
* Sortie : au terminal IPython ou capture dans un fichier texte.
* Retourne : la variable _liste_des_programmes_df_ qui contient la liste sous forme d'un dataframe Pandas.
* Fonctionnalités supplémentaires : les méthodes suivantes du dataframe Pandas permettent de changer la sélection et l'ordre de tri. TODO.
* Pour exemples voir <https://github.com/stardom1957/med-planification/tree/main/LISTES>, fichiers qui commencent par « prog-obs-par( ».

#### 1.2.3 Liste des réductions et des résultats pour publication

* Script : _liste_reductions.py_
* Mode : IDE (SPYDER), par sélection interactive du répertoire du programme d'observation.
* Sortie : au terminal IPython ou capture dans un fichier texte.
* Retourne : la variable _reductions_ qui contient la liste sous forme d'un dataframe Pandas.
* Fonctionnalités supplémentaires : les méthodes suivantes du dataframe Pandas permettent de changer la sélection et l'ordre de tri. TODO.
* Pour exemples voir <https://github.com/stardom1957/med-planification/tree/main/LISTES>, fichiers qui commencent par « reductions-par( ».

#### 1.2.4 Recherches des données des systèmes dans le catalogue WDS

#### 1.2.4.1 - Recherche d'un seul système (incluant notes WDS associées si applicable)

* Script : _recherche_wds.py_
* Mode : IDE (SPYDER), par saisie au clavier du nom WDS (découvreur et ID numérique).
* Sortie : au terminal IPython seulement.
* Retourne : aucune variable retournée.
* Fonctionnalités supplémentaires : l'existance du systèmes est automatiquement validée.

#### 1.2.4.2 - Recherche de plusieurs systèmes (sans les notes WDS)

* Script : _recherche_wds_multiples.py_
* Mode : IDE (SPYDER), par sélection interactive du fichier texte contenant les nom des systèmes (figure 8).
* Sortie : au terminal IPython ou dans un fichier texte (TODO).
* Retourne : la variable _collige_, un objet astroquery.utils.commons.TableList.
* Fonctionnalités supplémentaires : l'existance de chaque système est automatiquement validée et les doublons ne sont pas pris en compte. Certaines méthodes de l'objet _collige_ peuvent être utilisées pour rafiner la recherche (TODO).

![Figure 8](astrodm-doc/images/liste-sources.jpg)

**Figure 8** : Un exemple de fichier liste de systèmes multiples.

## 2.0 Travail de planification des observations - éphémérides

À développer. TODO.

## 3.0 Travail d'acquisition des données d'observation

### Description du travail d'acquisition des données

Le travail d'acquisition des données comprend la capture des images et la saisie des fichiers d'environnement (environnement.txt) pour les calibrations d'échelle (ech), les mesures de séparation (sep) et (d'angle) de position (pos). Lors des acquisitions sep et pos, l'acquisition de fichiers de calibration d'images darks et biases (cal) est facultative.

La **figure 9** illustre en détail la structure de fichiers pour l'acquition des données pour les observations de la paire STTA254AB dans le cadre du programme P2021-023, session 1, bloc 1.

La **figure 10** illustre en détail la structure de fichiers pour l'acquition des données pour les observations de l'acquisition d'échelle 2021-10-08b01.

![Figure 9](astrodm-doc/images/struct-donnees-observation.jpg)

**Figure 9** : Exemple de structure des données pour l’acquisition de sep et pos.

![Figure 10](astrodm-doc/images/struct-donnees-echelle.jpg)

**Figure 10** : Exemple de structure des fichiers d'acquisition d'échelle (ech).

PROCÉDURES

### 3.1. Acquisition des données de calibration d’échelle (ech)

* 3.1.1. pour la structure de données, voir la figure 10.

* 3.1.2. Le fichier log environnement.txt est REQUIS. Le modèle se trouve dans D:\DOCUMENTS\Astronomie\Data\modeles\AAAA-MM-JJb01. Pour un exemple, voir la figure 11.

* 3.1.3. Dans le fichier environnement.txt,  les valeurs de temp_to, masque, filtre et map doivent IMPÉRATIVEMENT être renseignées. 

* 3.1.4. Durant l'acquisition des images avec FireCapture, le fichier log au format txt est automatiquement créé dans le répertoire de saisie des images. Ce fichier porte le nom donné au moment de la création du profil d'acquisiton.

![Figure 11](astrodm-doc/images/environnement_txt_cal_exemple.jpg)

**Figure 11** : Un exemple de fichier log environnement.txt pour une acquisition de calibration d'échelle.

### 3.2. Acquisition des données de séparation (sep)

* 3.2.1. Pour la structure de données, voir la figure 9.

* 3.2.2. Le fichier log environnement.txt est REQUIS. Le modèle se trouve dans D:\DOCUMENTS\Astronomie\Data\modeles\systeme\Paire\PAAAA-nnn\Sx\b01\sep\environnement.txt. Pour un exemple, voir la figure 12.

* 3.2.3. Dans le fichier environnement.txt, les valeurs de temp_to, index_cal_E et map doivent IMPÉRATIVEMENT être renseignées.

* 3.2.4.  Durant l'acquisition des images avec FireCapture, le fichier log au format txt est automatiquement créé dans le répertoires de saisie des images. Ce fichier porte le nom donné au moment de la création du profil d'acquisiton..

![Figure 12](astrodm-doc/images/environnement_txt_sep_exemple.jpg)

**Figure 12** : Un exemple de fichier log environnement.txt pour une acquisition de séparation.

### 3.3. Acquisition des données (d’angle) de position (pos)

* 3.3.1. Pour la structure de données, voir la figure 9.

* 3.3.2. Le fichier log environnement.txt est REQUIS. Le modèle se trouve dans D:\DOCUMENTS\Astronomie\Data\modeles\systeme\Paire\PAAAA-nnn\Sx\b01\pos\environnement.txt. Pour un exemple, voir la figure 13.

* 3.3.3. Dans le fichier environnement.txt, les valeurs de temp_to et map doivent IMPÉRATIVEMENT être renseignées.

* 3.3.4.  Durant l'acquisition des images avec FireCapture, le fichier log au format txt est automatiquement créé dans le répertoires de saisie des images. Ce fichier porte le nom donné au moment de la création du profil d'acquisiton..

![Figure 13](astrodm-doc/images/environnement_txt_pos_exemple.jpg)

**Figure 13** : Un exemple de fichier log environnement.txt pour une acquisition (d'angle) de position.

## 4.0 Travail de pré-réduction

### Description du travail de pré-réduction

- Structure de données selon figure 5 pour acquisition d'observation ou 6 pour une acquisition d'échelle.

### Utilisation de REDUC

La pré-réduction s’effectue avec le logiciel REDUC en travaillant simultanément dans deux instances de ce logiciel : une instance s’occupe de la réduction de pos et l’autre celle de sep.

À l’aide de REDUC, la procédure de réduction complète suivante est répétée pour chaque bloc d’observation (b01, b02, …).

### SOMMAIRE Pré-réduction POS et SEP

On effectue d’abord la réduction de POS afin d’obtenir l’orientation de l’image delta_matrix. Le log de la réduction POS est inscrit dans un fichier Rlog… pos\reduc\Rlog*.txt.  On effectue ensuite (ou simultanément) la réduction de sep et on copie le delta_matrix de pos dans delta_matrix de sep. Le log de la réduction sep est versé dans un fichier Rlog… dans sep\reduc.

PROCÉDURE

4.1 Pré-réduction ‘complete’ (pos et sep):

    4.1.1. pos : voir logigramme PRÉ-RÉDUCTION-POS

    4.1.2. sep :  voir logigramme PRÉ-RÉDUCTION SEP ou ECH

4.2. Pré-réduction d'échelle (‘ech’) : voir logigramme PRÉ-RÉDUCTION SEP ou ECH

## 5.0 Travail de post-réduction

Pré-requis

- peut être exécutée à n’importe quel moment lorsque qu’il y a au moins une pré-réduction complétée pour un des blocs d’une session.

PROCÉDURE

5.1. Post-réduction :

    5.1.1. Au terminal ipython (Spyder, par ex. ) : exécuter le script reduction_*.py. Il s’agit du mode interactif; le script demande le chemin du programme et exécute la réduction.

    5.1.2. Dans le cahier de notes Jupyter Lab, exécuter la ligne suivante :

```do.post_reduction(type_session='complete', ch_prog=’chemin_du_programme’)```

    5.1.3. Suite à la post-réduction, dans les deux cas :
    - le log de post-réduction «post-réduction.log» placé dans le dossier de programme donne un bref apperçu du résultat de la post-réduction.
    - Le fichier ‘*_sessions.obj’ est un pickle d’un objet de classe astrodm.DoubleSessionsComplete.

5.2. Exploitation de l’objet issue du script du script reduction *.py.

# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 16:31:40 2020

@author: dominique
"""
'''
from astroquery.utils.tap.core import TapPlus
gaia = TapPlus(url="https://gea.esac.esa.int/tap-server/tap")
tables = gaia.load_tables(only_names=True)
for table in (tables):
    print(table.get_qualified_name())
'''    
### imports
from astroquery.vizier import Vizier as v
import sys

### FONCTIONS
def info_astrometriques(source, paire):
    v.CACHE = False
    v.ROW_LIMIT = 33 # au cas où ?
    ### recherche dans WDS
    result = v.query_constraints(catalog='B/wds/wds', Disc=source, Comp=paire)
    return result




#cat_list = v.find_catalogs('B/wds')
#wds_notes = v.get_catalogs('B/wds/notes')
#result = v.query_constraints(catalog='B/wds/wds', Disc='STF 205', Comp='A,BC')

### recherche Vizier.query_constraints

strSource = 'stf  60'.upper()

# caractères de remplacement ? et * acceptés
strComp = '*'.upper()

### recherche dans WDS
qres = info_astrometriques(strSource, strComp)
#result = v.query_constraints(catalog='B/wds/wds', Disc= strSource)

if qres != []:
    print('#' * 20)
    longueur = qres[0].__len__()
    print('Il y a {0} résultats pour {1}.'.format(longueur, strSource))
    # qres[0].pprint(show_unit=True, max_width=120)
    # trier sur WDS et composants
    qres[0].sort(['Disc', 'Comp'])
    #result[0].sort(['Comp'])
    #qres[qres.keys()[0]].pprint()
    
    print('\nAprès tri\n')
    qres[0].pprint(show_unit=True, max_width=120)
    print('#' * 20)

else:
    print("La requête pour '{0}' n'a donné aucun résultat".format(strSource))
    sys.exit()

print('\n\n')
print(qres[0][0])

print('\nWDS : {0} {1:3d}° / {2:4.2f}"\n'.format(qres[0][0]['Obs2'], qres[0][0]['pa2'], qres[0][0]['sep2']))

for r in range(longueur):
    #print(r+1, ' ', qres[0][r]['WDS'], qres[0][r]['Disc'], result[0][r]['Comp'])
    print('{0:>4d} J{1:>10s} {2:>7s} {3:>5s} '.format(r+1, qres[0][r]['WDS'], qres[0][r]['Disc'], qres[0][r]['Comp']))


### recherche dans WDS Notes
wds_notes = v.query_constraints(catalog='B/wds/notes', Disc=strSource)
if wds_notes != []:
    wds_notes[0].pprint(max_width=120)

### tap vizier
req = '''SELECT TOP 100 "B/wds/wds".WDS,  "B/wds/wds".Disc,  "B/wds/wds".Comp,  "B/wds/wds".Obs1,  "B/wds/wds".Obs2,  "B/wds/wds".pa1,  "B/wds/wds".pa2, 
 "B/wds/wds".sep1,  "B/wds/wds".sep2,  "B/wds/wds".mag1,  "B/wds/wds".mag2,  "B/wds/wds".pmRA1,  "B/wds/wds".pmDE1,  "B/wds/wds".DM,  "B/wds/wds".Notes, 
 "B/wds/wds".n_RAJ2000,  "B/wds/wds".RAJ2000,  "B/wds/wds".DEJ2000
 FROM "B/wds/wds"
 WHERE "B/wds/wds".Disc = 'STF 205'''
 
'''
SELECT TOP 100 "B/wds/wds".WDS,  "B/wds/wds".Disc,  "B/wds/wds".Comp,  "B/wds/wds".Obs1,  "B/wds/wds".Obs2,  "B/wds/wds".pa1,  "B/wds/wds".pa2, 
 "B/wds/wds".sep1,  "B/wds/wds".sep2,  "B/wds/wds".mag1,  "B/wds/wds".mag2,  "B/wds/wds".pmRA1,  "B/wds/wds".pmDE1,  "B/wds/wds".DM,  "B/wds/wds".Notes, 
 "B/wds/wds".n_RAJ2000,  "B/wds/wds".RAJ2000,  "B/wds/wds".DEJ2000
 FROM "B/wds/wds"
 '''
### recherche dans Hipparcos
h_result = v.query_constraints(catalog='I/239/hip_main', recno='110896')
h_result[0].pprint(max_width=150)
h_result[0]['HIP', 'Notes']
#!/usr/bin/python3

#	Skript pro ziskani aktulani vystrahy pro zvolene mesto (na zaklade CISORP) z CHMI
#	API dokumentace: https://www.chmi.cz/files/portal/docs/meteo/om/vystrahy/doc/Dokumentace_CAP.pdf
#	IntEx, 2023

import sys
from datetime import datetime
import urllib.request
import xmltodict
import json

CISORP = "5309" # (string!) vychozi = Pardubice
if (len(sys.argv) > 1):
	CISORP = sys.argv[1] # CISORP z command-line parametru

DEBUG = False # vsechny dostupne vystrahy (bez omezeni aktualniho data)

URL = 'https://www.chmi.cz/files/portal/docs/meteo/om/bulletiny/XOCZ50_OKPR.xml'

# pomocne objekty
severity_string = {
	'Unknown':	'Předběžná', 
	'Minor':	'Minimální', 
	'Moderate':	'Nízká', 
	'Severe':	'Vysoká', 
	'Extreme':	'Extrémní'
}
severity_int = {
	'Unknown':	1, 
	'Minor':	2, 
	'Moderate':	3, 
	'Severe':	4, 
	'Extreme':	5
}

now = datetime.now().astimezone()

# stazeni dat
data = urllib.request.urlopen(URL)

# konverze na slovnik
source = xmltodict.parse(data)

alerts = []

# pruchod pres vystrahy
for alert_info in source['alert']['info']:
	# jazyk hlaseni
	if (alert_info['language'] != 'cs'):
		continue # jen ceska hlaseni
	
	# druh hlaseni
	if (alert_info['responseType'] == 'None'):
		continue; # jen aktivni hlaseni
		
	# datum hlaseni
	expire = datetime.fromisoformat(alert_info['expires'])
	if (now > expire and not DEBUG):
		continue; # jen aktualni hlaseni

	# pruchod pres oblasti
	cisorp_related = False
	area_desc = None
	for area in alert_info['area']:

		#pruchod pres mesta
		for city in area['geocode']:
			if isinstance(city, str):
				continue # nevalidni hodnota

			if (city['valueName'] == 'CISORP' and city['value'] == CISORP):
				cisorp_related = True
				area_desc = area['areaDesc']; # jakeho kraje se to tyka
				break # tyka se mesta
			
		if (cisorp_related):
			break # tyka se oblasti

	if (not cisorp_related):
		continue # hlaseni se mesta (= oblasti) netyka
	
	# vystraha
	alert = {
		'cisorp': CISORP,
		'area': area_desc,
		'event': alert_info['event'],
		'onset': alert_info['onset'],
		'expires': alert_info['expires'],
		'severityLevel': severity_int[alert_info['severity']],
		'severity': severity_string[alert_info['severity']],
		'description': alert_info['description'],
		'instructions': alert_info['instruction']
	}

	alerts.append(alert)


# JSON vystup
if (len(alerts) == 0):
	alert = {
		'cisorp': CISORP,
		'event': "Žádná výstraha",
		'severityLevel': 0
	}
	print(json.dumps(alert)) # neni vystraha ("prazdne" hlaseni)
else:
	alerts.sort(key=lambda alert: alert['severityLevel'], reverse=True) # vyssi dulezitost nahore
	print(json.dumps(alerts[0])) # pouze nejdulezitejsi vystraha

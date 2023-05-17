#!/usr/bin/python3

#	Skript pro ziskani aktulani vystrahy pro zvolene mesto (na zaklade CISORP) z CHMI
#	API dokumentace: https://www.chmi.cz/files/portal/docs/meteo/om/vystrahy/doc/Dokumentace_CAP.pdf
#  	Ciselnik CISORP: https://apl.czso.cz/iSMS/cisdet.jsp?kodcis=65
#	IntEx, 2023

import sys
from datetime import datetime
import urllib.request
import xmltodict
import json
import traceback

CISORP = "5309" # (string!) vychozi = Pardubice
if (len(sys.argv) > 1):
	CISORP = sys.argv[1] # CISORP z command-line parametru

INCLUDE_EXPIRED = False # zahrnout vystrahy bez omezeni aktualniho data
DEBUG = False # ladici informace

URL = 'https://www.chmi.cz/files/portal/docs/meteo/om/bulletiny/XOCZ50_OKPR.xml'

# stazeni dat
try:
	data = urllib.request.urlopen(URL, timeout=30)
except:
	alert = {
		'cisorp': CISORP,
		'event': "Chyba stažení dat!",
		'description': traceback.format_exc(), 
		'severityLevel': 5
	}
	print(json.dumps(alert)) # chyba stazeni dat
	exit() # konec skriptu

# konverze na slovnik
try:
	source = xmltodict.parse(data)
except:
	alert = {
		'cisorp': CISORP,
		'event': "Chyba konverze dat!",
		'description': traceback.format_exc(), 
		'severityLevel': 5
	}
	print(json.dumps(alert)) # chyba konverze dat
	exit() # konec skriptu

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

# Hledani geocodu
def scanGeocode(gcListOrDict):
	if (isinstance(gcListOrDict, dict)):
		# slovnik (jeden gc)
		if (DEBUG):	
			print(gcListOrDict['value'])
		if (gcListOrDict['valueName'] == 'CISORP' and gcListOrDict['value'] == CISORP):
			if (DEBUG):
				print("^^^^ MATCH!")
			return True
	
	if (isinstance(gcListOrDict, list)):		 
		# seznam (vice gc)
		for gc in gcListOrDict:
			if isinstance(gc, str):
				if (DEBUG):
					print(gc + " (invalid, skipped)")
				continue # nevalidni hodnota

			if (DEBUG):	
				print(gc['value'])
			
			if (gc['valueName'] == 'CISORP' and gc['value'] == CISORP):
				if (DEBUG):
					print("^^^^ MATCH!")
				return True
		
	return False

# pruchod pres vystrahy
try:
	alerts = []
	for alert_info in source['alert']['info']:
		# jazyk vystrahy
		if (alert_info['language'] != 'cs'):
			continue # jen ceske
		
		# druh vystrahy
		if ('responseType' in alert_info and alert_info['responseType'] == 'None'):
			continue # jen aktivni
			
		# datum vystrahy
		expire = datetime.fromisoformat(alert_info['expires'])
		if (now > expire and not INCLUDE_EXPIRED):
			continue # jen aktualni
			
		if (DEBUG):
			print("Event: " + alert_info['event'])
			print("Onset: " + alert_info['onset'])
			print("Expires: " + alert_info['expires'])
			if (now > expire):
				print("(expired)")

		# prohledani zasazenych kraju
		if (DEBUG):
			print("Affected areas with geocodes:")

		cisorp_related = False
		area_desc = None
		
		if (isinstance(alert_info['area'], dict)):
			# jeden kraj
			if (DEBUG):
				print(alert_info['area']['areaDesc'] + " [SINGLE AREA]")
			# pruchod pres mesta
			if (scanGeocode(alert_info['area']['geocode'])):
				cisorp_related = True
				area_desc = alert_info['area']['areaDesc']; # jakeho kraje se to tyka	
		
		if (isinstance(alert_info['area'], list)):
			# vice kraju
			for area in alert_info['area']:
				if (DEBUG):
					print(area['areaDesc'])			
				# pruchod pres mesta
				if (scanGeocode(area['geocode'])):
					# tyka se mesta
					cisorp_related = True
					area_desc = area['areaDesc']; # jakeho kraje se to tyka
					break
				
		if (DEBUG):
			print()

		if (not cisorp_related):
			continue # hlaseni se mesta (= kraje) netyka

		# udaje vystrahy
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
		alerts.append(alert) # pridani vystrahy do seznamu vystrah

except:
	alert = {
		'cisorp': CISORP,
		'event': "Chyba zpracování dat!",
		'description': traceback.format_exc(), 
		'severityLevel': 5
	}
	print(json.dumps(alert)) # chyba zpracovani dat
	exit() # konec skriptu

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

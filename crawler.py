import requests, json, os
from datetime import datetime, date, timedelta
from bs4 import BeautifulSoup

# GET SECTIONS
def getSections(html):

	soup = BeautifulSoup(html, "html.parser")
	return soup.find(id="noonsite-sections")

def downloadSection(country, section):
	p = requests.get(country["url"] + "?rc=" + section)
	countryHtml = p.text

	return getSections(countryHtml)

# DOWNLOAD PROFILE
def downloadProfile(country):
	return downloadSection(country, "CountryProfile")
	
# DOWNLOAD FORMATLITIES
def downloadFormalities(country):
	return downloadSection(country, "Formalities")

def downloadGeneralInfo(country):
	return downloadSection(country, "GeneralInfo")

# DOWNLOAD COUNTRIES
def downloadCountries():

	countries = {}

	c = requests.get("http://www.noonsite.com/Countries")
	countriesHtml = c.text

	soup = BeautifulSoup(countriesHtml, "html.parser")
	countrylListing = soup.find(id="noonsite-countries-listing")

	currentArea = None

	for child in countrylListing.contents:

		# new area
		if child.name == "h2":

			currentArea = child.get_text().strip()
			
		if child.name == "p":

			for a in child.find_all("a"):

				if not currentArea in countries:
					countries[currentArea] = []

				countries[currentArea].append({
					"name": a.get_text(),
					"url": a.get("href")
				})

	return countries

# download countries
countries = downloadCountries()

# store countries in json file
with open("data/countries.json", "w") as f:
	f.write(json.dumps(countries))

for area in countries:
	for country in countries[area]:
		profile = downloadProfile(country)
		formalities = downloadFormalities(country)
		generalinfo = downloadGeneralInfo(country)

		print country["name"]
		os.mkdir("data/" + country["name"] + "/")
		
		with open("data/" + country["name"] + "/profile.html", "w") as f:
			f.write(str(profile))

		with open("data/" + country["name"] + "/formalities.html", "w") as f:
			f.write(str(formalities))

		with open("data/" + country["name"] + "/general.html", "w") as f:
			f.write(str(generalinfo))
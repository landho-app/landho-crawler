import requests, json, os
from datetime import datetime, date, timedelta
from bs4 import BeautifulSoup
from slugify import slugify

# DOWNLOAD IMAGE
def downloadImage(url, path):

	if not url.startswith("http://www.noonsite.com"):

		if url.startswith("/"):
			url = "http://www.noonsite.com" + url
		else:
			url = "http://www.noonsite.com/" + url

	#print url

	r = requests.get(url, stream=True)
	if r.status_code == 200:

		if not os.path.exists(path):
			os.makedirs(path)

		if os.path.isdir(path):
			os.rmdir(path)

		if not os.path.exists(path):
			with open(path, "wb") as f:
				for chunk in r:
					f.write(chunk)

# GET SECTIONS
def getSections(country, html):

	soup = BeautifulSoup(html, "html.parser")
	sections = soup.find(id="noonsite-sections")

	# download images
	folder = "data/" + country["slug"]
	sectionStr = str(sections)

	for img in sections.find_all("img"):
		fileName = img.get("src").replace("http://www.noonsite.com", "")
		downloadImage(img.get("src"), folder + fileName)
		sectionStr = sectionStr.replace("src=\"http://www.noonsite.com", "src=\"")

	return sectionStr

def downloadSection(country, section):
	p = requests.get(country["url"] + "?rc=" + section)
	countryHtml = p.text

	return getSections(country, countryHtml)

# DOWNLOAD PROFILE
def downloadProfile(country):
	return downloadSection(country, "CountryProfile")
	
# DOWNLOAD FORMATLITIES
def downloadFormalities(country):
	return downloadSection(country, "Formalities")

# DOWNLOAD GENERALINFO
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

				countryHtml = requests.get(a.get("href")).text
				countrySoup = BeautifulSoup(countryHtml, "html.parser")
				flag = None
				for img in countrySoup.find_all("img"):
					if "flags" in img.get("src") and ".gif/image" in img.get("src"):
						flag = img.get("src").replace("http://www.noonsite.com", "")

				print a.get_text()
				countries[currentArea].append({
					"name": a.get_text(),
					"url": a.get("href"),
					"slug": slugify(a.get_text()),
					"flag": flag
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

		folder = "data/" + country["slug"]

		print country["name"]
		if not os.path.isdir(folder + "/"):
			os.mkdir(folder + "/")
		
		with open(folder + "/profile.html", "w") as f:
			f.write(str(profile))

		with open(folder + "/formalities.html", "w") as f:
			f.write(str(formalities))

		with open(folder + "/general.html", "w") as f:
			f.write(str(generalinfo))
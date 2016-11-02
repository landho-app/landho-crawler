import requests, json, os, sys
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

		if img != None and img.get("src") != None:
			fileName = img.get("src").replace("http://www.noonsite.com", "")

			downloadImage(img.get("src"), folder + fileName)
			sectionStr = sectionStr.replace("src=\"http://www.noonsite.com", "src=\"")

	cities = []
	for a in sections.find_all("a"):
		if a != None and a.get("href") != None and a.get("href").startswith(country["url"]) and len(a.get("href")) < 90:
			cities.append({
				"name": a.get_text().replace("*", "").strip(),
				"url": a.get("href"),
				"slug": slugify(a.get_text().replace("*", "").strip())
			})

	return sectionStr, cities

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

# DOWNLOAD CITY
def downloadCity(city):
	c = requests.get(city["url"])
	return getSections(city, c.text)

# DOWNLOAD COUNTRIES
def downloadCountries(getFlag=False):

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

				flag = None

				if getFlag == True:
					countryHtml = requests.get(a.get("href")).text
					countrySoup = BeautifulSoup(countryHtml, "html.parser")

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
print "BUILD COUNTRIES.JSON"
countries = downloadCountries(True)

# store countries in json file
with open("data/countries.json", "w") as f:
	f.write(json.dumps(countries))

sys.exit()

print "\n\n"
print "FETCH INDIVIDUAL CONTRIES"

for area in countries:
	for country in countries[area]:

		print country["name"]
		profile, cities = downloadProfile(country)
		formalities, bla = downloadFormalities(country)
		generalinfo, blub = downloadGeneralInfo(country)

		folder = "data/" + country["slug"]

		# download cities
		for city in cities:
			try:
				print "- " + city["name"]
			except:
				pass

			cityInfo, bam = downloadCity(city)

			if not os.path.isdir(folder + "/city"):
				os.mkdir(folder + "/city")

			with open(folder + "/city/" + city["slug"] + ".html", "w") as f:
				f.write(str(cityInfo))

		if not os.path.isdir(folder + "/"):
			os.mkdir(folder + "/")

		with open(folder + "/profile.html", "w") as f:
			f.write(str(profile))

		with open(folder + "/formalities.html", "w") as f:
			f.write(str(formalities))

		with open(folder + "/general.html", "w") as f:
			f.write(str(generalinfo))

import requests, json, os, sys, hashlib, time, base64
from datetime import datetime, date, timedelta
from bs4 import BeautifulSoup
from slugify import slugify
import couchdb

# open connection to couchdb
couch = couchdb.Server(os.getenv("COUCHDB_URI", "https://admin:wZu9TP5pFNS2sTM4@db.landho-app.com"))

# DOWNLOAD IMAGE
def downloadImage(url):

	if not url.startswith("http://www.noonsite.com"):

		if url.startswith("/"):
			url = "http://www.noonsite.com" + url
		else:
			url = "http://www.noonsite.com/" + url

	r = requests.get(url)
	if r.status_code == 200:
		return r.headers["Content-Type"], base64.b64encode(r.content)
	else:
		return None, None

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

				flag = None

				if getFlag == True:
					countryHtml = requests.get(a.get("href")).text
					countrySoup = BeautifulSoup(countryHtml, "html.parser")

					for img in countrySoup.find_all("img"):
						if "flags" in img.get("src") and ".gif/image" in img.get("src"):
							flag = img.get("src").replace("http://www.noonsite.com", "")

				print a.get_text()
				country = {
					"continent": currentArea,
					"name": a.get_text(),
					"url": a.get("href"),
					"_id": slugify(a.get_text()),
					"flag": flag
				}

				country_checksum = checksum(country)
				country_document = couch["countries"].get(slugify(a.get_text()))

				# document needs an update, save to couchdb
				if not country_document or country_document["checksum"] != country_checksum:
					country["checksum"] = country_checksum
					country["updated"] = timestamp()

					if country_document != None:
						country["_rev"] = country_document["_rev"]

					# save document
					_id, _rev = couch["countries"].save(country)

					country["_rev"] = _rev
				else:
					country = country_document

				# check if flag has already been attached
				flag_att = couch["countries"].get_attachment(country, flag)
				if not flag_att:
					# download image
					content_type, img_data = downloadImage(flag)
					if content_type and img_data:
						couch["countries"].put_attachment(country, img_data, flag, content_type)


# CHECKSUM
def checksum(obj):
	return hashlib.md5(json.dumps(obj, sort_keys=True)).hexdigest()

# TIMESTAMP
def timestamp():
	return time.mktime(datetime.utcnow().timetuple())

# download countries
print "BUILD COUNTRIES.JSON"
downloadCountries(True)

sys.exit(0)

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

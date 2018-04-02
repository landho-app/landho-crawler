import requests, json, os, sys, hashlib, time
from datetime import datetime, date, timedelta
from bs4 import BeautifulSoup
from slugify import slugify
import couchdb

# open connection to couchdb
couch = couchdb.Server("https://admin:wZu9TP5pFNS2sTM4@db.landho-app.com")

# DOWNLOAD IMAGE
def downloadImage(url):

	if not url.startswith("http://www.noonsite.com"):

		if url.startswith("/"):
			url = "http://www.noonsite.com" + url
		else:
			url = "http://www.noonsite.com/" + url

	r = requests.get(url)
	if r.status_code == 200:
		return r.headers["Content-Type"], r.content
	else:
		return None, None

# GET SECTIONS
def getSections(country, html):

	soup = BeautifulSoup(html, "html.parser")
	sections = soup.find(id="noonsite-sections")

	sectionStr = unicode(sections)
	images = []

	# download images
	for img in sections.find_all("img"):

		if img != None and img.get("src") != None:
			fileName = prepareImgName(img.get("src").replace("http://www.noonsite.com", ""))

			content_type, img_data = downloadImage(img.get("src"))
			images.append({
				"name": fileName,
				"content_type": content_type,
				"img_data": img_data
			})

			sectionStr = sectionStr.replace("src=\"" + img.get("src"), "src=\"" + fileName)

	cities = []
	for a in sections.find_all("a"):
		if a != None and a.get("href") != None and a.get("href").startswith(country["url"]) and len(a.get("href")) < 90:
			cities.append({
				"name": a.get_text().replace("*", "").strip(),
				"url": a.get("href"),
				"slug": slugify(a.get_text().replace("*", "").strip())
			})

	return sectionStr, cities, images

# PREPARE IMG NAME
def prepareImgName(input):
	if not input:
		return None

	return input.replace("/", "-").strip("-")

# DOWNDLOAD SECTION
def downloadSection(country, section, db_name):
	p = requests.get(country["url"] + "?rc=" + section)
	countryHtml = p.text

	# download information
	sectionStr, cities, images = getSections(country, countryHtml)

	# store in couchdb
	section = {
		"_id": country["_id"],
		"section": sectionStr
	}

	section_checksum = checksum(section)
	section_document = couch[db_name].get(country["_id"])

	if not section_document or section_document["checksum"] != section_checksum:
		section["checksum"] = section_checksum
		section["updated"] = timestamp()

		if section_document != None:
			section["_rev"] = section_document["_rev"]

		# save section
		_id, _rev = couch[db_name].save(section)

		section["_rev"] = _rev
	else:
		section = section_document

	# upload images
	for image in images:
		# check if flag has already been attached
		img_att = couch[db_name].get_attachment(section, image["name"])
		if not img_att:
			if image["content_type"] and image["img_data"]:
				couch[db_name].put_attachment(section, image["img_data"], image["name"], image["content_type"])

	return sectionStr, cities

# DOWNLOAD PROFILE
def downloadProfile(country):
	 return downloadSection(country, "CountryProfile", "profiles")

# DOWNLOAD FORMATLITIES
def downloadFormalities(country):
	return downloadSection(country, "Formalities", "formalities")

# DOWNLOAD GENERALINFO
def downloadGeneralInfo(country):
	return downloadSection(country, "GeneralInfo", "generalinfos")

# DOWNLOAD CITY
def downloadCity(country, city):
	c = requests.get(city["url"])
	sectionStr, cities, images = getSections(city, c.text)

	# store in couchdb
	section = {
		"_id": country["_id"] + "-" + slugify(city["name"]),
		"name": city["name"],
		"country": country["_id"],
		"city": sectionStr
	}

	db_name = "cities"
	section_checksum = checksum(section)
	section_document = couch[db_name].get(section["_id"])

	if not section_document or section_document["checksum"] != section_checksum:
		section["checksum"] = section_checksum
		section["updated"] = timestamp()

		if section_document != None:
			section["_rev"] = section_document["_rev"]

		# save section
		_id, _rev = couch[db_name].save(section)

		section["_rev"] = _rev
	else:
		section = section_document

	# upload images
	for image in images:
		# check if flag has already been attached
		img_att = couch["cities"].get_attachment(section, image["name"])
		if not img_att:
			if image["content_type"] and image["img_data"]:
				couch["cities"].put_attachment(section, image["img_data"], image["name"], image["content_type"])

# DOWNLOAD COUNTRIES
def downloadCountries(getFlag=False):

	countries = []

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
					"flag": prepareImgName(flag)
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
						couch["countries"].put_attachment(country, img_data, prepareImgName(flag), content_type)

				countries.append(country)
	return countries

# CHECKSUM
def checksum(obj):
	return hashlib.md5(json.dumps(obj, sort_keys=True)).hexdigest()

# TIMESTAMP
def timestamp():
	return float(datetime.utcnow().strftime("%s"))

# download countries
print "BUILD COUNTRIES.JSON"
countries = downloadCountries(True)

print "\n\n"
print "FETCH INDIVIDUAL CONTRIES"

for country in countries:

	# open connection to couchdb
	couch = couchdb.Server(os.getenv("COUCHDB_URI"))

	print country["name"]
	profile, cities = downloadProfile(country)
	formalities, bla = downloadFormalities(country)
	generalinfo, blub = downloadGeneralInfo(country)

	# download cities
	for city in cities:
		try:
			print "- " + city["name"]
		except:
			pass

		downloadCity(country, city)

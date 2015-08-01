#!/usr/bin/env python
import os
import sys
import urllib2
import xlrd
import json
import httplib	
import urllib

# Parse credentials
applicationId = "T73AsYtH6A26QzdJMgLGder3fr3aOOmMi4ZbRn0L"
apiKey = "Z7UDl8Tzr7iNpU0ybPdfAmHhklrHc0LP0SuU5ncc"

# HSA dataset
download_url = 'http://data.gov.sg/Agency_Data/HSA/0411050000000013551E.xls'

hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

req = urllib2.Request(download_url, headers=hdr)

# Retrieve webpage as string, terminate program if fail to retrieve data
try:
    # Download file and save into system
    print "Downloading xls from data.gov"
    response = urllib2.urlopen(req)
    print "Downloaded file"
except:
    print "Unable to retrieve file from URL : " + download_url
    sys.exit()

book = xlrd.open_workbook(file_contents=response.read())
data_sheet = book.sheet_by_name('Data')
# read header values into the list    
keys = [str(data_sheet.cell(0, col_index).value).lower().replace(' ', '').replace('.', '') for col_index in xrange(data_sheet.ncols)]

# temp dict to store all dataset
dict_list = []

# iterate xls file to store each record as an object into the dict, skipping the first row which is the column headers
for row_index in xrange(1, data_sheet.nrows):
    d = {keys[col_index]: data_sheet.cell(row_index, col_index).value 
         for col_index in xrange(data_sheet.ncols)}
    dict_list.append(d)

print "Total records found", len(dict_list)
put = 0
post = 0
#print dict_list[0]
count = len(dict_list)

connection = httplib.HTTPSConnection('api.parse.com', 443)

for entry in dict_list:
	query_result = None
	result = None

	# Query Parse database to check if record exist
	licenceno = entry['licenceno']
	params = urllib.urlencode({"where":json.dumps({
		"licenceno": licenceno
	})})
	connection.connect()
	connection.request('GET', '/1/classes/drugs?%s' % params, '', {
		"X-Parse-Application-Id": applicationId,
		"X-Parse-REST-API-Key": apiKey
	})
	query_result = json.loads(connection.getresponse().read())

	# If record exists, update attributes
	if len(query_result['results']) == 1:
		objectId = str(query_result['results'][0]['objectId'])
		connection.request('PUT', '/1/classes/drugs/' + objectId, json.dumps(entry), {
			"X-Parse-Application-Id": applicationId,
			"X-Parse-REST-API-Key": apiKey,
			"Content-Type": "application/json"
		})
		result = json.loads(connection.getresponse().read())
		put += 1
		print "old", result
	elif len(query_result['results']) == 0:
		connection.request('POST', '/1/classes/drugs', json.dumps(entry), {
			"X-Parse-Application-Id": applicationId,
			"X-Parse-REST-API-Key": apiKey,
			"Content-Type": "application/json"
		})
		results = json.loads(connection.getresponse().read())
		post += 1
		print "new", results

	count -= 1
	print "Records left to process", count

print "put", put
print "post", post
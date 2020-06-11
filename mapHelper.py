###############################################################################
# Helper script to make maintaining the database easier
# 	Creates .zip files for any .info / .content files in ./CustomContent
#	Calculates .info hash
#	Calculates .zip  hash
#	Gets .zip file size
#	Applies current data to the "UPDATE DATE" field
#	
#	Downloads current database and updates fields based on above. 
#	If that map doesn't exist it creates a new entry
#
#	Allows me automate most of the data entry so I can just copy/paste and
#	avoid screwing up the data entry
###############################################################################


import gdown
from zipfile import ZipFile 
import os 
import glob
import csv
import hashlib
import datetime 
import math

filenameMapList = 'mapList.csv'
newfilenameMapList = 'newMapList.csv'
mapListGoogleURL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQ3uNvIexndfAxla3VACEpz6wCSLs8v8w1VzdmUPEw7SxuInqxbOEje_fUoxR5vmGnBZ9BRLloMJ0Xc/pub?gid=0&single=true&output=csv'

###############################################################################
# Compute an MD5 Sum for a file
###############################################################################
def getHash(filename):
   # make a hash object
   h = hashlib.md5()

   # open file for reading in binary mode
   with open(filename,'rb') as file:

	   # loop till the end of the file
	   chunk = 0
	   while chunk != b'':
		   # read only 1024 bytes at a time
		   chunk = file.read(1024)
		   h.update(chunk)

   # return the hex representation of digest
   return h.hexdigest()

###############################################################################
# Get the index for the map data based on ID
###############################################################################   
def getIndex(mapList, mapID):
	p=-1
	
	l=len(mapList["ID"])
	for i in range(0,l):
		if mapList["ID"][i] == mapID:
			p=i
			break
	return p
	
###############################################################################
# Obtain the custom map list from Google Doc and install missing maps
###############################################################################
if __name__ == "__main__":
	# Download the custom maps list from Google Drive
	print("***INFO*** Obtaining the complete custom maps list from server.")	
	try:
		gdown.download(mapListGoogleURL, filenameMapList, quiet=True)
	except AssertionError as error:
		print("\n***ERROR*** Unable to obtain the list of custom maps... Please try again later.\n")	
		exit()

	print("***INFO*** List downloaded sucessfully...\n\n")
	# Read the maps list from the file into a Dictionary
	f = open(filenameMapList)
	reader = csv.DictReader(f)
	mapList = {}
	for row in reader:
		for column, value in row.items():
			mapList.setdefault(column.upper(), []).append(value)
	f.close()
		
	
	mapFiles=glob.glob("CustomContent/*.info")
	
	for fname in mapFiles:
		p = fname.rfind(".")
		ID=fname[:p]
		slash=ID.rfind("/")
		ID=ID[slash+1:]
		
		zipFN= fname[:p] + ".zip"
		contentFN= fname[:p] + ".content"
		
		infoHash=getHash(fname)

		print("Zipping: %s" % zipFN)
		# writing files to a zipfile 
		with ZipFile(zipFN,'w') as zip: 
			zip.write(fname)
			zip.write(contentFN)
			zip.close()	
	    	
		i=getIndex(mapList, ID)
		
		zipHash=getHash(zipFN)
		zipSize=int(math.ceil(os.path.getsize(zipFN)/(1024*1024)))

		today=datetime.date.today().strftime("%m/%d/%Y")
		if i == -1:
			print("new row", ID)
			newRow=["", "", ID, infoHash,today, "", "", zipSize, "", zipHash, ""] 
			mapList.update(newRow)
		else:
			mapList["INFO HASH"][i]=infoHash
			mapList["UPDATE DATE"][i]=today
			mapList["FILE SIZE"][i]=zipSize
			mapList["ZIP HASH"][i]=zipHash
	
	
	l=len(mapList["MAP NAME"])
	
	f = open(newfilenameMapList, "w")	
	headers="MAP NAME,AUTHOR,ID,INFO HASH,RELEASE DATE,UPDATE DATE,RATING,FILE SIZE,DOWNLOAD URL,ZIP HASH,MISC FIELDS\n"
	f.write(headers)
	for i in range(0,l):
		s="%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (mapList["MAP NAME"][i], mapList["AUTHOR"][i], mapList["ID"][i], mapList["INFO HASH"][i], \
			mapList["RELEASE DATE"][i], mapList["UPDATE DATE"][i], mapList["RATING"][i], mapList["FILE SIZE"][i], mapList["DOWNLOAD URL"][i], \
			mapList["ZIP HASH"][i], mapList["MISC FIELDS"][i])
		f.write(s)
		
	f.close()
	
	
		

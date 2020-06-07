import os
import gdown
import csv
import hashlib
import argparse

from pathlib import Path


                    


#desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
# Prints: C:\Users\sdkca\Desktop
#print("The Desktop path is: " + desktop)
#print(os.environ)

appVersion = "1.0"
filenameMapList = 'mapList.csv'
mapListGoogleURL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQ3uNvIexndfAxla3VACEpz6wCSLs8v8w1VzdmUPEw7SxuInqxbOEje_fUoxR5vmGnBZ9BRLloMJ0Xc/pub?gid=0&single=true&output=csv'

onwardPath = "appdata/"
mapFolder = "CustomContent/"


parser = argparse.ArgumentParser(description='Onward Custom Map Downloader version %s' %(appVersion))
# Optional argument
parser.add_argument('-rating', type=int,
                    help='Rating Filter: Only install maps that have this star rating or better')
                    
# TODO
# Make sure Onward directory exists
# Make a CustomContent folder if it doesn't exist



def needMap(mapID, mapHash):
	infoFile=onwardPath + mapFolder + mapID + ".info"
	contentFile=onwardPath + mapFolder + mapID + ".content"  
	
	# If .content file doesn't exist you need to download the map
	my_file = Path(contentFile)
	if my_file.is_file() is False:
    		return True
	
	# if .info file doesn't exist the hash check will fail so you still need to download the map
	my_file = Path(infoFile)
	if my_file.is_file() is False:
    		return True
    		    		
    	# check hash of .info file to verify if map the user already has is current\
	h=getHash(infoFile)
	if h != mapHash:
		return True	

	# All test passed so we don't need this map file    	
	return False
	
def downloadMap(mapID, mapDownloadURL, zipHash):
	downloadName=onwardPath + mapID + ".zip"
		
	try:
		gdown.cached_download(mapDownloadURL, downloadName, md5=zipHash, postprocess=gdown.extractall)
	except AssertionError as error:
		return False
		
	# Delete the zip file after downloading/extracting.
	#os.remove(downloadName)
	return True

def getHash(filename):
   """"This function returns the SHA-1 hash
   of the file passed into it"""

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
   


if __name__ == "__main__":
	args = parser.parse_args()
	
	# Set the rating filter. If nothing is specififed install all maps
	if args.rating is not None and args.rating > 0:
		ratingFilter=args.rating
	else:
		ratingFilter=0

		
	# Download the custom maps list from Google Drive
	print("Obtaining the custom maps list...")	
	try:
		gdown.download(mapListGoogleURL, filenameMapList, quiet=False)
	except AssertionError as error:
		print("ERROR: Unable to obtain the list of custom maps... Please try again later.")	
		exit()



	# Read the maps list from the file as a Dictionary
	reader = csv.DictReader(open(filenameMapList))

	maps = {}
	for row in reader:
		for column, value in row.items():
			maps.setdefault(column.upper(), []).append(value)
		
	print (maps.keys())
	# Make sure the map list we download contains valid data	
	validKeys = {"MAP NAME":1, "ID":2, "INFO HASH":3, "RELEASE DATE":4, "UPDATE DATE":5, "RATING":6, "DOWNLOAD URL":7, "ZIP HASH":8}	
	if maps.keys() != validKeys.keys(): 
		print("ERROR: Unable to obtain the list of custom maps... Please try again later.")	
		print("here")
		
		exit()
	
	l=len(maps["MAP NAME"])
	if l is None or l < 1:	
		print("ERROR: Map list downloaded but is empty... Try again later.")	
		exit()			

	totalMapsInstalled=0
	totalMapsSkipped=0
	totalMapsFailed=0
	
	# Traverse the list of maps		
	for i in range(0,l):
		# If no rating is defined set it to 0 so the filter works properly.
		if maps["RATING"][i].isnumeric() is False:
			maps["RATING"][i]="0";
		
		# Don't download maps that have a lower star rating that the user specified
		if int(maps["RATING"][i]) >= ratingFilter:
			if needMap(maps["ID"][i], maps["INFO HASH"][i]):
				print("\n****Downloading map \"%s\"\t\tID:%s\t\tRating:%s" %(maps["MAP NAME"][i], maps["ID"][i],maps["RATING"][i]))
				if downloadMap(maps["ID"][i], maps["DOWNLOAD URL"][i], maps["ZIP HASH"][i]) is True:
					totalMapsInstalled = totalMapsInstalled + 1
				else:
					totalMapsFailed = totalMapsFailed + 1
					print("\r\r***ERROR: Map \"%s\" ID:%s did not have the expected hash value... This map will not be installed" %(maps["MAP NAME"], maps["ID"]))	
			else:
				totalMapsSkipped = totalMapsSkipped + 1
				print("Skipping map \"%s\" ID: %s ---- already installed." %(maps["MAP NAME"][i], maps["ID"][i]))
		else:
			totalMapsSkipped = totalMapsSkipped + 1
			print("Skipping map \"%s\" ID: %s ---- Map Rating %s below threshold %s" %(maps["MAP NAME"][i], maps["ID"][i],maps["RATING"][i], ratingFilter))	
			
			
	# Delete the custom map metadata
	os.remove(filenameMapList)	

	print("\n\nMaps Installed: %s\tMaps Skipped: %s\tTotal Maps Failed To Install:%s\tTotal Maps:%s" % (totalMapsInstalled, totalMapsSkipped, totalMapsFailed, l))




	


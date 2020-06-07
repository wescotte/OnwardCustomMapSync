import os
import gdown
import csv
import hashlib
import argparse

from pathlib import Path


                    
###############################################################################
# Global Variables
###############################################################################


appVersion = "1.0"
filenameMapList = 'mapList.csv'
mapListGoogleURL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQ3uNvIexndfAxla3VACEpz6wCSLs8v8w1VzdmUPEw7SxuInqxbOEje_fUoxR5vmGnBZ9BRLloMJ0Xc/pub?gid=0&single=true&output=csv'

onwardPath = "appdata/"
mapFolder = "CustomContent/"

# Setup Arguments
parser = argparse.ArgumentParser(description='Onward Custom Map Downloader version %s' %(appVersion))
parser.add_argument('-rating', type=int,
                    help='Rating Filter: Only install maps that have this star rating or better')
                    
# TODO
# Make sure Onward directory exists
#desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
# Prints: C:\Users\sdkca\Desktop
#print("The Desktop path is: " + desktop)
#print(os.environ)



###############################################################################
# Verify if we already have the map installed
# -Check if a mapID.info & mapID.content already exist in our custom map folder
# -Check if mapID.info MD5 hash matches current version
###############################################################################
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
	

###############################################################################
# Download a mapID.zip file and verify the MD5 sum matches
###############################################################################	
def downloadMap(mapID, mapDownloadURL, zipHash):
	downloadName=onwardPath + mapID + ".zip"
		
	try:
		gdown.cached_download(mapDownloadURL, downloadName, md5=zipHash, postprocess=gdown.extractall)
	except AssertionError as error:
		return False
		
	# Delete the zip file after downloading/extracting.
	#os.remove(downloadName)
	return True


###############################################################################
# Compute an MD5 Sum for a file
###############################################################################
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
   


###############################################################################
# Obtain the custom map list from Google Doc and install missing maps
###############################################################################
if __name__ == "__main__":
	args = parser.parse_args()
	
	# Set the rating filter. If nothing is specififed install all maps
	if args.rating is not None and args.rating > 0:
		ratingFilter=args.rating
	else:
		ratingFilter=0

		
	# Download the custom maps list from Google Drive
	print("***INFO*** Obtaining the complete custom maps list from server.")	
	try:
		gdown.download(mapListGoogleURL, filenameMapList, quiet=True)
	except AssertionError as error:
		print("\n***ERROR*** Unable to obtain the list of custom maps... Please try again later.\n")	
		exit()

	print("***INFO*** List downloaded sucessfully...")

	# Read the maps list from the file as a Dictionary
	reader = csv.DictReader(open(filenameMapList))

	maps = {}
	for row in reader:
		for column, value in row.items():
			maps.setdefault(column.upper(), []).append(value)
		
	# Make sure the map list we download contains valid data	
	validKeys = {"MAP NAME":1, "ID":2, "INFO HASH":3, "RELEASE DATE":4, "UPDATE DATE":5, "RATING":6, "DOWNLOAD URL":7, "ZIP HASH":8}	
	if maps.keys() != validKeys.keys(): 
		print("\n***ERROR*** Unable to obtain the list of custom maps... Please try again later.\n")	
		exit()
	
	l=len(maps["MAP NAME"])
	if l is None or l < 1:	
		print("\n***ERROR*** Map list downloaded but is empty... Try again later.\n")	
		exit()			

	totalMapsInstalled=0
	totalMapsAlreadyInstalled=0	
	totalMapsSkippedRating=0
	totalMapsFailed=0
	
	# Traverse the list of maps		
	for i in range(0,l):
		# If no rating is defined set it to 0 so the filter works properly.
		if maps["RATING"][i].isnumeric() is False:
			maps["RATING"][i]="0";
		
		# Don't download maps that have a lower star rating that the user specified
		if int(maps["RATING"][i]) >= ratingFilter:
			if needMap(maps["ID"][i], maps["INFO HASH"][i]):
				print("***DOWNLOADING MAP*** \"%s\"\t\tID:%s\t\tRating:%s" %(maps["MAP NAME"][i], maps["ID"][i],maps["RATING"][i]))
				if downloadMap(maps["ID"][i], maps["DOWNLOAD URL"][i], maps["ZIP HASH"][i]) is True:
					totalMapsInstalled = totalMapsInstalled + 1
					print("***SUCCESSFULLY INSTALLED*** \"%s\"\t\tID:%s\n" %(maps["MAP NAME"][i],maps["ID"][i]))
				else:
					totalMapsFailed = totalMapsFailed + 1
					print("\n***ERROR*** Map \"%s\" ID:%s did not have the expected hash value... This map will not be installed" %(maps["MAP NAME"][i], maps["ID"][i]))	
			else:
				totalMapsAlreadyInstalled = totalMapsAlreadyInstalled + 1
				print("***SKIPPING MAP*** \"%s\" ID: %s ---- already installed." %(maps["MAP NAME"][i], maps["ID"][i]))
		else:
			totalMapsSkippedRating = totalMapsSkippedRating + 1
			print("***SKIPPING MAP*** \"%s\" ID: %s ---- Map is rated below threshold" %(maps["MAP NAME"][i], maps["ID"][i]))	
			
			
	# Delete the custom map metadata
	os.remove(filenameMapList)	

	print("\n\n***INFO*** Maps Installed: %s\t\tAlready Installed: %s\t\tSkipped-Low Rating: %s\t\tInstall Failed: %s\t\tTotal Maps: %s" % (totalMapsInstalled, totalMapsAlreadyInstalled,totalMapsSkippedRating, totalMapsFailed, l))




	


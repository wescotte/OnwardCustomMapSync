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
		print("ERROR: Map ID: %s did not have the expected hash value... This map will not be installed" %(mapID))
		
	# Delete the zip file after downloading/extracting.
	os.remove(downloadName)


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
		gdown.download(mapListGoogleURL, filenameMapList, quiet=True)
	except AssertionError as error:
		print("ERROR: Unable to obtain the list of custom maps... Please try again later.")	
		exit()



	# Read the maps list from the file as a Dictionary
	reader = csv.DictReader(open(filenameMapList))

	maps = {}
	for row in reader:
		for column, value in row.items():
			maps.setdefault(column, []).append(value)
		
	print (maps.keys())
	# Make sure the map list we download contains valid data	
	validKeys = {"Map Name":1, "ID":2, "Info Hash":3, "Release Date":4, "Update Date":5, "Rating":6, "Download URL":7, "Zip Hash":8}	
	if maps.keys() != validKeys.keys(): 
		print("ERROR: Unable to obtain the list of custom maps... Please try again later.")	
		exit()
	
	l=len(maps["Map Name"])
	if l is None or l < 1:	
		print("ERROR: Map list downloaded but is empty... Try again later.")	
		exit()			

	# Traverse the list of maps		
	for i in range(0,l):
		# If no rating is defined set it to 0 so the filter works properly.
		if maps["Rating"][i].isnumeric() is False:
			maps["Rating"][i]="0";
		
		# Don't download maps that have a lower star rating that the user specified
		if int(maps["Rating"][i]) >= ratingFilter:
			if needMap(maps["ID"][i], maps["Info Hash"][i]):
				print("\n****Downloading map \"%s\" ID:%s Rating:%s" %(maps["Map Name"][i], maps["ID"][i],maps["Rating"][i]))
				downloadMap(maps["ID"][i], maps["Download URL"][i], maps["Zip Hash"][i])
			else:
				print("Skipping map \"%s\" ID: %s as it is already installed." %(maps["Map Name"][i], maps["ID"][i]))
		else:
			print("Skipping map \"%s\" ID: %s as it has a rating of %s which is below your threshold of %s" %(maps["Map Name"][i], maps["ID"][i],maps["Rating"][i], ratingFilter))	
			
			
	# Delete the custom map metadata
	os.remove(filenameMapList)	






	


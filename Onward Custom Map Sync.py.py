import os
import gdown
import csv
import hashlib

from pathlib import Path




#desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
# Prints: C:\Users\sdkca\Desktop
#print("The Desktop path is: " + desktop)
#print(os.environ)

filenameMapList = 'mapList.csv'
mapListGoogleURL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQ3uNvIexndfAxla3VACEpz6wCSLs8v8w1VzdmUPEw7SxuInqxbOEje_fUoxR5vmGnBZ9BRLloMJ0Xc/pub?gid=0&single=true&output=csv'

pathToMaps = "CustomContent2/"

# TODO
# Make sure Onward directory exists
# Make a CustomContent folder if it doesn't exist



def needMap(mapID, mapHash):
	infoFile=pathToMaps + mapID + ".info"
	contentFile=pathToMaps + mapID + ".content"  
	
	# If .content file doesn't exist you need to download the map
	my_file = Path(contentFile)
	if my_file.is_file() is False:
    		return True
	else:
		print("Found " + contentFile)
	
	# if .info file doesn't exist the hash check will fail so you still need to download the map
	my_file = Path(infoFile)
	if my_file.is_file() is False:
    		return True
	else:
		print("Found " + infoFile)
    		    		
    	# check hash of .info file to verify if map the user already has is current\
	h=getHash(infoFile)
	print("CHash: " + h + " recordedH: " + mapHash)
	if h != mapHash:
		return True	

	# All test passed so we don't need this map file    	
	return False
	
def downloadMap(mapID, mapDownloadURL, zipHash):
	downloadName=pathToMaps + mapID + ".zip"
	print("Downloading: " + mapDownloadURL + " to: " + downloadName);
	downloadOkay=gdown.cached_download(mapDownloadURL, downloadName, md5=zipHash, postprocess=gdown.extractall)
	
	print("Downloaded: " + downloadOkay)
	# Delete the zip file after downloading/extracting and verifying md5 match
	if downloadOkay == downloadName:
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
   


# Download the custom maps list from Google Drive
#gdown.download(mapListGoogleURL, filenameMapList, quiet=False)


# Read the maps list from the file as a Dictionary
reader = csv.DictReader(open(filenameMapList))

mapList = {}
for row in reader:
    for column, value in row.items():
        mapList.setdefault(column, []).append(value)
        
l=len(mapList["Map Name"])
for i in range(0,l):
#	mapFileName=mapList["ID"][i] & ".info"
#	print(mapList["Map Name"][i])
	if needMap(mapList["ID"][i], mapList["Info Hash"][i]):
		print(mapList["Zip Hash"][i] + " len: " + str(len(mapList["Zip Hash"][i])))
		downloadMap(mapList["ID"][i], mapList["Download URL"][i], mapList["Zip Hash"][i])
	else:
		print("Skipping " + mapList["Map Name"][i] + " ID: " + mapList[ID][i] + " already exists...")






	


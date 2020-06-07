import os
import csv
import hashlib
import argparse
from zipfile import ZipFile
from pathlib import Path

from lxml import etree

# gdown required libs
import requests
import re
import sys
import tqdm
import os.path as osp




                    
###############################################################################
# Global Variables
###############################################################################
appVersion = "0.99"
settingsFile="Onward Custom Map Sync Settings.xml"
XMLSettings = None

filenameMapList = 'Map List.csv'
mapListGoogleURL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQ3uNvIexndfAxla3VACEpz6wCSLs8v8w1VzdmUPEw7SxuInqxbOEje_fUoxR5vmGnBZ9BRLloMJ0Xc/pub?gid=0&single=true&output=csv'

if "APPDATA" not in os.environ:
    print("***ERROR*** APPDATA environmental variable not set. Don't know how to find Onward Custom Maps folder")
    exit()
    
onwardPath = os.environ["APPDATA"] + "\..\LocalLow\Downpour Interactive\Onward\\"
mapFolder = "CustomContent\\"


		
###############################################################################
# Setup Command Line Arguments
###############################################################################
parser = argparse.ArgumentParser(description='Onward Custom Map Downloader version %s' %(appVersion))
parser.add_argument('-rating', type=int,
                    help='Rating Filter: Only install maps that have this star rating or better')
                    



###############################################################################
# Create Default Settings for if the settings file is missing
###############################################################################
def createDefaultSettings():
	global XMLSettings
	
	root = etree.Element('Onward_Custom_Map_Sync_Settings')
	mlURL = etree.SubElement(root, 'Map_List_URL')
	mlFN = etree.SubElement(root, 'Map_List_Filename')
	DelZIPs = etree.SubElement(root, 'Delete_Map_Zips_After_Install')
	DelML = etree.SubElement(root, 'Delete_Map_List_On_Exit')
	exlude = etree.SubElement(root, 'Exclude_Maps_Filters')	
	
	rFilter = etree.SubElement(exlude, 'Ratings_Filter')
	
	mlURL.text = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQ3uNvIexndfAxla3VACEpz6wCSLs8v8w1VzdmUPEw7SxuInqxbOEje_fUoxR5vmGnBZ9BRLloMJ0Xc/pub?gid=0&single=true&output=csv'
	mlFN.text = 'Map List.csv'
	DelZIPs.text = 'True'
	DelML.text = 'True'
	rFilter.text='0'
	
	XMLSettings=root	
	
###############################################################################
# Load Settings
###############################################################################
def loadSettings():
	global XMLSettings
	
	# If no settings file exists create a new one with default values
	if os.path.isfile(settingsFile) == False:
		createDefaultSettings()
		saveSettings()
		
	XMLSettings = etree.parse(settingsFile)
	


###############################################################################
# Save Settings
###############################################################################
def saveSettings():
	global XMLSettings
	
	mydata = etree.tostring(XMLSettings, pretty_print=True)
	f = open(settingsFile, "wb")
	f.write(mydata)
	f.close()


###############################################################################
# Download a file from Google Drive
# Adapted from gdown library
# https://github.com/wkentaro/gdown
###############################################################################				
def downloadGoogleDriveFile(localFileName, url, quiet=True):
	CHUNK_SIZE = 512 * 1024  # 512KB
	url_origin = url
	s = requests.session()
	
	while True:	
		try:
			res = s.get(url, stream=True)
		except requests.exceptions.ProxyError as e:
			print("An error has occurred using proxy:", proxy, file=sys.stderr)
			print(e, file=sys.stderr)
			return False

		# Save cookies
		#with open(cookies_file, "w") as f:
		#	json.dump(sess.cookies.items(), f, indent=2)

		if "Content-Disposition" in res.headers:
			# This is the file
			break

		# Need to redirect with confirmation
		try:
			url = get_url_from_gdrive_confirmation(res.text)
		except RuntimeError as e:
			print("Access denied with the following error:")
			error = "\n".join(textwrap.wrap(str(e)))
			error = indent_func(error, "\t")
			print("\n", error, "\n", file=sys.stderr)
			print(
				"You may still be able to access the file from the browser:",
				file=sys.stderr,
			)
			print("\n\t", url_origin, "\n", file=sys.stderr)
			return False

		if url is None:
			print("Permission denied:", url_origin, file=sys.stderr)
			print(
				"Maybe you need to change permission over "
				"'Anyone with the link'?",
				file=sys.stderr,
			)
			return False
	# End While
	
	if not quiet:
		print("Downloading...", file=sys.stderr)
		print("From:", url_origin, file=sys.stderr)
		print(
			"To:",
			localFileName,
			file=sys.stderr,
		)
	
	f = open(localFileName, "wb")
	try:
		total = res.headers.get("Content-Length")
		if total is not None:
			total = int(total)
		if not quiet:
			pbar = tqdm.tqdm(total=total, unit="B", unit_scale=True)
		#t_start = time.time()
		for chunk in res.iter_content(chunk_size=CHUNK_SIZE):
			f.write(chunk)
			if not quiet:
				pbar.update(len(chunk))
		""" Disabled throttling for now				
			if speed is not None:
				elapsed_time_expected = 1.0 * pbar.n / speed
				elapsed_time = time.time() - t_start
				if elapsed_time < elapsed_time_expected:
				time.sleep(elapsed_time_expected - elapsed_time)
		"""
		if not quiet:
			pbar.close()

	

	except IOError as e:
		print(e, file=sys.stderr)
		f.close()		
		os.remove(localFileName)
		return False
	
	# File downloaded sucessfully	
	f.close()
	return True
	
def get_url_from_gdrive_confirmation(contents):
    url = ""
    for line in contents.splitlines():
        m = re.search(r'href="(\/uc\?export=download[^"]+)', line)
        if m:
            url = "https://docs.google.com" + m.groups()[0]
            url = url.replace("&amp;", "&")
            return url
        m = re.search("confirm=([^;&]+)", line)
        if m:
            confirm = m.groups()[0]
            url = re.sub(
                r"confirm=([^;&]+)", r"confirm={}".format(confirm), url
            )
            return url
        m = re.search('"downloadUrl":"([^"]+)', line)
        if m:
            url = m.groups()[0]
            url = url.replace("\\u003d", "=")
            url = url.replace("\\u0026", "&")
            return url
        m = re.search('<p class="uc-error-subcaption">(.*)</p>', line)
        if m:
            error = m.groups()[0]
            raise RuntimeError(error)
			
			
###############################################################################
# Verify this map doesn't mean any exclude filters
###############################################################################
def filterMap(mapID, mapName, mapAuthor):
	authorFilter = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Exclude_Maps_Filters/Exlude_Map_Author')
	for i in range(0,len(authorFilter)):
		if authorFilter[i].text == mapAuthor:
			print("***SKIPPING MAP*** \"%s\" ID: %s by %s ---- Filtered by Author." %(mapName, mapID, mapAuthor))
			return True
			
	IDFilter = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Exclude_Maps_Filters/Exlude_Map_ID')
	for i in range(0,len(IDFilter)):
		if IDFilter[i].text == mapID:
			print("***SKIPPING MAP*** \"%s\" ID: %s by %s ---- This map is marked not to install." %(mapName, mapID, mapAuthor))
			return True	
	

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
def getMap(mapID, mapDownloadURL, zipHash, quiet=True):
	
	# Download the Google Drive file
	downloadName=onwardPath + mapID + ".zip"
	
	if "DRIVE.GOOGLE.COM" in mapDownloadURL.upper():
		if downloadGoogleDriveFile(downloadName, mapDownloadURL, quiet) == False:
			return False
	elif "KOIZ" in mapDownloadURL.upper():
		Print("***INFO*** Koiz doesn't want his maps hosted here... Please ask him to reconsider")
		return False
	else:
		Print("***ERROR*** Don't know how to download URL: %s" % mapDownloadURL)
		return False
		
	# validate hash
	calculatedZipHash = getHash(downloadName)
	if zipHash != calculatedZipHash:
		print("***ERROR***: Zip file hash incorrect. Expecting %s but got %s" % (zipHash, calculatedZipHash))
		os.remove(downloadName)			
		return False
	
	# Unzip file
	with ZipFile(downloadName, 'r') as zipObj:
		# Extract all the contents of zip file in current directory
		try:
			zipObj.extractall(onwardPath)	
		except:
			zipObj.close()
			os.remove(downloadName)
			print("***ERROR***: Failed to extract %s" % downloadName)
			return False
			
	zipObj.close()	
	
	# Sucessfully downloaded and extracted map so delete zip file
	delMap = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Delete_Map_Zips_After_Install')
	try:
		if delMap[0].text == "True":
			os.remove(downloadName)	
	except:
		pass
		
	return True


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
# Obtain the custom map list from Google Doc and install missing maps
###############################################################################
if __name__ == "__main__":
	loadSettings()
	
    # Make sure the Onward folder exists
	if os.path.isdir(onwardPath) is False:
		print("***ERROR*** Can't find ONWARD folder in '%s'" % onwardPath)
		exit()
        
    
	args = parser.parse_args()
	
	# Set the rating filter. If nothing is specififed use value in XML settings. If that doesn't exist default 0 / All maps
	if args.rating is not None and args.rating > 0:
		ratingFilter=args.rating
	else:
		rf = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Exclude_Maps_Filters/Ratings_Filter')
		try: 
			ratingFilter=int(rf[0].text)
		except:
			ratingFilter=0

	
	# Download the custom maps list from Google Drive
	print("***INFO*** Obtaining the complete custom maps list from server.")	
	try:
		downloadGoogleDriveFile(filenameMapList, mapListGoogleURL, quiet=True)
	except AssertionError as error:
		print("\n***ERROR*** Unable to obtain the list of custom maps... Please try again later.\n")	
		exit()

	print("***INFO*** List downloaded sucessfully...\n\n")


	# Read the maps list from the file into a Dictionary
	f = open(filenameMapList)
	reader = csv.DictReader(f)
	maps = {}
	for row in reader:
		for column, value in row.items():
			maps.setdefault(column.upper(), []).append(value)
	f.close()
		
	# Make sure the map list we download contains valid data	
	validKeys = {"MAP NAME":1, "AUTHOR":2, "ID":3, "INFO HASH":4, "RELEASE DATE":5, "UPDATE DATE":6, "RATING":7, "DOWNLOAD URL":8, "ZIP HASH":9, "MISC FIELDS":10}	
	if maps.keys() != validKeys.keys(): 
		print (maps.keys())
		print("\n***ERROR*** Map List Strucure does not match expected format...\n")	
		exit()
	
	l=len(maps["MAP NAME"])
	if l is None or l < 1:	
		print("\n***ERROR*** Map list downloaded but is empty... Try again later.\n")	
		exit()			
		
		

	totalMapsInstalled=0
	totalMapsAlreadyInstalled=0	
	totalMapsSkippedRating=0
	totalMapsExcluded=0
	totalMapsFailed=0
	
	# Traverse the list of maps		
	for i in range(0,l):
	
		# If no rating is defined set it to 0 so the filter works properly.
		if maps["RATING"][i].isnumeric() is False:
			maps["RATING"][i]="0";
		
		# Don't download maps that have a lower star rating that the user specified
		if int(maps["RATING"][i]) < ratingFilter:
			totalMapsSkippedRating = totalMapsSkippedRating + 1
			print("***SKIPPING MAP*** \"%s\" ID: %s ---- Map is rated below threshold" %(maps["MAP NAME"][i], maps["ID"][i]))	
			continue	

		# Check for custom filters - Specific Map or Specific Author
		if filterMap(maps["ID"][i], maps["MAP NAME"][i], maps["AUTHOR"][i]):
			totalMapsExcluded = totalMapsExcluded + 1
			continue				
			
		# Verify the map isn't already installed
		if needMap(maps["ID"][i], maps["INFO HASH"][i]):
			print("***DOWNLOADING MAP*** \"%s\" by %s\t\tID: %s\t\tMap Star Rating: %s" %(maps["MAP NAME"][i], maps["AUTHOR"][i], maps["ID"][i],maps["RATING"][i]))
			if getMap(maps["ID"][i], maps["DOWNLOAD URL"][i], maps["ZIP HASH"][i], quiet=False) is True:
				totalMapsInstalled = totalMapsInstalled + 1
				print("***SUCCESSFULLY INSTALLED*** \"%s\"\t\tID:%s\n" %(maps["MAP NAME"][i],maps["ID"][i]))
			else:
				totalMapsFailed = totalMapsFailed + 1
				print("\n***ERROR*** Map \"%s\" ID:%s did not have the expected hash value... This map will not be installed" %(maps["MAP NAME"][i], maps["ID"][i]))	
		else:
			totalMapsAlreadyInstalled = totalMapsAlreadyInstalled + 1
			print("***SKIPPING MAP*** \"%s\" ID: %s ---- already installed." %(maps["MAP NAME"][i], maps["ID"][i]))

			
			
	# Delete the custom map metadata
	delMapList = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Delete_Map_List_On_Exit')
	try:
		if delMapList[0].text == "True":	
			os.remove(filenameMapList)
	except:
		pass

	print("\n\n***INFO*** Maps Installed: %s\tAlready Installed: %s\tSkipped-Low Rating: %s\tSkipped-Custom Filter: %s\tInstall Failed: %s\tTotal Maps: %s" % (totalMapsInstalled, totalMapsAlreadyInstalled,totalMapsSkippedRating, totalMapsExcluded, totalMapsFailed, l))
	os.system("pause")



	


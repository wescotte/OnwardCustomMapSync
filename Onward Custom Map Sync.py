import os
import csv
import hashlib
import argparse
import datetime 
from zipfile import ZipFile
from pathlib import Path
import webbrowser

from lxml import etree

# gdown required libs
import requests
import re
import sys
import tqdm
import os.path as osp

# GUI libs
import PySimpleGUI as sg

# TODO --- Probably should have taken the time to learn how to use enums in Python....
#			If I have time or any major feature requests it's probably worth refactoring a ton of stuff to use enums.
# TODO --- windowGlobal and errorMsgBuffer are clunky... It was the easy solution for allowing
#			both GUI and command line in the same app but might want to refactor at some point.

###############################################################################
# Global Variables
###############################################################################
appVersion = 1.00

filenameMapList = "Map List.csv"
logFilename = "Onward Custom Map Sync.log"
settingsFile="Onward Custom Map Sync Settings.xml"

XMLSettings = None
downloadedAnything = False	# If this is true we update the Last Run Date setting in the XML file on exit

mapListGoogleURL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQ3uNvIexndfAxla3VACEpz6wCSLs8v8w1VzdmUPEw7SxuInqxbOEje_fUoxR5vmGnBZ9BRLloMJ0Xc/pub?gid=0&single=true&output=csv'
maps = {}	# Dictionary of map data download from Google Drive Spreadsheet

onwardPath = "\..\LocalLow\Downpour Interactive\Onward\\"
mapFolder = "CustomContent\\"

# Pointer to the GUI window
globalWindow = None
errorMsgBuffer = None
logFileGlobal = None

# Colors
COLOR_FILTERED="#770000"
COLOR_DOWNLOAD="#007700"
COLOR_DEFAULT="#FFFFFF"
COLOR_BACKGROUND="#000000"
COLOR_ERROR_MESSAGE="#770000"
COLOR_ANNOUNCEMENT="#007700"

###############################################################################
# Setup Command Line Arguments
###############################################################################
parser = argparse.ArgumentParser(description='Onward Custom Map Downloader version %s' %(appVersion))
parser.add_argument('-rating', type=int,
					help='Rating Filter: Only install maps that have this star rating or better')
parser.add_argument("-noGUI", help="Disable the GUI and run in console mode", action='store_true')
parser.add_argument("-logResults", help="Write all messages/errors to 'Onward Custom Map Sync.log'", action='store_true')
parser.add_argument("-justUpdate", help="Only download updates for maps already installed", action='store_true')
parser.add_argument("-justNew", help="Install only new maps (RELEASE DATE after the last Last_Date_Run in XML settings file) regardless of rating", action='store_true')			   
parser.add_argument("-scheduleDaily", help="Add an entry to the Windows Task Scheduler to run daily at specified hh:mm in 24-hour clock / miltary time format")
parser.add_argument("-quiet", help="Disable GUI and don't display any output just write to log file.", action="store_true")

args = parser.parse_args()
###############################################################################
# Create Default Settings for if the settings file is missing
###############################################################################
def createDefaultSettings():
	global XMLSettings
	
	root = etree.Element('Onward_Custom_Map_Sync_Settings')
	runDate = etree.SubElement(root, 'Last_Date_Run')
	mlURL = etree.SubElement(root, 'Map_List_URL')
	mlFN = etree.SubElement(root, 'Map_List_Filename')
	DelZIPs = etree.SubElement(root, 'Delete_Map_Zips_After_Install')
	DelML = etree.SubElement(root, 'Delete_Map_List_On_Exit')
	log = etree.SubElement(root, 'Write_To_Logfile')	
	logSizeLimit = etree.SubElement(root, "Log_Size_Limit_inMB")	
	exlude = etree.SubElement(root, 'Exclude_Maps_Filters')	
	rFilter = etree.SubElement(exlude, 'Ratings_Filter')
	
	runDate.text=str(datetime.date.today().strftime("%m/%d/%Y"))
	mlURL.text = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQ3uNvIexndfAxla3VACEpz6wCSLs8v8w1VzdmUPEw7SxuInqxbOEje_fUoxR5vmGnBZ9BRLloMJ0Xc/pub?gid=0&single=true&output=csv'
	mlFN.text = 'Map List.csv'
	DelZIPs.text = 'True'
	DelML.text = 'True'
	log.text = 'True'
	logSizeLimit.text = "50" # Defaults to logging at max 50mb before erasing
	
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
# Load existing XML settings and just update the run date
###############################################################################
def updateLastRunDate():
	# Load from disk instead of updating current settings because they could have
	# applied filters they don't want permanently stored
	loadSettings()
	try:
		runDate = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Last_Date_Run')
		runDate[0].text=datetime.date.today().strftime("%m/%d/%Y")
	except: 
		reportMessage('{:*^15} Unable to update last run date. Your "Onward Custom Map Sync Settings.xml" might be corrupted....'.format("ERROR"))
		reportMessage('{:*^15} You can erase this file and run the program again and it will create a new one with default settings'.format("ERROR"))
	saveSettings()
	
 
###############################################################################
# Add an entry for this program to run automatically via 
# the Windows Task Scheduler
###############################################################################
# https://stackoverflow.com/questions/26160900/is-there-a-way-to-add-a-task-to-the-windows-task-scheduler-via-python-3
def createTask(h,m):
	import datetime
	import win32com.client

	taskName='Onward Custom Map Sync'
	
	scheduler = win32com.client.Dispatch('Schedule.Service')
	scheduler.Connect()
	root_folder = scheduler.GetFolder('\\')
	task_def = scheduler.NewTask(0)

	arguments="-noGUI"
	global args
	if args.justNew is True:
		arguments=arguments+" -justNew"
	if args.justUpdate is True:
		arguments=arguments+" -justUpdate"		

	# Create trigger
	today = datetime.datetime.today()
	time = datetime.time(int(h), int(m) )
	start_time = datetime.datetime.combine(today, time)	
	TASK_TRIGGER_TIME = 2 # Run Daily
	trigger = task_def.Triggers.Create(TASK_TRIGGER_TIME)
	trigger.StartBoundary = start_time.isoformat()

	# Create action
	TASK_ACTION_EXEC = 0
	action = task_def.Actions.Create(TASK_ACTION_EXEC)
	action.ID = 'DO NOTHING'
	action.Path = sys.argv[0]
	action.WorkingDirectory=os.path.dirname(os.path.realpath(__file__))
	action.Arguments = arguments

	
	# Set parameters
	task_def.RegistrationInfo.Description = 'Automatically download and update custom maps for the game Onward by Downpour Interactive'
	task_def.Settings.Enabled = True
	task_def.Settings.StopIfGoingOnBatteries = False
		
	# Register task
	# If task already exists, it will be updated
	TASK_CREATE_OR_UPDATE = 6
	TASK_LOGON_NONE = 0
	root_folder.RegisterTaskDefinition(
		taskName,  # Task name
		task_def,
		TASK_CREATE_OR_UPDATE,
		'',  # No user
		'',  # No password
		TASK_LOGON_NONE)

	#Delete the scheduled task
	#root_folder.DeleteTask(taskName, 0)
	return
		

###############################################################################
# Inform the user of a message
# -noGUI means stdout
# -quiet means log to Ownard Custom Map Sync.log
# Otherwise display in the status log 
###############################################################################	
def reportMessage(message, logToFile=True):

	global globalWindow
	global errorMsgBuffer
	global args
	global logFileGlobal
	
	# Output to log file
	if logFileGlobal is not None and logToFile is True:
		logFileGlobal.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + " " + message + "\n")
		
	if args.noGUI is False and args.quiet is False:
		color=COLOR_DEFAULT
		if message.find("ERROR") != -1:
			color=COLOR_ERROR_MESSAGE
		elif  message.find("ANNOUNCEMENT") != -1:
			color=COLOR_ANNOUNCEMENT

		# If no GUI window exists buffer the errors so when it exists we can output all messages
		#	This occurs if there are errors before the GUI is created/finalized OR
		#		when we transition between main GUI and progress bar window
		if globalWindow is None:
			if errorMsgBuffer is None:
				errorMsgBuffer = []
			errorMsgBuffer.append(message)
		else:	
			try: # Could also be in a state where the GUI exists but the INSTALL_LOG portion itself doesn't for some reason...
				log=globalWindow["INSTALL_LOG"]
				if errorMsgBuffer is not None:
					color=COLOR_DEFAULT
					for m in errorMsgBuffer:
						if m.find("ERROR") != -1:
							color=COLOR_ERROR_MESSAGE
						elif m.find("ANNOUNCEMENT") != -1:
									color=COLOR_ANNOUNCEMENT
						log.update(m + "\n", text_color_for_value=color, append=True)
					errorMsgBuffer = None
				
				log.update(message + "\n", text_color_for_value=color, append=True, autoscroll=True)
			except:
				if errorMsgBuffer is None:
					errorMsgBuffer = []
				errorMsgBuffer.append(message)
				
	elif args.quiet is False:
		print(message)
	
###############################################################################
# Download a file from Google Drive
# Adapted from gdown library
# https://github.com/wkentaro/gdown
###############################################################################				
def downloadGoogleDriveFile(localFileName, url, fileSize, quiet=True, progressBarsGUI=None):
	CHUNK_SIZE = 512 * 1024	 # 512KB
	url_origin = url
	s = requests.session()
	
	while True:	
		try:
			res = s.get(url, stream=True)
		except requests.exceptions.ProxyError as e:
			reportMessage("An error has occurred using proxy:" + proxy)
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
			reportMessage("Access denied with the following error:")
			error = "\n".join(textwrap.wrap(str(e)))
			error = indent_func(error, "\t")
			reportMessage("\n"+error+"\n")
			reportMessage("You may still be able to access the file from the browser:")
			reportMessage("\n\t" + url_origin + "\n")
			return False

		if url is None:
			reportMessage("Permission denied:" +  url_origin)
			reportMessage("Maybe you need to change permission over to 'Anyone with the link'")
			return False
	# End While
	
	if not quiet:
		reportMessage("Downloading...", False)
		reportMessage("From:" + url_origin, False)
		reportMessage("To:" + localFileName, False)
	
	f = open(localFileName, "wb")
	try:
		total = res.headers.get("Content-Length")
		if total is not None:
			total = int(total)
		
		try:
			totalNumberOfBytes = int(fileSize) * 1024**2 # Convert MB to bytes for status bar
		except:
			totalNumberOfBytes=0
		if not quiet:
			#Google Drive doesn't seem to properly report the file size during download so we just store it for each zip file
			#pbar = tqdm.tqdm(total=total, unit="B", unit_scale=True)
			pbar = tqdm.tqdm(total=totalNumberOfBytes, unit="B", unit_scale=True)
		
		#t_start = time.time()
		bytesWritten=0
					
		for chunk in res.iter_content(chunk_size=CHUNK_SIZE):
			bytesWritten=bytesWritten+len(chunk)
			f.write(chunk)
			if not quiet:				
				pbar.update(len(chunk))
				
			# Handle GUI Progress Bars				
			if progressBarsGUI is not None:
				progress_bar = progressBarsGUI['MAP_PROGRESS']
				progress_bar.update_bar(bytesWritten, totalNumberOfBytes)
				
				# check to see if the cancel button was clicked and exit loop if clicked
				event, values = progressBarsGUI.read(timeout=0)
				if event == 'Cancel' or sg.WIN_CLOSED or event == None:
					# Trigger a user abort
					return None					

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
		reportMessage(e)
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
# Returnss 
#	"" if map isn't filterd otherwise returns the type of filter detected
#	as a string
###############################################################################
def filterMap(needStatus, mapID, mapName, mapAuthor, mapRating, mapReleaseDate):
	filterMsg = ""

	# mapRating going to be a string so convert it to an integer
	try:
		rating=int(mapRating)
	except:
		rating=0
		
	if rating == -1:
		filterMsg="UNAVAILBLE FOR D/L AT AUTHROR'S REQUEST"
		return filterMsg
		
	if args.justNew is True:
		try:
			runDate = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Last_Date_Run')
			lastCheckDate=datetime.datetime.strptime(runDate[0].text, "%m/%d/%Y").date()
		except:
			lastCheckDate=datetime.date.today()
			
		releaseDate=datetime.datetime.strptime(mapReleaseDate, "%m/%d/%Y").date()
		# If it's not a new release but there is an update we still download it
		if releaseDate < lastCheckDate and needStatus not in ["UPDATE", "REINSTALL"]:	
			filterMsg = addFilterMsg(filterMsg, "NOT A NEW RELEASE")
	elif args.justUpdate is True and needStatus == "DOWNLOAD":
		filterMsg = addFilterMsg(filterMsg, "NOT AN UPDATE")

	IDFilter = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Exclude_Maps_Filters/Exlude_Map_ID')
	for f in IDFilter:
		if f.text == mapID:
			reportMessage("{:*^15} {:<35} by {:<20} Star Rating:{}".format("SKIPPING MAP", mapName, mapAuthor, mapRating))
			filterMsg = addFilterMsg(filterMsg, "MAP NAME")
			
	authorFilter = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Exclude_Maps_Filters/Exlude_Map_Author')
	for f in authorFilter:
		if f.text == mapAuthor:
			reportMessage("{:*^15} {:<35} by {:<20} Star Rating:{}".format("SKIPPING MAP", mapName, mapAuthor, mapRating))
			filterMsg = addFilterMsg(filterMsg, "AUTHOR")

	ratingFilter=getXMLRatingFilter()
	if rating < ratingFilter:
		filterMsg = addFilterMsg(filterMsg, "RATING")
			
	return filterMsg
	
###############################################################################
# Combine filter messages into a single string
###############################################################################	
def addFilterMsg(filterMsg, newMessage):
	if len(filterMsg) > 0:
		filterMsg = filterMsg + " & " + newMessage
	else:
		filterMsg = "FILTERED BY: " + newMessage
	
	return filterMsg	
	
###############################################################################
# Verify if we already have the map installed
# -Check if a mapID.info & mapID.content already exist in our custom map folder
# -Check if mapID.info MD5 hash matches current version
# Returns
#	"INSTALLED"	Map already installed and passes hash verification
#	"REINSTALL"	Map already installed but failed validation
#	"DOWNLOAD"	Map doesn't exist
#	"UPDATE"	Map installed but detecting a newer version is available
###############################################################################
def needMap(mapID, mapHash):
	infoFile=onwardPath + mapFolder + mapID + ".info"
	contentFile=onwardPath + mapFolder + mapID + ".content"	 

	# If .content file doesn't exist you need to download the map
	my_file = Path(contentFile)
	if my_file.is_file() is False:
			return "DOWNLOAD"
	
	# if .info file doesn't exist the hash check will fail so you still need to download the map
	my_file = Path(infoFile)
	if my_file.is_file() is False:
			return "REINSTALL"
						
		# check hash of .info file to verify if map the user already has is current
	h=getHash(infoFile)
	if h != mapHash:
		return "UPDATE"	

	# All test passed so we don't need this map file		
	return "INSTALLED"
	
###############################################################################
# Download a mapID.zip file and verify the MD5 sum matches
# Returns True/False on success/failure but also can return None if the user 
#	decides to abort the download
###############################################################################	
def getMap(mapID, mapDownloadURL, zipHash, fileSize, quiet=False, progressBarsGUI=None):
	# Download the Google Drive file
	downloadName=onwardPath + mapID + ".zip"
	
	gotMap=True
	if "DRIVE.GOOGLE.COM" in mapDownloadURL.upper():
		gotMap=downloadGoogleDriveFile(downloadName, mapDownloadURL, fileSize, quiet, progressBarsGUI)
	elif "KOIZ" in mapDownloadURL.upper():
		reportMessage("{:*^15} Koiz doesn't want his maps hosted anywhere except official Onward servers... Please ask him to reconsider as this tool can't access those files directly.".format("INFO"))	
		return False
	else:
		reportMessage("{:*^15} Don't know how to download URL: {}".format("ERROR", mapDownloadURL))
		return False
	
	# If download failed/aborted then no reason to unzip or check hashes
	if gotMap is False or gotMap is None:
		return gotMap
		
	# validate hash
	calculatedZipHash = getHash(downloadName)
	if zipHash != calculatedZipHash:
		reportMessage("{:*^15} Zip file hash incorrect. Expecting {} but got {}".format("ERROR", zipHash, calculatedZipHash))

		try:
			os.remove(downloadName)	
		except:
			pass		
	
		return False
	
	# Unzip file
	with ZipFile(downloadName, 'r') as zipObj:
		# Extract all the contents of zip file in current directory
		try:
			zipObj.extractall(onwardPath)
		except:
			zipObj.close()
			os.remove(downloadName)
			reportMessage("{:*^15} Failed to extract {}".format("ERROR", downloadName))
			return False
			
	zipObj.close()	
	
	# Sucessfully downloaded and extracted map so delete zip file
	delMap = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Delete_Map_Zips_After_Install')
	try:
		if delMap[0].text.upper() == "TRUE":
			os.remove(downloadName)	
	except:
		pass
		
	return gotMap


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
# Get the rating filter from command line argument or XML setting
###############################################################################
def getXMLRatingFilter():
	# Set the rating filter. If nothing is specififed use value in XML settings. If that doesn't exist default 0 / All maps
	if args.rating is not None and args.rating > 0:
		ratingFilter=args.rating
	else:
		rf = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Exclude_Maps_Filters/Ratings_Filter')
		try: 
			ratingFilter=int(rf[0].text)
		except:
			ratingFilter=0
			
	return ratingFilter
			
			
###############################################################################
# Start Downloading Maps
###############################################################################
def startDownload(progressBarsGUI=False):
	retryCount=0
	retryMaxAttempts=3
	
	while retryCount < retryMaxAttempts:
		summaryData={}
		summaryData=processFilters()
		
		if summaryData["totalToInstall"] == 0:
			reportMessage("{:*^15} No maps to install".format("INFO"))
			if progressBarsGUI is not False:	
				sg.popup("You have no maps marked for download.", title="Warning")
			return
			
		# If the user is in GUI mode disable the window from accepting input while 
		#	downloading and create the progress bars window
		global globalWindow
		oldglobalWindow=globalWindow
		
		window=None	
		if progressBarsGUI is not False:
			# Goofy bug with pySimgpleGUI where if the string grows by a character it truncates....
			# So just tack on a bunch of spaces at the end as a temporay fix	
			mapProgressText=sg.Text('Downloading Map: {:50}'.format(maps["MAP NAME"][0]), key='MAP_PROGRESS_TEXT')
			mapProgress=sg.ProgressBar(1, orientation='h', size=(57, 20), key='MAP_PROGRESS')
			allProgressText=sg.Text('Total Progress: Map 1 of {:50}'.format(summaryData["totalToInstall"]), key='ALL_PROGRESS_TEXT')
			allProgress=sg.ProgressBar(1, orientation='h', size=(57, 20), key='ALL_PROGRESS')

			installLog=sg.MLine(default_text='', size=(120, 10), autoscroll=True, font="Courier 7", background_color=COLOR_BACKGROUND, key='INSTALL_LOG')
			installLogObjs=[[installLog]]
			installLogFrame=sg.Frame(title="Install Log", title_location="n", element_justification="center", relief="groove", layout=installLogObjs) 
		
			# layout the form
			layout =	[[mapProgressText],[mapProgress],[allProgressText],[allProgress],[installLogFrame],[sg.Cancel()]]

			# create the form
			window = sg.Window('Download Progress', layout=layout, disable_close=True)
			
			# We set the global window to the current progress bar window so the function reportMessage() is displaying messages to
			#	the currently active window. Once downloads finish or are aborted we switch it back to the main window.
			globalWindow=window			
		
		# Traverse the list of maps		
		#TODO Sanity check all spreadhsheet data as looping... ie make sure filesize is a number, etc etc
		l=len(maps["MAP NAME"])
		installCount=0
		abortedByUser=False
		for i in range(0,l):			
			# Update the progress bar if in GUI mode
			if progressBarsGUI is not False:
				# check to see if the cancel button was clicked and exit loop if clicked
				event, values = window.read(timeout=0)
				if event == 'Cancel' or sg.WIN_CLOSED or event == None:			
					break		
				
				mapProgressText.Update(value='Downloading Map: {}'.format(maps["MAP NAME"][i]))
				allProgressText.Update(value='Total Progress: Map {} of {}'.format(installCount+1, summaryData["totalToInstall"]))
				allProgress.update_bar(installCount, summaryData["totalToInstall"])			
			
			if maps["MISC FIELDS"][i] in ["REINSTALL", "DOWNLOAD", "UPDATE"]:
				msg="{} of {}".format(installCount+1, summaryData["totalToInstall"])
				msg="{:*^15} {:<35} {:<25} by {:<20} size:{:<4}mb".format("DOWNLOADING", "MAP " + msg, maps["MAP NAME"][i], maps["AUTHOR"][i], maps["FILE SIZE"][i])
				reportMessage(msg)
				try:
					mapStatus=getMap(maps["ID"][i], maps["DOWNLOAD URL"][i], maps["ZIP HASH"][i], maps["FILE SIZE"][i], quiet=progressBarsGUI, progressBarsGUI=window)
					installCount = installCount + 1
					if mapStatus is True:
							msg="{:*^15} {:<35} {:<25} by {:<20} Star Rating:{}".format("INSTALLED", "Hash Verified", maps["MAP NAME"][i], maps["AUTHOR"][i], maps["RATING"][i])
							reportMessage(msg)
					elif mapStatus is None:
						abortedByUser=True
						break
					else:
						summaryData["totalMapsFailed"] = summaryData["totalMapsFailed"] + 1
				except:
					summaryData["totalMapsFailed"] = summaryData["totalMapsFailed"] + 1
			elif maps["MISC FIELDS"][i] == "INSTALLED":
				msg="{:*^15} {:<35}	{:<25} by {:<20}".format("INFO", "Already Installed", maps["MAP NAME"][i], maps["AUTHOR"][i])
				reportMessage(msg)
			else:
				msg="{:*^15} {:<35} {:<25} by {:<20} Star Rating:{}".format("FILTERED BY", maps["MISC FIELDS"][i][13:], maps["MAP NAME"][i], maps["AUTHOR"][i],  maps["RATING"][i])		
				#msg="{:*^15} Already installed	 {:<25} by {:<20}".format("INFO", maps["MAP NAME"][i], maps["AUTHOR"][i])
				reportMessage(msg)		
		
		# If we completed a full loop and was not aborted by the user then we need to update the last run date
		if abortedByUser is True:	
			reportMessage("{:*^15} Aborted by user".format("INFO"))
		elif summaryData["totalMapsFailed"] == 0:
			updateLastRunDate()
		
		msg="{:*^15} New Maps installed:{:<5}Maps Skipped:{:<10}Maps Failed Install:{:<30}Total Maps:{:<5}".format("INFO", \
			installCount, summaryData["totalAlreadyInstalled"], summaryData["totalMapsFailed"], l)
		reportMessage(msg)
		msg="{:*^15} Filterd by Rating:{:<6}Filterd by Author:{:<5}Filterd by Name:{:<9}Filterd Not New:{:<9}Total Filtered:{:<5}".format("INFO", \
			summaryData["totalSkippedRating"], summaryData["totalSkippedAuthor"],summaryData["totalSkippedName"], summaryData["totalSkippedNotNewRelease"], \
			summaryData["totalExcluded"] )
		reportMessage(msg)

		if progressBarsGUI is True:
			if window != None:
				# Switch from progress bars to original GUI and copy install log 
				globalWindow=oldglobalWindow
				msgs=installLog.get().split("\n")
				for m in msgs:
					reportMessage(m, False)
				window.close()
		else:
			# os.system("pause")
			pass
		
		# If there are any failed downloads then retry to download any missing maps again
		if summaryData["totalMapsFailed"] != 0:
			retryCount = retryCount + 1
			msg="{:*^15} {} failed to install. Retrying... Attempt {} of {}".format("ERROR", summaryData["totalMapsFailed"], retryCount, retryMaxAttempts)
			reportMessage(msg)
		else:
			break


###############################################################################
# Setup the GUI
###############################################################################
def displayGUI():
	summaryData = {}


	###########################################################################
	# GUI Objects
	###########################################################################	
	# Create table object
	headings=["Map Name", "Author", "Status", "Size", "Rating", "Published", "Updated"]
	table=sg.Table(values=[], headings=headings, max_col_width=55,
					auto_size_columns=False,
					display_row_numbers=False,
					col_widths=[30,25,45, 12,12,13,13],
					justification='center',
					num_rows=20,
					key='MAPS_TABLE',
					vertical_scroll_only=False,
					font='Courier 7',
					header_font='Courier 9')


	###########################################################################
	# Quick Filters
	quickFiltersList=["Use All Filters", "Only Download Updates", "Download Updates & New Releases"]
	qfDefault=0
	if args.justUpdate is True and args.justNew is False:
		qfDefault=1
	elif args.justUpdate is False and args.justNew is True:
		qfDefault=2
	quickFiltersCombobox=sg.Combo(quickFiltersList, readonly=True, visible=True, size=(32,1), default_value=quickFiltersList[qfDefault], font='Courier 8', change_submits=True, key="QF_SELECTED")
	quickFiltersFrame=sg.Frame(title="Quick Filters", title_location="n", element_justification="center", relief="groove", font='Courier 10', pad=(1,0,0,4), layout=[[quickFiltersCombobox]])	
	
	###########################################################################
	# Filter Selected
	includeBtn=sg.Button(button_text="Include", size=(7,1), font='Courier 8', key='INCLUDE_SELECTED')
	excludeBtn=sg.Button(button_text="Exclude", size=(7,1), font='Courier 8', key='EXCLUDE_SELECTED')		
	seletedFilterObjs=[includeBtn, excludeBtn]
	filterFrameSelected=sg.Frame(title="Selected Maps", title_location="n", element_justification="center", relief="groove", font='Courier 10', pad=(1,0,0,4), layout=[seletedFilterObjs]) 
	
	###########################################################################
	# Author Filter
	authorList=list(set( maps["AUTHOR"]))	# Get unique lists of Authors
	authorList.sort(key=str.casefold)		# Put authors in ABC order
	authorListCombobox=sg.Combo(authorList, readonly=True, visible=True, size=(20,1), font='Courier 8', change_submits=True, default_value=authorList[0], key="AUTHOR_SELECTED")
	# Since we need to keep the FILTER/CLEAR in sync we need to check if the default authtor is currently being filtered or not
	btnText="EXCLUDE"
	if processXMLFilter("EXISTS", "Exlude_Map_Author", authorList[0]):
		btnText="INCLUDE"
	authorBtn=sg.Button(button_text=btnText, size=(7,1), font='Courier 8', key='AUTHOR')	
	authorObjs=[authorListCombobox, authorBtn]
	filterFrameAuthor=sg.Frame(title="Author", title_location="n", element_justification="center", relief="groove", font='Courier 10', pad=(1,0,0,4), layout=[authorObjs]) 

	###########################################################################	
	# Rating Filter
	ratingFilter=getXMLRatingFilter()
	
	ratingList=["All", "1 Star", "2 Star", "3 Star", "4 Star", "5 Star"]
	ratingListCombobox=sg.Combo(ratingList, readonly=True, visible=True, size=(8,1), default_value=ratingList[ratingFilter], font='Courier 10',)
	ratingBtn=sg.Button(button_text="Apply", size=(7,1), font='Courier 8', key='RATING')		
	ratingObjs=[ratingListCombobox, ratingBtn]
	filterFrameRating=sg.Frame(title="Min Star Rating", title_location="n", element_justification="center", relief="groove", font='Courier 10', pad=(1,0,0,4), layout=[ratingObjs]) 
	
	###########################################################################	
	# Filters Layout
	filterFrameObjs=[quickFiltersFrame, filterFrameSelected, filterFrameAuthor, filterFrameRating]
	filterFrame=sg.Frame(title="Exclude Installing Maps By", title_location="n", relief="groove", pad=(1,1,0,4),layout=[filterFrameObjs]) 

	###########################################################################
	# Summary
	summaryLine=sg.Text("",size=(80,2), key='SUMMARY_LINE')	
	installLog=sg.MLine(default_text='', size=(150, 10), autoscroll=True, font='Courier 7', background_color=COLOR_BACKGROUND, key='INSTALL_LOG')
	installLogObjs=[[installLog], [summaryLine]]
	installLogFrame=sg.Frame(title="Install Log", title_location="n", element_justification="center", relief="groove", layout=installLogObjs) 
	
	###########################################################################
	# Bottom Row
	startDownloadBtn=sg.Button(button_text="Start Download", size=(10,2), key='DOWNLOAD')
	helpBtn=sg.Button(button_text="Help", key='HELP')
	###########################################################################
	# Settings objects
	settingsObjs=	[		sg.Button(button_text="Load", size=(8,1), font='Courier 8', key="LOAD"),		\
							sg.Button(button_text="Save", size=(8,1), font='Courier 8', key="SAVE"),		\
							sg.Button(button_text="Default", size=(8,1), font='Courier 8',key="DEFAULT")	\
					]
	settingFrame=sg.Frame(title="Filters", title_location="n", element_justification="center", relief="groove", font='Courier 10', pad=(0,0,0,4), layout=[settingsObjs]) 
	
	SchedHourText=sg.Text('Hour:')
	SchedHour=sg.Combo(list(range(0,23)), readonly=True, visible=True, size=(2,1), default_value="23", font='Courier 10', key='SCHEDULE_HOUR')
	SchedMinText=sg.Text('Min:')	
	SchedMin=sg.Combo(["00","15","30","45"], readonly=True, visible=True, size=(2,1), default_value="30", font='Courier 10',  key='SCHEDULE_MIN')	
	taskSchedBtn=sg.Button(button_text="Schedule Task", key='SCHEDULE')
	schedObjs=[[SchedHourText, SchedHour, SchedMinText, SchedMin, taskSchedBtn]]
	taskSchedFrame=sg.Frame(title="Run Daily via Windows Task Scheduler", title_location="n", element_justification="center", relief="groove", layout=schedObjs) 
		
	###########################################################################
	# Layout of GUI
	layout = [ [filterFrame], [table], [installLogFrame], [startDownloadBtn, helpBtn, settingFrame, taskSchedFrame]	 ]

	# ------ Create Window ------
	#sg.change_look_and_feel('GreenTan')
	window = sg.Window('Onward Custom Map Installer', layout, font='Courier 12', size=(800,650) )

	# Finalize the layout and then update populate the table / status lines otherwise won't update until user does something to trigger the event loop	
	window.Finalize()	
	global globalWindow
	globalWindow=window
	
	global errorMsgBuffer
	errorInBuffer = False
	for e in errorMsgBuffer:
		if e.find("ERROR") != -1:
			errorInBuffer = True
			break
	
	if errorInBuffer is False:
		updateMapData(window, summaryData)
	else:
		# Report this just to clear the buffer
		reportMessage("ERROR CAN'T CONTINUE...")
	
	###########################################################################
	# End GUI Objects
	###########################################################################	
	
	#from pprint import pprint
	#pprint(vars(table))
	
	# Since some messages were reported before the GUI was created we need to flush the buffer to the screen
	reportMessage("", False)
	
	# ------ Event Loop ------
	while True:
		event, values = window.read()
		if event == sg.WIN_CLOSED:
			break	
		# If detected an error message in the buffer we shouldn't let the user do anything except 
		#	read the messages and quit the application
		if errorInBuffer is True:
			reportMessage("Error detected program can't do anything until resolved. This error can't be resolved while program is running...")
			continue
		elif event == "LOAD":
			loadSettings()
		elif event == "SAVE":
			saveSettings()
		elif event == "DEFAULT":
			createDefaultSettings()	
		elif event == "QF_SELECTED":
			qfSelected=str(quickFiltersCombobox.Get())
			if qfSelected == quickFiltersList[0]:
				args.justUpdate=False
				args.justNew=False
			elif qfSelected == quickFiltersList[1]:
				args.justUpdate=True
				args.justNew=False
			elif qfSelected == quickFiltersList[2]:
				args.justUpdate=True
				args.justNew=True
		elif event == "INCLUDE_SELECTED":
			for i in table.SelectedRows:
				processXMLFilter("REMOVE", "Exlude_Map_ID", maps["ID"][i])
		elif event == "EXCLUDE_SELECTED":
			for i in table.SelectedRows:		
				processXMLFilter("ADD", "Exlude_Map_ID", maps["ID"][i])
		elif event == "AUTHOR":
			author=str(authorListCombobox.Get())
			if processXMLFilter("EXISTS", "Exlude_Map_Author", author) == False:
				processXMLFilter("ADD", "Exlude_Map_Author", author)
			else:
				processXMLFilter("REMOVE", "Exlude_Map_Author", author)								
		elif event == "RATING":
			rf = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Exclude_Maps_Filters/Ratings_Filter')
			try:
				rf[0].text=str(ratingList.index(ratingListCombobox.Get()))
			except:
				# TODO: This should probably be more specific than just reseting all to default
				createDefaultSettings()	
		elif event == "SCHEDULE":
			createTask(SchedHour.Get(), SchedMin.Get())
		elif event == "DOWNLOAD":
			window.Disappear()
			startDownload(progressBarsGUI=True)
			#updateMapData(window, summaryData)
			window.Reappear()
			window.BringToFront()
		elif event == "HELP":
			webbrowser.open_new("https://github.com/wescotte/OnwardCustomMapSync")
			
		updateMapData(window, summaryData)
	window.close()

###############################################################################
# Update the GUI table and summary lines
###############################################################################			
def updateMapData(window, summaryData):
	table=window['MAPS_TABLE']
	summaryLine=window['SUMMARY_LINE']
	installLog=window['INSTALL_LOG']
	
	summaryData={}
	summaryData=processFilters()

	tableData=[]
	
	rc=[]
	
	l=len(maps["MAP NAME"])	
	for i in range(0,l):
		tableData.append([maps["MAP NAME"][i], maps["AUTHOR"][i], maps["MISC FIELDS"][i],  maps["FILE SIZE"][i] + "mb", maps["RATING"][i], maps["RELEASE DATE"][i], maps["UPDATE DATE"][i]])
		if maps["MISC FIELDS"][i] in ["DOWNLOAD", "UPDATE", "REINSTALL"]:
			rc.append((i, COLOR_DOWNLOAD, COLOR_BACKGROUND))
		elif maps["MISC FIELDS"][i].find("FILTER") != -1:
			rc.append((i,COLOR_FILTERED, COLOR_BACKGROUND))
		else:
			rc.append((i,COLOR_DEFAULT, COLOR_BACKGROUND))
	summaryText='To Install:{:<4}Already Installed:{:<4}Maps Excluded:{:<4}Total Maps:{:<4}\nExcluded By	Rating:{:<4}Author:{:<4}Name:{:<4}Release Date:{:<4}'.format( \
			summaryData["totalToInstall"], summaryData["totalAlreadyInstalled"], summaryData["totalExcluded"], summaryData["totalMaps"],  \
			summaryData["totalSkippedRating"], summaryData["totalSkippedAuthor"], summaryData["totalSkippedName"], summaryData["totalSkippedNotNewRelease"] )
	
	table.Update(values=tableData, row_colors=rc)
	summaryLine.Update(value=summaryText)

	# Update the button text on the Author Remove to reflect the current seletion
	author=str(window["AUTHOR_SELECTED"].Get())
	if processXMLFilter("EXISTS", "Exlude_Map_Author", author) == True:
		window["AUTHOR"].update(text="INCLUDE")	
	else:
		window["AUTHOR"].update(text="EXCLUDE")		

	window.Finalize()

###############################################################################
# Traverse the list of maps and keep track of which maps to download or skip
###############################################################################
def processFilters():
	summaryData={}
	summaryData.update({	"totalToInstall":0,		"totalAlreadyInstalled":0,																\
							"totalSkippedRating":0, "totalSkippedAuthor":0,		"totalSkippedName":0,	"totalSkippedNotNewRelease":0,		\
							"totalExcluded":0,		"totalMapsFailed":0,		"totalMaps":0 })
	
	ratingFilter=getXMLRatingFilter()

	l=len(maps["MAP NAME"])
	summaryData["totalMaps"]=l
	
	for i in range(0,l):
		status=""
		
		needStatus=needMap(maps["ID"][i], maps["INFO HASH"][i])
		filterStatus=filterMap(needStatus, maps["ID"][i], maps["MAP NAME"][i], maps["AUTHOR"][i], maps["RATING"][i], maps["RELEASE DATE"][i])
			
		# If a map is already installed flag to skip it		
		if needStatus == "INSTALLED":
			summaryData["totalAlreadyInstalled"]=summaryData["totalAlreadyInstalled"]+1
			status=needStatus
		# If we use the -justUpdate flag and an update is available download it regardless of any filters.
		# Otherwise only download if we need it and there are no filters.
		elif (needStatus in ["UPDATE", "REINSTALL", "DOWNLOAD"] and filterStatus == ""):
			summaryData["totalToInstall"]=summaryData["totalToInstall"]+1
			status=needStatus
		else:
			# If we need the map but we have the justUpdate flag enabled then it's possible there are no filters and thus we should upate
			# the status to reflect his special case
			if needStatus in ["DOWNLOAD", "REINSTALL"] and filterStatus == "":
				status = "FILTERED BY: ONLY INSTALL UPDATES"
			else:
				status=filterStatus 
			if status.find("RATING") != -1:
				summaryData["totalSkippedRating"]=summaryData["totalSkippedRating"]+1
			elif status.find("AUTHOR") != -1:
				summaryData["totalSkippedAuthor"]=summaryData["totalSkippedAuthor"]+1
			elif status.find("MAP NAME") != -1:
				summaryData["totalSkippedName"]=summaryData["totalSkippedName"]+1
			elif status.find("NOT A NEW RELEASE") != -1:
				summaryData["totalSkippedNotNewRelease"]=summaryData["totalSkippedNotNewRelease"]+1
			summaryData["totalExcluded"]=summaryData["totalExcluded"]+1			
		
		# Special case where we don't have a map installed but rating is -1 meaning author doesn't want distribution
		if status==needStatus and filterStatus.find("UNAVAILBLE") != -1:
			status=filterStatus
			#summaryData["totalToInstall"]=summaryData["totalToInstall"]-1
			summaryData["totalSkippedName"]=summaryData["totalSkippedName"]+1
		
		# Repurposing the "MISC FIELDS" columns for status becuase after we load the intial data
		# we don't need/want that data anymore anyway and it's just easiser this way
		maps["MISC FIELDS"][i]=status
		
	return summaryData
	
	
###############################################################################
# Add/Remove or Check if a map filter exists in the XML data
###############################################################################
def processXMLFilter(method, tag, text=None):
	if method=="EXISTS":
		s='/Onward_Custom_Map_Sync_Settings/Exclude_Maps_Filters/%s[text()="%s"]' % (tag,text)
		rf = XMLSettings.xpath(s)
		if len(rf) > 0:
			return True
		else:
			return False
			
	if method=="ADD":
		e=etree.Element(tag)
		e.text=str(text)
		#e.tail = '\n'	# Keeps the formatting nice in the XML file
		rf = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Exclude_Maps_Filters')
		rf[0].insert(-1,e)	# Add at the end of list TODO: Wrap this in a try perhaps?
		
	if method=="REMOVE":
		s='/Onward_Custom_Map_Sync_Settings/Exclude_Maps_Filters/%s[text()="%s"]' % (tag,text)
		rf = XMLSettings.xpath(s)
		for el in rf:
			el.getparent().remove(el)

###############################################################################
# Run some basic checks on the map list downloaded for Google Drive
#	In addition to sanity checks on the data also check what the min version of
#	tool is required to process that data and check for any "annoncements"
###############################################################################
def validateMapList():
	valid=True
	global onwardPath
	
	if "APPDATA" not in os.environ:
		reportMessage("{:*^15} APPDATA environmental variable not set. Don't know how to find Onward Custom Maps folder".format("ERROR"))
		valid=False
	else:	
		onwardPath = os.environ["APPDATA"] + onwardPath
	
	# Make sure the Onward folder exists
	if os.path.isdir(onwardPath) is False:
		reportMessage("{:*^15} Can't find ONWARD folder in '{}'".format("ERROR",onwardPath))
		valid=False
		
	global maps
	maps = {}
	# Download the custom maps list from Google Drive
	reportMessage("{:*^15} Obtaining the complete custom maps list from server.".format("INFO"))	
	try:
		downloadGoogleDriveFile(filenameMapList, mapListGoogleURL, 0, quiet=True)
	except AssertionError as error:
		reportMessage("{:*^15} Unable to obtain the list of custom maps... Please try again later.".format("ERROR"))	
		valid=False

	reportMessage("{:*^15} List downloaded sucessfully...".format("INFO"))

	# Read the maps list from the file into a Dictionary
	f = open(filenameMapList)
	reader = csv.DictReader(f)

	for row in reader:
		for column, value in row.items():
			maps.setdefault(column.upper(), []).append(value)
	f.close()
	
	# Make sure the map list we download contains valid data	
	validKeys = ["MAP NAME", "AUTHOR", "ID", "INFO HASH", "RELEASE DATE", "UPDATE DATE", "RATING", "FILE SIZE", "DOWNLOAD URL", "ZIP HASH", "MISC FIELDS"]
	# Make sure all keys exist
	for k in validKeys:
		if k not in maps.keys():
			reportMessage("{:*^15} Can to find \"{}\" data in map list... Make sure you are running the current version of this tool.".format("ERROR",k))
			valid=False
	
	# Make sure there is some data in the file
	l=len(maps["MAP NAME"])
	if l is None or l < 1:	
		reportMessage("{:*^15} Map list downloaded but is empty... Try again later.".format("ERROR"))	
		valid=False		
	
	# Verify the version of the map data works wiht this version of the application
	try:
		vPos=maps["MISC FIELDS"].index("VERSION")	
		mapListVer=float(maps["MISC FIELDS"][vPos+1])
		if appVersion < mapListVer:
			reportMessage("{:*^15} Your application version is out of date. Please update".format("ERROR"))
			reportMessage("{:*^15} Check for updates at https://github.com/wescotte/OnwardCustomMapSync".format("ERROR"))
			valid=False
	except:
		reportMessage("{:*^15}	Can't validate version of Maps List.".format("ERROR"))
		valid=False
	
	# Check for any announcements to display to the user
	# Used for future proofing so I can inform users using this tool interactively is anything breaks
	try:
		vPos=0
		while True:
			vPos=maps["MISC FIELDS"].index("ANNOUNCEMENT", vPos)+1
			reportMessage("{:*^15} {}".format("ANNOUNCEMENT", maps["MISC FIELDS"][vPos]))
	except:
		pass
		
	return valid
###############################################################################
# Obtain the custom map list from Google Doc and install missing maps
###############################################################################
if __name__ == "__main__":
	# Hide the terminal window if running in GUI mode
	# Found how to do this from https://github.com/pyinstaller/pyinstaller/issues/1339#issuecomment-122909830
	if args.noGUI is False:
		if sys.platform.lower().startswith('win'):
			import ctypes
		whnd = ctypes.windll.kernel32.GetConsoleWindow()
		if whnd != 0:
			ctypes.windll.user32.ShowWindow(whnd, 0)
		# if you wanted to close the handles...
		#ctypes.windll.kernel32.CloseHandle(whnd)			
			pass
			
	if args.scheduleDaily is not None:
		#createTask(args.scheduleDaily)
		exit()
	
	loadSettings()
	
	# If the user specifies to log the 
	enableLogging=False
	
	# Check if user enabled logging via command line
	if args.logResults is True:
		enableLogging = True

	# Check if user enabled logging via XML setting
	parm = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Write_To_Logfile')
	try:
		if parm[0].text.upper() == "TRUE":	
			enableLogging=True
	except:
		pass
		
	if enableLogging is True:
		# Before start logging check if the current log is exceeding max size and delete if necessary
		parm = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Log_Size_Limit_inMB')
		sizeLimit=0
		try:
			sizeLimit=int(parm[0].text) * 1024**2 # Convert to megabytes
		except:
			sizeLimit = 100 * 1024**2 # Default to 100mb
		
		# Get file size of log file and delete if it exceeds it.
		try: 
			fSize=os.path.getsize(logFilename)
			if fSize > sizeLimit:
				os.remove(logFilename)
		except:
			pass # log file doesn't exist yet
			
		logFileGlobal=open(logFilename, "a+")
		
	# Download map data from Google Drive and validate it's contents	
	v=validateMapList()
	# Display the GUI or if -noGUI specified just start downloading
	if args.noGUI is True:
		if v is True:
			startDownload()
	else:	
		displayGUI()

	
	# Delete the custom map metadata
	delMapList = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Delete_Map_List_On_Exit')
	try:
		if delMapList[0].text.upper() == "TRUE":	
			os.remove(filenameMapList)
	except:
		pass
		

	# If the user happens to be running this from command prompt 
	if args.noGUI is False:
		if sys.platform.lower().startswith('win'):
			import ctypes
		whnd = ctypes.windll.kernel32.GetConsoleWindow()
		if whnd != 0:
			ctypes.windll.user32.ShowWindow(whnd, 2)
			pass

	# Close the log file on exist
	if enableLogging is True:
		logFileGlobal.close()
		


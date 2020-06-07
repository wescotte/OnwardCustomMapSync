import os
import csv
import hashlib
import argparse
import datetime 
from zipfile import ZipFile
from pathlib import Path

from lxml import etree

# gdown required libs
import requests
import re
import sys
import tqdm
import os.path as osp

# GUI libs
import PySimpleGUI as sg

# TODO --- Use enums everywhere it makes sense! Right now it's kinda messy
# TODO --- "Only update existing maps" quick functionality
#		Only look to download maps already installed that have updates
#		Add a "NEW" status that highlights maps that didn't exist last time the app was run?

###############################################################################
# Global Variables
###############################################################################
appVersion = 1.00

settingsFile="Onward Custom Map Sync Settings.xml"
XMLSettings = None
downloadedAnything = False	# If this is true we update the Last Run Date setting in the XML file on exit

filenameMapList = 'Map List.csv'
mapListGoogleURL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQ3uNvIexndfAxla3VACEpz6wCSLs8v8w1VzdmUPEw7SxuInqxbOEje_fUoxR5vmGnBZ9BRLloMJ0Xc/pub?gid=0&single=true&output=csv'
maps = {}	# Dictionary of map data download from Google Drive Spreadsheet

if "APPDATA" not in os.environ:
	reportMessage("***ERROR*** APPDATA environmental variable not set. Don't know how to find Onward Custom Maps folder")
	exit()
	
onwardPath = os.environ["APPDATA"] + "\..\LocalLow\Downpour Interactive\Onward\\"
mapFolder = "CustomContent\\"

# Pointer to the GUI window
globalWindow = None

		
###############################################################################
# Setup Command Line Arguments
###############################################################################
parser = argparse.ArgumentParser(description='Onward Custom Map Downloader version %s' %(appVersion))
parser.add_argument('-rating', type=int,
					help='Rating Filter: Only install maps that have this star rating or better')
parser.add_argument("-noGUI", help="Disable the GUI and run in console mode", action='store_true')
parser.add_argument("-justUpdate", help="Only download updates for maps already installed", action='store_true')
parser.add_argument("-justNew", help="Install only new maps (RELEASE DATE after the last Last_Date_Run in XML settings file) regardless of rating", action='store_true')               
parser.add_argument("-scheduleDaily", help="Add an entry to the Windows Task Scheduler to run daily at specified hh:mm in 24-hour clock / miltary time format") 

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
	exlude = etree.SubElement(root, 'Exclude_Maps_Filters')	
	
	rFilter = etree.SubElement(exlude, 'Ratings_Filter')
	
	runDate.text=str(datetime.date.today().strftime("%m/%d/%Y"))
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
		reportMessage('***ERROR*** Unable to update last run date. Your "Onward Custom Map Sync Settings.xml" might be corrupted....')
		reportMessage('***ERROR***		You can erase this file and run the program again and it will create a new one with default settings')
	saveSettings()
	

###############################################################################
# Add an entry for this program to run automatically via 
# the Windows Task Scheduler
###############################################################################
def createTask(timeToRun):
	print("Feature not implimented yet...")
	exit()
	
	# How to delete a task...
	"""
	import pythoncom, time, win32api
	from win32com.taskscheduler import taskscheduler
	test_task_name='test_addtask_1.job'

	ts=pythoncom.CoCreateInstance(taskscheduler.CLSID_CTaskScheduler,None,
								  pythoncom.CLSCTX_INPROC_SERVER,taskscheduler.IID_ITaskScheduler)

	tasks=ts.Enum()
	for task in tasks:
		reportMessage(task)
	if test_task_name in tasks:
		reportMessage('Deleting existing task '+test_task_name)
		ts.Delete(test_task_name)	
	"""
	
	reportMessage(timeToRun)
	
	# Get path of EXE
	taskToRun=os.getcwd() + "\\" + sys.argv[0]
	#return
	"""
	#creates a daily task
	#def create_daily_task(name, cmd, hour=None, minute=None):
	name="Onward Custom Map Sync"
	cmd=taskToRun
	cmd = cmd.split()
	hour=22
	minute=55

	
	import time
	from win32com.taskscheduler import taskscheduler
	
	ts = pythoncom.CoCreateInstance(taskscheduler.CLSID_CTaskScheduler,None,
									pythoncom.CLSCTX_INPROC_SERVER,
									taskscheduler.IID_ITaskScheduler)
	print("here");
	if '%s.job' % name not in ts.Enum():
		task = ts.NewWorkItem(name)
		task.SetApplicationName(cmd[0])
		task.SetParameters(' '.join(cmd[1:]))
		task.SetPriority(taskscheduler.REALTIME_PRIORITY_CLASS)
		task.SetFlags(taskscheduler.TASK_FLAG_RUN_ONLY_IF_LOGGED_ON)
		task.SetAccountInformation('', None)
		ts.AddWorkItem(name, task)
		run_time = time.localtime(time.time() + 300)
		tr_ind, tr = task.CreateTrigger()
		tt = tr.GetTrigger()
		tt.Flags = 0
		tt.BeginYear = int(time.strftime('%Y', run_time))
		tt.BeginMonth = int(time.strftime('%m', run_time))
		tt.BeginDay = int(time.strftime('%d', run_time))

		if minute is None:
			tt.StartMinute = int(time.strftime('%M', run_time))

		else:
			tt.StartMinute = minute

		if hour is None:
			tt.StartHour = int(time.strftime('%H', run_time))

		else:
			tt.StartHour = hour

		tt.TriggerType = int(taskscheduler.TASK_TIME_TRIGGER_DAILY)
		tr.SetTrigger(tt)

		pf = task.QueryInterface(pythoncom.IID_IPersistFile)
		pf.Save(None,1)

		task.Run()
		print("here2")
	else:
		raise KeyError("%s already exists" % name)
		print("h343")


	task = ts.Activate(name)
	exit_code, startup_error_code = task.GetExitCode()
	return win32api.FormatMessage(startup_error_code)
	"""




	import datetime
	import win32com.client

	scheduler = win32com.client.Dispatch('Schedule.Service')
	scheduler.Connect()
	root_folder = scheduler.GetFolder('\\')
	task_def = scheduler.NewTask(0)

	# Create trigger
	start_time = datetime.datetime.now() + datetime.timedelta(minutes=1)
	TASK_TRIGGER_TIME = 1
	trigger = task_def.Triggers.Create(TASK_TRIGGER_TIME)
	trigger.StartBoundary = start_time.isoformat()

	# Create action
	TASK_ACTION_EXEC = 0
	action = task_def.Actions.Create(TASK_ACTION_EXEC)
	action.ID = 'DO NOTHING'
	action.Path = 'taskToRun'
	action.Arguments = '-noGUI -quiet"'

	# Set parameters
	task_def.RegistrationInfo.Description = 'Onward Customer Map Downloader'
	task_def.Settings.Enabled = True
	task_def.Settings.StopIfGoingOnBatteries = False

	# Register task
	# If task already exists, it will be updated
	TASK_CREATE_OR_UPDATE = 6
	TASK_LOGON_NONE = 0
	root_folder.RegisterTaskDefinition(
		'Test Task',  # Task name
		task_def,
		TASK_CREATE_OR_UPDATE,
		'',  # No user
		'',  # No password
		TASK_LOGON_NONE)

	

###############################################################################
# Inform the user of a message
# -noGUI means stdout
# -quiet means log to Ownard Custom Map Sync.log
# Otherwise display in the status log 
###############################################################################	
def reportMessage(message):

	global globalWindow	
	if globalWindow is not None:
		color="black"
		#if message.find("ERROR") != -1:
		#	color="red"
		print(message)
		globalWindow["INSTALL_LOG"].update(message + "\n", text_color_for_value=color, append=True)
	else:
		print(message)
	
###############################################################################
# Download a file from Google Drive
# Adapted from gdown library
# https://github.com/wkentaro/gdown
###############################################################################				
def downloadGoogleDriveFile(localFileName, url, fileSize, quiet=True, progressBarsGUI=None):
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
		print("To:", localFileName, file=sys.stderr)
	
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
				if event == 'Cancel' or event == None:
					progressBarsGUI.close()
					global globalWindow
					globalWindow=None
					return False					

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
# Returnss 
#	"" if map isn't filterd otherwise returns the type of filter detected
#	as a string
###############################################################################
def filterMap(mapID, mapName, mapAuthor, mapRating, mapReleaseDate):
	filterMsg = ""
	
	if args.justNew is True:
		try:
			runDate = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Last_Date_Run')
			lastCheckDate=date(runDate[0].text)
		except:
			lastCheckDate=datetime.date.today()
		if date(mapReleaseDate) <= lastCheckDate:
			return "FILTERED BY: NOT A NEW RELEASE"
	
	# mapRating going to be a string so convert it to an integer
	try:
		rating=int(mapRating)
	except:
		rating=0
		print(mapRating)
		
	if rating == -1:
		filterMsg="UNAVAILBLE FOR D/L AT AUTHROR'S REQUEST"
		return filterMsg
		
	IDFilter = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Exclude_Maps_Filters/Exlude_Map_ID')
	for f in IDFilter:
		if f.text == mapID:
			reportMessage("***SKIPPING MAP*** \"%s\" ID: %s by %s ---- This map is marked not to install." %(mapName, mapID, mapAuthor))
			filterMsg = "FILTERED BY: MAP NAME"
			
	authorFilter = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Exclude_Maps_Filters/Exlude_Map_Author')
	for f in authorFilter:
		if f.text == mapAuthor:
			reportMessage("***SKIPPING MAP*** \"%s\" ID: %s by %s ---- Filtered by Author." %(mapName, mapID, mapAuthor))
			if len(filterMsg) > 0:
				filterMsg = filterMsg + " & AUTHOR"
			else:
				filterMsg = "FILTERED BY: AUTHOR"

	ratingFilter=getXMLRatingFilter()
	if rating < ratingFilter:
		if len(filterMsg) > 0:
			filterMsg = filterMsg + " & RATING"
		else:
			filterMsg = "FILTERED BY: RATING"
			
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
###############################################################################	
def getMap(mapID, mapDownloadURL, zipHash, fileSize, quiet=False, progressBarsGUI=None):
	# Set this to True so we keep track of the last time we actually downloaded content
	global downloadedAnything
	downloadedAnything=True
	
	# Download the Google Drive file
	downloadName=onwardPath + mapID + ".zip"
	
	if "DRIVE.GOOGLE.COM" in mapDownloadURL.upper():
		if downloadGoogleDriveFile(downloadName, mapDownloadURL, fileSize, quiet, progressBarsGUI) == False:
			return False
	elif "KOIZ" in mapDownloadURL.upper():
		reportMessage("***INFO*** Koiz doesn't want his maps hosted anywhere except official Onward servers... Please ask him to reconsider as this tool can't access those files directly.")
		return False
	else:
		reportMessage("***ERROR*** Don't know how to download URL: %s" % mapDownloadURL)
		return False
		
	# validate hash
	calculatedZipHash = getHash(downloadName)
	if zipHash != calculatedZipHash:
		reportMessage("***ERROR***: Zip file hash incorrect. Expecting %s but got %s" % (zipHash, calculatedZipHash))
	# Sucessfully downloaded and extracted map so delete zip file
		delMap = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Delete_Map_Zips_After_Install')
		try:
			if delMap[0].text.upper() == "TRUE":
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
			reportMessage("***ERROR***: Failed to extract %s" % downloadName)
			return False
			
	zipObj.close()	
	
	# Sucessfully downloaded and extracted map so delete zip file
	delMap = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Delete_Map_Zips_After_Install')
	try:
		if delMap[0].text.upper() == "TRUE":
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
	summaryData={}
	summaryData=processFilters()
	
	if summaryData["totalToInstall"] == 0:
		reportMessage("***INFO*** No maps to install")
		return
		
	# If the user is in GUI mode disable the window from accepting input while 
	#	downloading and create the progress bars window
	global globalWindow
	oldglobalWindow=globalWindow
	
	window=None	
	if progressBarsGUI is not False:
		if summaryData["totalToInstall"] == 0:
			sg.popup("You have no maps marked for download.", title="Warning")
			return

		mapProgressText=sg.Text('Downloading Map: %s' % maps["MAP NAME"][0], key='MAP_PROGRESS_TEXT')
		mapProgress=sg.ProgressBar(1, orientation='h', size=(57, 20), key='MAP_PROGRESS')
		allProgressText=sg.Text('Total Progress: Map 1 of %d' % (summaryData["totalToInstall"]), key='ALL_PROGRESS_TEXT')
		allProgress=sg.ProgressBar(1, orientation='h', size=(57, 20), key='ALL_PROGRESS')

		installLog=sg.MLine(default_text='', size=(120, 10), autoscroll=True, font="monospace 7", key='INSTALL_LOG')
		installLogObjs=[[installLog]]
		installLogFrame=sg.Frame(title="Install Log", title_location="n", element_justification="center", relief="groove", layout=installLogObjs) 
	
		# layout the form
		layout = 	[[mapProgressText],[mapProgress],[allProgressText],[allProgress],[installLogFrame],[sg.Cancel()]]

		# create the form
		window = sg.Window('Download Progress', layout)
		
		# We set the global window to the current progress bar window so the function reportMessage() is displaying messages to
		#	the currently active window. Once downloads finish or are aborted we switch it back to the main window.
		globalWindow=window 

	
	# Traverse the list of maps		
	#TODO Sanity check all spreadhsheet data as looping... ie make sure filesize is a number, etc etc
#	summaryData.update({	"totalToInstall":0, 	"totalAlreadyInstalled":0, 																\
#							"totalSkippedRating":0, "totalSkippedAuthor":0, 	"totalSkippedName":0, 	"totalSkippedNotNewRlease":0,		\
#							"totalExcluded":0, 		"totalMapsFailed":0, 		"totalMaps":0 })

	l=len(maps["MAP NAME"])
	installCount=0
	for i in range(0,l):
		if window is None:
			break
			
		# Update the progress bar
		if progressBarsGUI is not False:
			# check to see if the cancel button was clicked and exit loop if clicked
			event, values = window.read(timeout=0)
			if event == 'Cancel' or event == None:
				globalWindow=oldglobalWindow
				break		
				
			mapProgressText.Update(value='Downloading Map: %s' % maps["MAP NAME"][i])
			allProgressText.Update(value='Total Progress: Map %d of %d' % (installCount, summaryData["totalToInstall"]))
			allProgress.update_bar(installCount, summaryData["totalToInstall"])			
			
		if maps["MISC FIELDS"][i] in ["REINSTALL", "DOWNLOAD", "UPDATE"]:
			reportMessage("***DOWNLOADING*** MAP %d of %d: NAME: %s by %s size:%smb" % (installCount, summaryData["totalToInstall"], maps["MAP NAME"][i], maps["AUTHOR"][i], maps["FILE SIZE"][i]))
			if getMap(maps["ID"][i], maps["DOWNLOAD URL"][i], maps["ZIP HASH"][i], maps["FILE SIZE"][i], quiet=False, progressBarsGUI=window) is True:
					installCount = installCount + 1
					reportMessage("\n***INSTALLED***       \"%s\" by %s\tID:%s\tMap Star Rating: %s\n" %(maps["MAP NAME"][i].ljust(30), maps["AUTHOR"][i].ljust(15), maps["ID"][i], maps["RATING"][i]))
			else:
					summaryData["totalMapsFailed"] = summaryData["totalMapsFailed"] + 1
					reportMessage("\n***ERROR*** Map    \"%s\" ID:%s did not have the expected hash value... This map will not be installed" %(maps["MAP NAME"][i], maps["ID"][i]))	
		else:
			reportMessage("***INFO*** Skipped installing %s by %s --- %s" % (maps["MAP NAME"][i], maps["AUTHOR"][i], maps["MISC FIELDS"][i]))
			
	reportMessage("\n\n***INFO*** Maps Installed: %s\tAlready Installed: %s\tSkipped-Low Rating: %s\tSkipped-Custom Filter: %s\tInstall Failed: %s\tTotal Maps: %s" \
		% (installCount, summaryData["totalAlreadyInstalled"], summaryData["totalSkippedRating"], summaryData["totalExcluded"], summaryData["totalMapsFailed"], l))

	if progressBarsGUI is False:
		os.system("pause")
	else:
		if window != None:
			globalWindow=oldglobalWindow	# Switch back to the main UI window so reportMessage() is displaying in the correct place
			try:
				globalWindow["INSTALL_LOG"].update(installLog.get(), append=False)	# Move the install log to the main window
			except:
				pass
			window.close()




###############################################################################
# Setup the GUI
###############################################################################
def displayGUI():
	summaryData = {}


	###########################################################################
	# GUI Objects
	###########################################################################	
	# Create table object
	rows, cols = (l, 6) 
	tableData = [[""]*cols]*rows 	
	headings=["Map Name", "Author", "Status", "Size", "Rating", "Published", "Updated"]
	table=sg.Table(values=tableData[1:][:], headings=headings, max_col_width=55,
					auto_size_columns=False,
					display_row_numbers=False,
					col_widths=[30,25,45, 13,13,13,13],
					justification='center',
					num_rows=20,
					key='MAPS_TABLE',
					vertical_scroll_only=False,
					font='Courier 7',
					header_font='Courier 9')

	
	###########################################################################
	# Settings objects
	settingsObjs=	[		sg.Button(button_text="Load", size=(8,1), font='Courier 8', key="LOAD"), 		\
							sg.Button(button_text="Save", size=(8,1), font='Courier 8', key="SAVE"), 		\
							sg.Button(button_text="Default", size=(8,1), font='Courier 8',key="DEFAULT")	\
					]
	settingFrame=sg.Frame(title="Map Filters", title_location="n", element_justification="center", relief="groove", font='Courier 10', pad=(0,0,0,4), layout=[settingsObjs]) 

	###########################################################################
	# Filter Selected
	includeBtn=sg.Button(button_text="Include", size=(7,1), font='Courier 8', key='INCLUDE_SELECTED')
	excludeBtn=sg.Button(button_text="Exclude", size=(7,1), font='Courier 8', key='EXCLUDE_SELECTED')		
	seletedFilterObjs=[includeBtn, excludeBtn]
	filterFrameSelected=sg.Frame(title="Selected Maps", title_location="n", element_justification="center", relief="groove", font='Courier 10', pad=(1,0,0,4), layout=[seletedFilterObjs]) 
	
	###########################################################################
	# Author Filter
	authorList=list(set( maps["AUTHOR"])) 	# Get unique lists of Authors
	authorList.sort(key=str.casefold)	 	# Put authors in ABC order
	authorListCombobox=sg.Combo(authorList, readonly=True, visible=True, size=(22,1), font='Courier 8', change_submits=True, default_value=authorList[0], key="AUTHOR_SELECTED")
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
	filterFrameRating=sg.Frame(title="Minimum Star Rating", title_location="n", element_justification="center", relief="groove", font='Courier 10', pad=(1,0,0,4), layout=[ratingObjs]) 
	
	###########################################################################	
	# Filters Layout
	filterFrameObjs=[settingFrame, filterFrameSelected, filterFrameAuthor, filterFrameRating]
	filterFrame=sg.Frame(title="Exclude Installing Maps By", title_location="n", relief="groove", pad=(1,1,0,4),layout=[filterFrameObjs]) 

	###########################################################################
	# Summary
	summaryLine=sg.Text("",size=(80,2), key='SUMMARY_LINE')	
	installLog=sg.MLine(default_text='', size=(120, 10), font='monospace 8', key='INSTALL_LOG')
	installLogObjs=[[installLog], [summaryLine]]
	installLogFrame=sg.Frame(title="Install Log", title_location="n", element_justification="center", relief="groove", layout=installLogObjs) 
	
	###########################################################################
	# Bottom Buttons
	startDownloadBtn=sg.Button(button_text="Download", key='DOWNLOAD')
	
	
	SchedList=["Use Current Filters", "Only Update Existing Maps", "Update Existing & Download New Releases"]
	SchedListCombobox=sg.Combo(SchedList, readonly=True, visible=True, size=(30,1), default_value=SchedList[0], font='Courier 10')
	taskSchedBtn=sg.Button(button_text="Schedule", key='Add to Scheduler')
	schedObjs=[[SchedListCombobox, taskSchedBtn]]
	taskSchedFrame=sg.Frame(title="Automaticall run daily via Windows Task Scheduler", title_location="n", element_justification="center", relief="groove", layout=schedObjs) 
		
	###########################################################################
	# Layout of GUI
	layout = [ [filterFrame], [table], [installLogFrame], [startDownloadBtn, taskSchedFrame]	 ]

	# ------ Create Window ------
	sg.change_look_and_feel('GreenTan')
	window = sg.Window('Onward Custom Map Installer', layout, font='Courier 12', size=(800,650) )

	# Finalize the layout and then update populate the table / status lines otherwise won't update until user does something to trigger the event loop
	window.Finalize()	
	updateMapData(window, summaryData)
	
	global globalWindow
	globalWindow=window
	###########################################################################
	# End GUI Objects
	###########################################################################	
	
	#from pprint import pprint
	#pprint(vars(table))

	# ------ Event Loop ------
	while True:
		event, values = window.read()
		if event == sg.WIN_CLOSED:
			break		
		elif event == "LOAD":
			loadSettings()
		elif event == "SAVE":
			saveSettings()
		elif event == "DEFAULT":
			createDefaultSettings()	
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
		
		elif event == "DOWNLOAD":
			window.Disappear()
			startDownload(progressBarsGUI=True)
			#updateMapData(window, summaryData)
			window.Reappear()

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
	
	l=len(maps["MAP NAME"])	
	for i in range(0,l):
		tableData.append([maps["MAP NAME"][i], maps["AUTHOR"][i], maps["MISC FIELDS"][i],  maps["FILE SIZE"][i] + "mb", maps["RATING"][i], maps["RELEASE DATE"][i], maps["UPDATE DATE"][i]])
		

	summaryText="Total To Download:%d\tAlready Installed:%d\tTotal Maps: %d\nBy Rating:%d\tBy Author:%d\tBy Name:%d\tTotal Exlcuded:%d" \
		% (	summaryData["totalToInstall"], summaryData["totalAlreadyInstalled"], summaryData["totalMaps"],  \
			summaryData["totalSkippedRating"], summaryData["totalSkippedAuthor"], summaryData["totalSkippedName"] ,summaryData["totalExcluded"] )
	
	table.Update(values=tableData)
	summaryLine.Update(value=summaryText)

	# Update the button text on the Author Remove to reflect the current seletion
	author=str(window["AUTHOR_SELECTED"].Get())
	if processXMLFilter("EXISTS", "Exlude_Map_Author", author) == True:
		window["AUTHOR"].update(text="INCLUDE")	
	else:
		window["AUTHOR"].update(text="EXCLUDE")		


###############################################################################
# Traverse the list of maps and keep track of which maps to download or skip
###############################################################################
def processFilters():
	summaryData={}
	summaryData.update({	"totalToInstall":0, 	"totalAlreadyInstalled":0, 																\
							"totalSkippedRating":0, "totalSkippedAuthor":0, 	"totalSkippedName":0, 	"totalSkippedNotNewRlease":0,		\
							"totalExcluded":0, 		"totalMapsFailed":0, 		"totalMaps":0 })
	
	ratingFilter=getXMLRatingFilter()

	l=len(maps["MAP NAME"])
	summaryData["totalMaps"]=l
	
	for i in range(0,l):
		status=""
		
		needStatus=needMap(maps["ID"][i], maps["INFO HASH"][i])
		filterStatus=filterMap(maps["ID"][i], maps["MAP NAME"][i], maps["AUTHOR"][i], maps["RATING"][i], maps["RELEASE DATE"][i])
		# If a map is already installed flag to skip it
		if needStatus == "INSTALLED":
			summaryData["totalAlreadyInstalled"]=summaryData["totalAlreadyInstalled"]+1
			status=needStatus
		# If we use the -justUpdate flag and an update is available download it regardless of any filters.
		# Otherwise only download if we need it and there are no filters.
		elif (needStatus == "UPDATE" and args.justUpdate is True) or (needStatus in ["UPDATE", "REINSTALL", "DOWNLOAD"] and filterStatus == "" and args.justUpdate is False):
			summaryData["totalToInstall"]=summaryData["totalToInstall"]+1	
			status=needStatus
		else:
			status=filterStatus 
			if status.find("RATING") != -1:
				summaryData["totalSkippedRating"]=summaryData["totalSkippedRating"]+1
			elif status.find("AUTHOR") != -1:
				summaryData["totalSkippedAuthor"]=summaryData["totalSkippedAuthor"]+1
			elif status.find("MAP NAME") != -1:
				summaryData["totalSkippedName"]=summaryData["totalSkippedName"]+1
			elif status.find("NOT A NEW RELEASE") != -1:
				summaryData["totalSkippedNotNewRlease"]=summaryData["totalSkippedNotNewRlease"]+1
			summaryData["totalExcluded"]=summaryData["totalExcluded"]+1			
		
		# Special case where we don't have a map installed but rating is -1 meaning author doesn't want distribution
		if status==needStatus and filterStatus.find("UNAVAILBLE") != -1:
			status=filterStatus
			summaryData["totalToInstall"]=summaryData["totalToInstall"]-1
			summaryData["totalSkippedName"]=summaryData["totalSkippedName"]+1
		
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
			#ctypes.windll.user32.ShowWindow(whnd, 0)
		# if you wanted to close the handles...
		#ctypes.windll.kernel32.CloseHandle(whnd)			
			pass
			
	if args.scheduleDaily is not None:
		#createTask(args.scheduleDaily)
		exit()
	
	loadSettings()
	
	# Make sure the Onward folder exists
	if os.path.isdir(onwardPath) is False:
		reportMessage("***ERROR*** Can't find ONWARD folder in '%s'" % onwardPath)
		exit()

	
	# Download the custom maps list from Google Drive
	reportMessage("***INFO*** Obtaining the complete custom maps list from server.")	
	try:
		downloadGoogleDriveFile(filenameMapList, mapListGoogleURL, 0, quiet=True)
	except AssertionError as error:
		reportMessage("\n***ERROR*** Unable to obtain the list of custom maps... Please try again later.\n")	
		exit()

	reportMessage("***INFO*** List downloaded sucessfully...\n\n")


	# Read the maps list from the file into a Dictionary
	f = open(filenameMapList)
	reader = csv.DictReader(f)
	maps = {}
	for row in reader:
		for column, value in row.items():
			maps.setdefault(column.upper(), []).append(value)
	f.close()
		
	# Make sure the map list we download contains valid data	
	# TODO: Make this more inteligent.... Maybe just go 1 by 1 and verify each key matches
	validKeys = {"MAP NAME":1, "AUTHOR":2, "ID":3, "INFO HASH":4, "RELEASE DATE":5, "UPDATE DATE":6, "RATING":7, "FILE SIZE":8, "DOWNLOAD URL":9, "ZIP HASH":10, "MISC FIELDS":11}	
	if maps.keys() < validKeys.keys(): 
		print (maps.keys())
		reportMessage("\n***ERROR*** Map List Strucure does not match expected format... Check for an update to this app\n")	
		exit()
	
	# Make sure there is some data in the file
	l=len(maps["MAP NAME"])
	if l is None or l < 1:	
		reportMessage("\n***ERROR*** Map list downloaded but is empty... Try again later.\n")	
		exit()			
	
	# Verify the version of the map data works wiht this version of the application
	vPos=maps["MISC FIELDS"].index("VERSION")
	try:
		mapListVer=float(maps["MISC FIELDS"][vPos+1])
		if appVersion < mapListVer:
			reportMessage("***ERROR*** Your application version is out of date. Please update")
			exit()
	except:
		reportMessage("***ERROR*** Can't validate version of Maps List.")
		exit()


	# Display the GUI or if -noGUI specified just start downloading
	if args.noGUI is True:
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
		
	
	# If we downloaded anything this session update the last run date
	# global downloadedAnything
	if downloadedAnything is True:
		updateLastRunDate()

	# If the user happens to be running this from command prompt 
	if args.noGUI is False:
		if sys.platform.lower().startswith('win'):
			import ctypes
		whnd = ctypes.windll.kernel32.GetConsoleWindow()
		if whnd != 0:
			#ctypes.windll.user32.ShowWindow(whnd, 1)
			pass

	


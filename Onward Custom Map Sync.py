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

# GUI libs
import PySimpleGUI as sg


					
###############################################################################
# Global Variables
###############################################################################
appVersion = 1.00

settingsFile="Onward Custom Map Sync Settings.xml"
XMLSettings = None

filenameMapList = 'Map List.csv'
mapListGoogleURL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQ3uNvIexndfAxla3VACEpz6wCSLs8v8w1VzdmUPEw7SxuInqxbOEje_fUoxR5vmGnBZ9BRLloMJ0Xc/pub?gid=0&single=true&output=csv'
maps = {}	# Dictionary of map data download from Google Drive Spreadsheet

if "APPDATA" not in os.environ:
	reportMessage("***ERROR*** APPDATA environmental variable not set. Don't know how to find Onward Custom Maps folder")
	exit()
	
onwardPath = os.environ["APPDATA"] + "\..\LocalLow\Downpour Interactive\Onward\\"
mapFolder = "CustomContent\\"


		
###############################################################################
# Setup Command Line Arguments
###############################################################################
parser = argparse.ArgumentParser(description='Onward Custom Map Downloader version %s' %(appVersion))
parser.add_argument('-rating', type=int,
					help='Rating Filter: Only install maps that have this star rating or better')
parser.add_argument("-noGUI", help="Disable the GUI and run in console mode")        
parser.add_argument("-quiet", help="Disable all output and log to a text file instead")
parser.add_argument("-scheduleDaily", help="Add an entry to the Windows Task Scheduler to run daily at specified hh:mm in 24-hour clock / miltary time format") 


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
	print(message)

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
# Returnss 
#	"" if map isn't filterd otherwise returns the type of filter detected
#	as a string
###############################################################################
def filterMap(mapID, mapName, mapAuthor):
	authorFilter = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Exclude_Maps_Filters/Exlude_Map_Author')
	for i in range(0,len(authorFilter)):
		if authorFilter[i].text == mapAuthor:
			reportMessage("***SKIPPING MAP*** \"%s\" ID: %s by %s ---- Filtered by Author." %(mapName, mapID, mapAuthor))
			return "AUTHROR"
			
	IDFilter = XMLSettings.xpath('/Onward_Custom_Map_Sync_Settings/Exclude_Maps_Filters/Exlude_Map_ID')
	for i in range(0,len(IDFilter)):
		if IDFilter[i].text == mapID:
			reportMessage("***SKIPPING MAP*** \"%s\" ID: %s by %s ---- This map is marked not to install." %(mapName, mapID, mapAuthor))
			return "MAP NAME"
	
	return ""
	

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
def getMap(mapID, mapDownloadURL, zipHash, quiet=True):
	
	# Download the Google Drive file
	downloadName=onwardPath + mapID + ".zip"
	
	if "DRIVE.GOOGLE.COM" in mapDownloadURL.upper():
		if downloadGoogleDriveFile(downloadName, mapDownloadURL, quiet) == False:
			return False
	elif "KOIZ" in mapDownloadURL.upper():
		reportMessage("***INFO*** Koiz doesn't want his maps hosted here... Please ask him to reconsider")
		return False
	else:
		reportMessage("***ERROR*** Don't know how to download URL: %s" % mapDownloadURL)
		return False
		
	# validate hash
	calculatedZipHash = getHash(downloadName)
	if zipHash != calculatedZipHash:
		reportMessage("***ERROR***: Zip file hash incorrect. Expecting %s but got %s" % (zipHash, calculatedZipHash))
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
# Start Downloading Maps
###############################################################################
def startDownload():
	l=len(maps["MAP NAME"])
	
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
			reportMessage("***SKIPPING MAP*** \"%s\" ID: %s ---- Map is rated below threshold" %(maps["MAP NAME"][i].ljust(30), maps["ID"][i]))	
			continue	

		# Check for custom filters - Specific Map or Specific Author
		if filterMap(maps["ID"][i], maps["MAP NAME"][i], maps["AUTHOR"][i]) != "":
			totalMapsExcluded = totalMapsExcluded + 1
			continue				
			
		# Verify the map isn't already installed
		if needMap(maps["ID"][i], maps["INFO HASH"][i]) != "INSTALLED":
			reportMessage("***DOWNLOADING MAP*** \"%s\" by %s\tID: %s\tMap Star Rating: %s" %(maps["MAP NAME"][i].ljust(30), maps["AUTHOR"][i].ljust(15), maps["ID"][i],maps["RATING"][i]))
			if getMap(maps["ID"][i], maps["DOWNLOAD URL"][i], maps["ZIP HASH"][i], quiet=False) is True:
				totalMapsInstalled = totalMapsInstalled + 1
				reportMessage("\n***INSTALLED***       \"%s\" by %s\tID:%s\tMap Star Rating: %s\n" %(maps["MAP NAME"][i].ljust(30), maps["AUTHOR"][i].ljust(15), maps["ID"][i], maps["RATING"][i]))
			else:
				totalMapsFailed = totalMapsFailed + 1
				reportMessage("\n***ERROR*** Map    \"%s\" ID:%s did not have the expected hash value... This map will not be installed" %(maps["MAP NAME"][i], maps["ID"][i]))	
		else:
			totalMapsAlreadyInstalled = totalMapsAlreadyInstalled + 1
			reportMessage("***SKIPPING MAP***    \"%s\" by %s\tID: %s \tAlready installed." %(maps["MAP NAME"][i].ljust(30), maps["AUTHOR"][i].ljust(15), maps["ID"][i]))

	reportMessage("\n\n***INFO*** Maps Installed: %s\tAlready Installed: %s\tSkipped-Low Rating: %s\tSkipped-Custom Filter: %s\tInstall Failed: %s\tTotal Maps: %s" % (totalMapsInstalled, totalMapsAlreadyInstalled,totalMapsSkippedRating, totalMapsExcluded, totalMapsFailed, l))
	os.system("pause")


###############################################################################
# Setup the GUI
###############################################################################
def displayGUI():
	l=len(maps["MAP NAME"])
	
	totalMapsInstalled=0
	totalMapsAlreadyInstalled=0	
	totalMapsSkippedRating=0
	totalMapsExcluded=0
	totalMapsFailed=0



	
	#Setup the map list table
	rows, cols = (l, 6) 
	tableData = [[""]*cols]*rows 
	# ------ Make the Table Data ------
	headings=["Map Name", "Author", "Stars", "Published", "Updated", "Status"]
	
	for i in range(0,l):
		status=filterMap(maps["ID"][i], maps["MAP NAME"][i], maps["AUTHOR"][i])
		if status != "":
			status="IGNORE:" + status
		elif int(maps["RATING"][i]) < ratingFilter:
			status="IGNORE:RATING"
		else:
			status=needMap(maps["ID"][i], maps["INFO HASH"][i])
		tableData[i]=[maps["MAP NAME"][i], maps["AUTHOR"][i], maps["RATING"][i], maps["RELEASE DATE"][i], maps["UPDATE DATE"][i], status]


	# Create table object
	table=sg.Table(values=tableData[1:][:], headings=headings, max_col_width=55,
					auto_size_columns=False,
					display_row_numbers=False,
					col_widths=[25,20,8,12,12,20],
					justification='center',
					num_rows=20,
					key='-TABLE-',
					vertical_scroll_only=False,
					font='Courier 10',
					header_font='Courier 13',
					tooltip='This is a table')

	#from pprint import pprint
	#pprint(vars(table))

	
	# ------ Window Layout ------
	settingsObjs=[sg.Button(button_text="Load", key='Load'), sg.Button(button_text="Save", key='Save'), sg.Button(button_text="Default", key='Default')]
	settingFrame=sg.Frame(title="Settings", title_location="n", element_justification="center", relief="groove", layout=[settingsObjs]) 

	# Setup Author Filte
	authorList=list(set( maps["AUTHOR"])) # Get unique lists of Authors
	authorListCombobox=sg.Combo(authorList, readonly=True, visible=True, default_value=authorList[0])
	authorBtn=sg.Button(button_text="Apply", key='Author')	
	authorObjs=[authorListCombobox, authorBtn]
	filterFrameAuthor=sg.Frame(title="Author", title_location="n", element_justification="center", relief="groove", layout=[authorObjs]) 
	
	#Setup Rating Filter
	ratingList=["All", "5 Star", "4 Star", "3 Star", "2 Star", "1 Star"]
	ratingListCombobox=sg.Combo(ratingList, readonly=True, visible=True, default_value="All")
	ratingBtn=sg.Button(button_text="Apply", key='Rating')		
	ratingObjs=[ratingListCombobox, ratingBtn]
	filterFrameRating=sg.Frame(title="Minimum Star Rating", title_location="n", element_justification="center", relief="groove", layout=[ratingObjs]) 
	
	filterFrameObjs=[filterFrameAuthor, filterFrameRating]
	filterFrame=sg.Frame(title="Exclude Maps By", title_location="n", relief="groove", layout=[filterFrameObjs]) 

	# Layout of GUI
	layout = [ [settingFrame, filterFrame],
			[table]
		]


	# ------ Create Window ------
	sg.change_look_and_feel('GreenTan')
	window = sg.Window('Onward Custom Map Installer', layout, font='Courier 12', size=(800,600) )

	
	# ------ Event Loop ------
	while True:
		event, values = window.read()
		print(event, values)	
		if event == sg.WIN_CLOSED:
			break		
		elif event == "Load":
			loadSettings()
		elif event == "Save":
			saveSettings()
		elif event == "Default":
			createDefaultSettings()		
		pass

	window.close()
				   				
###############################################################################
# Obtain the custom map list from Google Doc and install missing maps
###############################################################################
if __name__ == "__main__":
	args = parser.parse_args()
	
	if args.scheduleDaily is not None:
		#createTask(args.scheduleDaily)
		exit()
	
	loadSettings()
	
	# Make sure the Onward folder exists
	if os.path.isdir(onwardPath) is False:
		reportMessage("***ERROR*** Can't find ONWARD folder in '%s'" % onwardPath)
		exit()
		
	
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
	reportMessage("***INFO*** Obtaining the complete custom maps list from server.")	
	try:
		downloadGoogleDriveFile(filenameMapList, mapListGoogleURL, quiet=True)
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
	validKeys = {"MAP NAME":1, "AUTHOR":2, "ID":3, "INFO HASH":4, "RELEASE DATE":5, "UPDATE DATE":6, "RATING":7, "DOWNLOAD URL":8, "ZIP HASH":9, "MISC FIELDS":10}	
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
	if args.noGUI is not None:
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



	


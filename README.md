# Onward Custom Map Sync
Onward recently added the ability to play custom maps. However, in order to support non Steam players they were forced to impliment their own workshop system. This means there is a lot of core functionality that is simply going to take time to roll out as Downpour Interactice is a very small team. Hopefully this tool makes it eaier for players to get custom content until the developers have time to focus on the missing features.

## How to use this tool:

To get everything just **Start Download** button in the lower left corner. You can also have this tool run daily by clicking the **Schedule Task** button in the lower right corner. This just automates creating an entry into the [Windows Task Scheduler](https://www.windowscentral.com/how-create-automated-task-using-task-scheduler-windows-10). If there are maps you don't want to download see the Filters section below.

![Screenshot](https://user-images.githubusercontent.com/5240185/85643374-86e94300-b659-11ea-8346-cb52f6432f9f.jpg)

## Quick Filters:
* **Use Current Filters** Use whatever settings are stored in **Onward Custom Map Sync Settings.xml**
* **Only Update Existing Maps** Only download maps you already have installed that have updates available
* **Update Existing & Download New Releases** Only download updates and new maps released after the last time you ran this program

## Filters:
* **Selected Maps** Ignore installing individial maps. Any maps you have selected in the table below (shift click to select multiple or ctrl click to include/exclude just one) and click **include** or **exclude** to add or remove the filter.
* **Author** Ignore dowload current and future maps for specific authors.
* **Rating** Only install maps that are at least your selected star rating.

Any filters you apply are temporary unless you click **Save**.

All filters can be adjusted manually via your favorite text editor by modifying the **Onward Custom Map Sync Settings.xml**

- <Exclude_Maps_Filters>
- -	<Exlude_Map_ID>3351ae75-a8e3-48b0-9451-d136a08ad114</Exlude_Map_ID>
- -	<Exlude_Map_ID>cfcb28ad-7083-4956-9eb6-5e6311c22393</Exlude_Map_ID>
- -	<Exlude_Map_Author>koiz</Exlude_Map_Author>
- -	<Ratings_Filter>4</Ratings_Filter>
- </Exclude_Maps_Filters>

**NOTE**If you don't know what the ID to use with <Exclude_Map_ID> you can look them up [here](https://docs.google.com/spreadsheets/d/e/2PACX-1vQ3uNvIexndfAxla3VACEpz6wCSLs8v8w1VzdmUPEw7SxuInqxbOEje_fUoxR5vmGnBZ9BRLloMJ0Xc/pubhtml?gid=0&single=true) or you can open **Map List.csv** while the program is running.

## Command Line Arguments
* **-rating <int>** Specify your rating threshold
* **-noGUI** Disables GUI interface and automatically starts downloading (using XML setting file filters) when you run the app
* **-justUpdate** Only downloads updates for maps you already have installed
* **-justNew** Only downloads new maps that were released after the last time the app was run (last run date stored in XML settings file)

## How this tool works:
Unfortunately Downpour Interactive doesn't allow their workshop data to be accessible outside of Onward so I personally have to download all the maps and make them publically available via my personal Google Drive. This means I have to keep up with Onward custom map releases for this tool to function. So if you notice Onward is reporting there are updates/new maps but this tool doesn't please let me know (Wescott on the Onward Discord) so I can fix the issue.

This tool pulls data from [this Google Spreadhsheet](https://docs.google.com/spreadsheets/d/e/2PACX-1vQ3uNvIexndfAxla3VACEpz6wCSLs8v8w1VzdmUPEw7SxuInqxbOEje_fUoxR5vmGnBZ9BRLloMJ0Xc/pubhtml?gid=0&single=true) (which I manually update) in order to know how to identify if a map is current or not. I record the m5sum of each map's .info file and use this as a basis to determine if you have the current version or not. If your .info doesn't match my list (or you don't have the .info file at all) it flags that map to be installed. When you look at the spreadsheet you will see there is a Google Drive link for each map so you can download them directly that way instead of using the tool if you want.

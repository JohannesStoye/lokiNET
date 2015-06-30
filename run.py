#!/usr/bin/python

########################################################################
# Copyright 2015 Daniel Haake
#
# This file is part of lokiNET
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
########################################################################

from engineClasses.tools import tools
import getpass
import os
import sys
import signal
import time
import sqlite3
import urllib2
import MySQLdb


myTool = tools()
usageString = "Usage: " + sys.argv[0] + myTool.blue  + " <interface> <options>" + myTool.stop
invalidString = myTool.fail + "[-]" + myTool.stop + " Invalid parameter combination!"
offlineOrOnline = "offline"
gpsOrStreet = "address"
currentTimestamp = time.time()
dataFile = "Data.db"
privacy = 0
silentArray = []
silent = 0
path = os.path.split(os.path.realpath(__file__))[0]
silentString = 0
remoteOrLocal = "l"
server = ""
por = 3306
username = ""
password = ""
database = ""


def dbSelectCommit(statement):
        connectionCursor.execute(statement)
        return connectionCursor.fetchall()

def dbChangeCommit(statement):
        connectionCursor.execute(statement)
        connection.commit()

def createDatabaseFile(sig):
	# check if copy file already exists
	if os.path.isfile(path + "/data/" +  sig + dataFile):
		pass
	else:
		os.system("cp " + path + "/data/dataTemplate.db " + path + "/data/" + sig + dataFile)

def ctrlc_handler(self, frm):
        if "-m" in sys.argv or "--monitor" in sys.argv:
                print myTool.green + "[+] " + myTool.stop + "Monitor mode removed"
                os.system("ifconfig " + interface + " down")
                os.system("iwconfig " + interface + " mode managed")
                os.system("ifconfig " + interface + " up")
        print myTool.green + "\n\n[+] " + myTool.stop + "Good bye!"
        print "*** Remember: \"A hacker should only be limited by his imagination and not by his tools.\"\n"
        sys.exit(0)

if len(sys.argv) < 2:
        sys.exit(usageString + "\n-h: help menu")
else:
	signal.signal(signal.SIGINT, ctrlc_handler)
	interface = sys.argv[1]

	# help menu
        if "-h" in sys.argv or "--help" in sys.argv:
		print usageString
		print "scanengine:" + myTool.blue + "\t[-addr|--address]" + myTool.stop + "\t" + myTool.green + "[default] " + myTool.stop + "Use direct address input for location (excludes GPS input)"
		print myTool.blue + "\t\t[-gps|--gps]" + myTool.stop + "\t\tUse direct GPS input for location (excludes address input)"
		print myTool.blue + "\t\t[-off|--offline]" + myTool.stop + "\t" + myTool.green + "[default]" + myTool.stop + "Uses offline mode (excludes online mode)"
		print myTool.blue + "\t\t[-on|--online]" + myTool.stop + "\t\tUse online mode (excludes offline mode)"

		print "webinterface:" +  myTool.blue + "\t[-web|--webinterface]" + myTool.stop + "\tStart webserver to analyse collected data"

		print "Database:" +  myTool.blue + "\t[-me|--merge]" + myTool.stop + "\t\tMerge different database files to one"		
		print myTool.blue + "\t\t[-ct|--createTables]" + myTool.stop + "\tCreate database tables for a remote MySQL server"

		print "Silent Mode:" + myTool.blue + "\t[-pc|--print-crontab]" + myTool.stop + "\tJust creates a silent mode string. You can use it for adding the program to your cronjobs."		
		print myTool.blue + "\t\t[-s|--silent]" + myTool.stop + "\t\tEnable silent mode. In silent mode no console output will be generated.\n\t\t\t\t\tTo make sure the script works fine you need to put the silent flag at the end of the parameters followed by all needed input."		

		print "others:" + myTool.blue + "\t\t[-h|--help]" + myTool.stop + "\t\tPrints this help menu"
		print myTool.blue + "\t\t[-m|--monitor]" + myTool.stop + "\t\tChange mode of selected interface to \"monitor\""
		print myTool.blue + "\t\t[-p|--privacy]" + myTool.stop + "\t\tIf you set this parameter all collected personal data will be scrambled."
		print ""
		sys.exit()

	# create mysql database tables for a remote database
	if "-ct" in sys.argv or "--createTables" in sys.argv:
		print myTool.green + "[+] " + myTool.stop + "Create MySQL tables on a remote server selected."
		print "[?] Type in the server parameters."
		server = raw_input("# Server address: ")
                por = int(raw_input("# Port number: "))
                database = raw_input("# Database: ")
                username = raw_input("# Username: ")
                password = getpass.getpass()
		
		# create tables
		connection = MySQLdb.connect(host=server, user=username, passwd=password, db=database, port=por)
                connectionCursor = connection.cursor()		
		try:
			connectionCursor.execute("create table accesspoints (ID int not null auto_increment, bssid varchar(50) not null, essid text not null, channel int not null, power int not null, locationId int not null, encryption text, time text, primary key (ID))")
			print myTool.green + "[+] " + myTool.stop + "Table accesspoints created."
		except:
			print myTool.fail + "[-] " + myTool.stop + "ERROR creating table for access points."
		try:
			connectionCursor.execute("create table clientProbes (ID int not null auto_increment, clientMac varchar(8) not null, probe text not null, locationId int not null, power int, timeFirst text not null, timeLast text not null, primary key(ID))")
			print myTool.green + "[+] " + myTool.stop + "Table clientProbes created."
		except:
			print myTool.fail + "[-] " + myTool.stop + "ERROR creating table for client probes."
		try:
			connectionCursor.execute("create table connections (ID int auto_increment, macOne varchar(8) not null, macTwo varchar(8) not null, power int not null, locationID int not null, timeFirst text not null, timeLast text not null, primary key(ID))")
			print myTool.green + "[+] " + myTool.stop + "Table connections created."
		except:
			print myTool.fail + "[-] " + myTool.stop + "ERROR creating table for connections."
		try:
			connectionCursor.execute("create table locations (ID int auto_increment, country text not null, zipcode text not null, city text not null, street text not null, streetnumber text not null, gpsl text, gpsw text, time text not null, primary key(ID))")
			print myTool.green + "[+] " + myTool.stop + "Table locations created."
		except:
			print myTool.fail + "[-] " + myTool.stop + "ERROR creating table for locations."
		connectionCursor.close()

		print myTool.green + "[+] " + myTool.stop + "Finished."
		sys.exit()

	# print silent string
	if "-pc" in sys.argv or "--print-crontab" in sys.argv:
		silentString = 1
		if silent == 0:
			print myTool.green + "[+] " + myTool.stop + "Only generate a silent string for your crontab."		

	# silent mode configuration
	if "-s" in sys.argv or "--silent" in sys.argv:
		position = 0
		c = 0
		silent = 1
		for element in sys.argv:
			if element == "-s" or element == "--silent":
				position = c
			c += 1
		for i in range(position + 1, len(sys.argv)):
			silentArray.append(sys.argv[i])

	# enable privacy
	if "-p" in sys.argv or "--privacy" in sys.argv:
		privacy = 1
		if silent == 0:
			print myTool.green + "[+] " + myTool.stop + "Privacy activated."

	# start monitor mode if desired
        if "-m" in sys.argv or "--monitor" in sys.argv:
                os.system("ifconfig " + interface + " down")
                os.system("iwconfig " + interface + " mode monitor")
                os.system("ifconfig " + interface + " up")
		if silent == 0:
			print myTool.green + "[+] " + myTool.stop + "Monitor interface started."

	# start the merge script
	if "-me" in sys.argv or "--merge" in sys.argv:
		print myTool.warning + "[!] " + myTool.stop + "IMPORTANT: Before you start, take care that all files you want to merge are located inside the data/merge directory."
		files = os.listdir(path + "/data/merge/")
		fileString = ""
		for f in files:
			fileString += f + " "
		if fileString != "":
			print myTool.warning + "[!] " + myTool.stop + "Merging the following files: " + fileString
			cont = raw_input("# Continue? (yes: y, no: n) ")
			if cont == "y":
				print myTool.green + "[+] " + myTool.stop + "Calling merge.py..."
				os.system("./merge.py " + fileString)
				print myTool.green + "[+] " + myTool.stop + "Merging completed."
			else:
				print myTool.warning + "[!] " + myTool.stop + "Abort."
		else:
			print myTool.fail + "[-] " + myTool.stop + "No files to merge! data/merge is empty."
		sys.exit()

	# start evaluation webinterface
        if "-web" in sys.argv or "--webinterface" in sys.argv:
		try:			
			print myTool.green + "[+] " + myTool.stop + "Starting webinterface for database analysis. You should point your browser to:"
			print myTool.green + "[+]" + myTool.stop + " http://127.0.0.1:8000/cgi-bin/index.html"
			os.system("python -m CGIHTTPServer")
			sys.exit()
		except:
			print myTool.fail + "[-] " + myTool.stop + "Webserver could not be started!"
			sys.exit()

	# use offline mode
        if "-off" in sys.argv or "--offline" in sys.argv:
                # check for invalid option
                if "-on" in sys.argv or "--online" in sys.argv:
                        sys.exit(invalidString)
                else:
			if silent == 0:
				print myTool.green + "[+]" + myTool.stop + " Offline mode selected."
                        offlineOrOnline = "offline"

        # use online mode
        if "-on" in sys.argv or "--online" in sys.argv:
                # check for invalid option
                if "-off" in sys.argv or "--offline" in sys.argv:
                        sys.exit(invalidString)
                else:
			if silent == 0:
				print myTool.green + "[+]" + myTool.stop + " Online mode selected."
				# check if a remote database or local should be used
				remoteOrLocal = raw_input("# Use (r)emote or (l)ocal databse?: ")
				if remoteOrLocal == "r":
					print myTool.green + "[+]" + myTool.stop + " Remote database selected."
					print "[?] MySQL connection properties:"
					server = raw_input("# Server address: ")
					por = int(raw_input("# Port number: "))
					database = raw_input("# Database: ")
					username = raw_input("# Username: ")
					password = getpass.getpass()
				else:
					print myTool.green + "[+]" + myTool.stop + " Local database selected."

			offlineOrOnline = "online"

	# direct gps input
        if "-gps" in sys.argv or "--gps" in sys.argv:
                # check for invalid option
                if "-addr" in sys.argv or "--address" in sys.argv:
                        sys.exit(invalidString)
                else:
			if silent == 0:
				print myTool.green + "[+]" + myTool.stop + " GPS mode selected."
                        gpsOrStreet = "gps"

        # address input (convert to to gps later)
        if "-addr" in sys.argv or "--address" in sys.argv:
                # check for invalid option
                if "-gps" in sys.argv or "--gps" in sys.argv:
                        sys.exit(invalidString)
                else:
			if silent == 0:
				print myTool.green + "[+]" + myTool.stop + " Address mode selected."
                        gpsOrStreet = "address"

	# start session
	if gpsOrStreet == "address":
		if len(silentArray) == 0:
			print myTool.green + "\n[+++] " + myTool.stop + "Scanengine Selected" + myTool.green + " [+++]" + myTool.stop
			print "[?] Type in your current location:"
			country = raw_input("# Country: ")
			zipcode = raw_input("# Zipcode: ")
			city = raw_input("# City: ")
			street = raw_input("# Street: ")
			streetnumber = raw_input("# Streetnumber: ")
			print "[?] Type in the session id:"
			signature = raw_input("# Session value: ")
		else:
			country = silentArray[0]
			zipcode = silentArray[1]
			city = silentArray[2]
			street = silentArray[3]
			streetnumber = silentArray[4]
			signature = silentArray[5]
			if silentArray[6] == "r":
				remoteOrLocal = "r"
				server = silentArray[7]
				username = silentArray[8]
				password = silentArray[9]
				database = silentArray[10]
				por = int(silentArray[11])
		
		if silentString == 1:
			mon = " "
			priv = " "
			offOn = " "
			if "-m" in sys.argv or "--monitor" in sys.argv:
				mon = " -m "
			if "-p" in sys.argv or "--privacy" in sys.argv:
				priv = " -p "
			if offlineOrOnline != "offline":
				offOn = " -on "
			print "\n" + myTool.green + "[+] Crontab String: " + myTool.stop + "@reboot python " + path + "/run.py " + interface + mon + offOn + priv + "-s " + country + " " + zipcode + " " + city + " " + street + " " + streetnumber + " " + signature + " " + remoteOrLocal + " " + server + " " + username + " " + password + " " + database + " " + str(por)
			print myTool.green + "[+]" + myTool.stop + " This string can be added to your devices crontab (crontab -e) to run it automatically on startup."
			sys.exit(0)
		
		createDatabaseFile(signature)
		
		# save new location to database
		if remoteOrLocal == "l":
			connection = sqlite3.connect(path + "/data/" + signature + "Data.db")
		else:
                        connection = MySQLdb.connect(host=server, user=username, passwd=password, db=database, port=por)
		connectionCursor = connection.cursor()

		# test if location is already in database
		inDB = dbSelectCommit("select ID from locations where country=\"" + country + "\" and zipcode=\"" + zipcode + "\" and city=\"" + city + "\" and street=\"" + street + "\" and streetnumber=\"" + streetnumber + "\"")

		if len(inDB) == 0:
			if offlineOrOnline == "offline":
				dbChangeCommit("insert into locations (country, zipcode, city, street, streetnumber, gpsl, gpsw, time) values (\"" + country + "\", \"" + zipcode + "\", \"" + city + "\", \"" + street + "\", \"" + streetnumber + "\", \"0\", \"0\", \"" + str(currentTimestamp) + "\")")
			else:
				# resolve gps coordinates from address
				url = "http://maps.googleapis.com/maps/api/geocode/xml?address=" + urllib2.quote(country) + ",+" + urllib2.quote(zipcode) + ",+" + urllib2.quote(city) + ",+" + urllib2.quote(street) + ",+" + urllib2.quote(streetnumber) + "&sensor=false"
				# extract GPS coordinates
				res = myTool.streetToGps(url)
				dbChangeCommit("insert into locations (country, zipcode, city, street, streetnumber, gpsl, gpsw, time) values (\"" + country + "\", \"" + zipcode + "\", \"" + city + "\", \"" + street + "\", \"" + streetnumber + "\", \"" + res[1] + "\", \"" + res[0] + "\", \"" + str(currentTimestamp) + "\")")
				if len(silentArray) == 0:
					print myTool.green + "[+] " + myTool.stop + "Resolving GPS coordinates... (needs internet connection!)"
					
			maxLocationId = dbSelectCommit("SELECT ID FROM locations ORDER BY ID DESC LIMIT 1")[0][0]
		else:
			maxLocationId = inDB[0][0]
			if len(silentArray) == 0:
				print myTool.warning + "[!] " + myTool.stop + "Location already exists in database. Using saved entry instead of saving a new one."
		
		# execute scan script
		os.system(path + "/scan.py " + interface + " " + signature + " " + str(maxLocationId) + " " + str(privacy) + " " + str(silent) + " " + remoteOrLocal + " " + server + " " + username + " " + password + " " + database + " " + str(por))
	else:
		# direct GPS input
		if silent == 0:
			print myTool.green + "\n[+++] " + myTool.stop + "Scanengine Selected" + myTool.green + " [+++]" + myTool.stop
			print "[?] Type in your current location:"
			gpsl = raw_input("# Longitude: ")
			gpsw = raw_input("# Latitude: ")
			print "[?] Type in the session id:"
			signature = raw_input("# Session value: ")
		else:
			gpsl = silentArray[0]
			gpsw = silentArray[1]
			signature = silentArray[2]
			if silentArray[3] == "r":
				remoteOrLocal = "r"
                        	server = silentArray[4]
                                username = silentArray[5]
                                password = silentArray[6]
				database = silentArray[7]
				por = int(silentArray[8])

		
		if silentString == 1:
			mon = " "
			priv = " "
			offOn = " "
			if "-m" in sys.argv or "--monitor" in sys.argv:
				mon = " -m "
			if "-p" in sys.argv or "--privacy" in sys.argv:
				priv = " -p "	
			if offlineOrOnline != "offline":
				offOn = " -on "			
			print "\n" + myTool.green + "[+] Crontab String: " + myTool.stop + "@reboot python " + path + "/run.py " + interface + mon + offOn + priv + "-gps -s " + gpsl + " " + gpsw + " " + signature + " " + remoteOrLocal + " " + server + " " + username + " " + password + " " + database + " " + str(por)
			print myTool.green + "[+]" + myTool.stop + " This string can be added to your devices crontab (crontab -e) to run it automatically on startup."
			sys.exit(0)		
		
		createDatabaseFile(signature)
		if remoteOrLocal == "l":
			connection = sqlite3.connect(path + "/data/" + signature + "Data.db")
		else:
		 	connection = MySQLdb.connect(host=server, user=username, passwd=password, db=database, port=por)
		connectionCursor = connection.cursor()		
		
		# test if location is already in database
		inDB = dbSelectCommit("select ID from locations where gpsl=\"" + gpsl + "\" and gpsw=\"" + gpsw + "\"")
		
		if len(inDB) == 0:
			# save new location to database
			dbChangeCommit("insert into locations (country, zipcode, city, street, streetnumber, gpsl, gpsw, time) values (\"No entry.\", \"No entry.\", \"No entry.\", \"No entry.\", \"No entry.\", \"" + gpsl + "\", \"" + gpsw + "\", \"" + str(currentTimestamp) + "\")")
		
			maxLocationId = dbSelectCommit("SELECT ID FROM locations ORDER BY ID DESC LIMIT 1")[0][0]
		else:
			maxLocationId = inDB[0][0]
			if silent == 0:
				print myTool.warning + "[!] " + myTool.stop + "Location already exists in database. Using saved entry instead of saving a new one."
		
		# execute scan script
		os.system(path + "/scan.py " + interface + " " + signature + " " + str(maxLocationId) + " " + str(privacy) + " " + str(silent) + " " + remoteOrLocal + " " + server + " " + username + " " + password + " " + database + " " + str(por))

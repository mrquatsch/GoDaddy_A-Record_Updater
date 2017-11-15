#!/usr/local/bin/python
#############################################
# Import the necessary modules
#############################################
import time
import requests
import getopt
import sys
import json
import godaddyproperties
import logging
import logging.handlers
import datetime
import os
from cgi import escape
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

def main():
	global version

	os.environ['TZ'] = 'America/Chicago'
	time.tzset()

	version = '1.0'

	loadProperties()

	logger.info("Executing for domain name: " + domainName)

	initializeBrowser()

	publicIP = getPublicIP()
	logger.info("Current public IP: " + str(publicIP))

	login(loginURL, username, password)

	goDaddyPublicIP = getDNSRecord()
	logger.info("GoDaddy " + domainName + " domain a-record set to " + str(goDaddyPublicIP))

	if publicIP == goDaddyPublicIP:
		logger.info("GoDaddy is configured with our current public IP. Will not update a-record.")
	else:
		logger.info("GoDaddy is not configured with our current public IP. Updating now...")
		updateARecord(publicIP, goDaddyPublicIP)

	exitScript(0)

def initializeBrowser():
	global browser
	global wait

	try:
		pageTimeout = 30
		browser = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true', '--ssl-protocol=any'],service_log_path='logs/ghostdriver.log')
		wait = webdriver.support.ui.WebDriverWait(browser, pageTimeout)
	except:
		logger.info("Failed to initialize browser")
		exitScript(0)

def loadProperties():
	global loginURL
	global username
	global password
	global domainName
	global dnsManagementURL
	global publicIPAPI
	global logger

	logDirectory = ''
	username = ''
	password = ''
	domainName = ''
	loginURL = ''
	dnsManagementURL = ''
	publicIPAPI = ''

	try:
		logDirectory = godaddyproperties.logdirectory
		print ("Property logdirectory successfully loaded")
	except:
		print ("No logdirectory property found. Using default: " + logdirectory)
		pass

	try:
		logger = logging.getLogger('server_logger')
		logger.setLevel(logging.DEBUG)
		log_filename = logDirectory + 'GoDaddyDNSUpdater.log'
		fh = logging.handlers.RotatingFileHandler(log_filename, maxBytes=10*1024*1024, backupCount=5)
		ch = logging.StreamHandler()
		ch.setLevel(logging.DEBUG)
		formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
		fh.setFormatter(formatter)
		ch.setFormatter(formatter)
		#logger.addHandler(fh)
		logger.addHandler(ch)
	except:
		print ("FATAL: Unable to set logger... Exiting.\n\n")
		exitScript(99)

	#############################################
	# Log some stuff
	#############################################
	logger.info("Running GoDaddy DNS Updater - Version: " + str(version))
	logger.info("Loading properties...")

	#############################################
	# For each item, try to pull a value from
	# the properties file. If the entry does
	# not exist, set a default value, as set
	# above
	#############################################
	try:
		domainName = godaddyproperties.domainname
		logger.info("Property domainname successfully loaded")
	except:
		logger.warning("You must provide a domainname.")
		exitScript(99)

	try:
		username = godaddyproperties.username
		logger.info("Property username successfully loaded")
	except:
		logger.warning("You must provide a username for " + domainName)
		exitScript(99)

	try:
		password = godaddyproperties.password
		logger.info("Property password successfully loaded")
	except:
		logger.warning("You must provide a password for " + domainName)
		exitScript(99)

	try:
		loginURL = 'https://sso.godaddy.com/?realm=idp&app=mya&path=&pc=urlargs'
		dnsManagementURL = 'https://dcc.godaddy.com/manage/' + domainName + '/dns'
		publicIPAPI = 'https://api.ipify.org?format=json'
	except:
		logger.warning("Failed to load default properties")
		exitScript(99)

def getPublicIP():
	publicIP = '0'
	r = requests.get(publicIPAPI)
	if r.status_code < 300:
		try:
			publicIP = json.loads(r.text)['ip']
			#logger.infopublicIP
		except:
			logger.warning("Failed to obtain public IP from api")
			exitScript(99)
	return publicIP

def login(loginURL, username, password):
	#############################################
	# Used to log into the account
	#############################################
	try:
		browser.get(loginURL)
		browser.maximize_window()
		browser.get_screenshot_as_file('screenshots/godaddyloginScreen.png')
		wait.until(lambda browser: browser.find_element_by_id('username'))
		browser.get_screenshot_as_file('screenshots/usernameEntry.png')
	except:
		logger.warning("Failed to get login screen")
		exitScript(99)

	try:
		usernameElement = browser.find_element_by_id('username')
		usernameElement.clear()
		usernameElement.send_keys(username)

		passwordElement = browser.find_element_by_id('password')
		passwordElement.clear()
		passwordElement.send_keys(password)
		browser.get_screenshot_as_file('screenshots/passwordEntry.png')

		signInButton = browser.find_element_by_id('submitBtn')
		signInButton.click()
	except:
		logger.warning("Failed to submit form")
		exitScript(99)

	try:
		#wait.until(lambda browser: browser.find_element_by_class_name('footer-html'))
		time.sleep(10)
		browser.get_screenshot_as_file('screenshots/godaddyPostloginScreen.png')
	except:
		logger.warning("Failed to get past login screen")
		exitScript(99)

def getDNSRecord():
	recordValue = 0
	try:
		browser.get(dnsManagementURL)
		browser.get_screenshot_as_file('screenshots/godaddyDNSManagementScreen.png')
		wait.until(lambda browser: browser.find_element_by_id('collapseRecords'))
		time.sleep(5) # It takes a few seconds to load the entire DNS table
		browser.get_screenshot_as_file('screenshots/godaddyDNSManagementRecordsScreen.png')
		for row in browser.find_elements_by_css_selector("tr.ng-scope"):
			recordType = str(row.find_elements_by_tag_name("td")[0].text)
			if recordType == 'A':
				recordName = str(row.find_elements_by_tag_name("td")[1].text)
				recordValue = str(row.find_elements_by_tag_name("td")[2].text)
				recordTTL = str(row.find_elements_by_tag_name("td")[3].text)
	except:
		logger.info("Unable to obtain DNS results from GoDaddy")
		exitScript(99)

	if recordValue != 0:
		return recordValue
	else:
		exitScript(99)

def updateARecord(publicIP, goDaddyPublicIP):
	try:
		found = False
		browser.get(dnsManagementURL)
		wait.until(lambda browser: browser.find_element_by_id('collapseRecords'))
		time.sleep(5) # It takes a few seconds to load the entire DNS table
		browser.get_screenshot_as_file('screenshots/godaddyDNSManagementRecordUpdateScreen.png')

		# Loop through DNS entries by type name.
		# If we find an a-record, click to edit
		for row in browser.find_elements_by_css_selector("tr.ng-scope"):
			recordType = row.find_elements_by_tag_name("td")[0]
			if recordType.text == 'A':
				recordEdit = row.find_elements_by_tag_name("td")[5]
				recordEdit.find_elements_by_tag_name('span')[0].click()
				time.sleep(5)
				browser.get_screenshot_as_file('screenshots/godaddyUpdateRecord.png')
				for item in row.find_elements_by_tag_name('input'):
					if item.get_attribute('value') == goDaddyPublicIP:
						item.clear()
						item.send_keys(publicIP)
						item.send_keys(Keys.ENTER)
						browser.get_screenshot_as_file('screenshots/godaddyRecordUpdated.png')
						saveButton = browser.find_element_by_id('btnRecordSaveXS')
						found = True
		if found:
			saveButton.click
			logger.info("DNS a-record updated successfully.")
			time.sleep(5)
			browser.get_screenshot_as_file('screenshots/godaddyRecordUpdated-PostSave.png')
	except:
		logger.warning("Unable to update DNS record")
		exitScript(99)

def exitScript(exitCode):
	browser.quit()
	if exitCode == 0:
		logger.info("Completed requested work. Exiting...")
	else:
		logger.error("Script terminated")
	sys.exit(exitCode)

if __name__ == '__main__':
	main()

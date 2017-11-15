# GoDaddy_A-Record_Updater

Just a simple python script to sync your GoDaddy domain name(a-record) with your public IP.

GoDaddy doesn't offer an application to do this, so I wrote one for myself. 


**Requirements**

* Python 2.7
* Selenium - Phantomjs driver
* Python modules
	* requests
	* getopt
	* logging
	* logging.handlers
	* cgi
* A "logs" directory
	* Feel free to fork, modify and remove this if wanted. It just helps me with troubleshooting/debuging
* A "screenshots" directory
	* Feel free to fork, modify and remove this if wanted. It just helps me with troubleshooting/debuging


##### That said, I just run the script inside of my own Docker container; which has all of the above requirements

[sterrymike/mycontainers](https://hub.docker.com/r/sterrymike/mycontainers/)

##### Feel free to fork this as you please and copy my docker container.

**NOTE:** I made the docker container when I fairly new to Docker, so it can probably be made a bit smaller than the current iteration.

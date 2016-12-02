# CHROnIC_Collector
##**Cisco Health Report & ONline Information Collector**
This is an application designed to interact with infrastructure components, and perform an online analysis of them.

*The Challenge* - It can be tedious to collect the data needed for routine health analysis. For example, the UCS Health Check requres a PowerShell script to be ran, which requires the UCS PowerTools to be installed, as well as a number of security requirements. This can be very complex for anyone who does not routinely use PowerShell.

*The Solution* - Create an application that will enable interaction with UCS from the cloud. This particular application has several microservices, including:

* Bus - Used as a basic HTTP-based message queue
* Collector - On-prem component used to exchange core information between on-prem infrastructure and the Portal. Consumes messages from the queue.
* Portal - Information Collection service and agent used to push tasks into the queue.
* UCS ESX Analyzer - Process data and generate reports which are pushed back into the queue.

Contributors - Josh Anderson, Chad Peterson, Loy Evans

###This repo is for the following service:
Collector - This microservice is designed to reach out to the bus to consume messages, take action on those messages, and post responses back to the bus. It is designed to be ran as an on-prem component that communicates to the bus in a public infrastructure. The messages intended to be consumed are sets of API calls that will be executed against on-prem gear, and data will be collected from those API calls and posted back to the bus.

###This repo includes the following resources:
**Repo Information**
* LICENSE
    * Code Licensing Information
* README.md
    * This document
* .gitignore
    * Standard gitignore file to prevent commiting unneeded or security risk files

**CICD Build Configuration**
* .drone.sec
    * Encrypted Drone Settings
* .drone.yml
    * CICD Build instructions for Drone Server
* drone_secrets_sample.yml
    * template for the secrets file that will be used to encrypt credentials
* Dockerfile
    * Docker build file for applicaiton container
* requirements.txt
    * pip installation requirements

**Application Files**
* app.py
    * This kicks off the application. This application listens and is delivered strictly as an API.
* test.py
    * Flask build test application. Used to validate API functionality for the build process.
* ucs.csv / ucs.json
    * Sample UCS API calls
* vcenter.csv / vcenter.json
    * Sample vCenter API calls
* samplepush.py
    * Sample push to bus

# Installation

## Environment

* [Docker Container](#opt1)
* [Native Python](#opt2)

## Docker Installation<a name="opt1"></a>

**Prerequisites:**
The following components are required to locall run this container:
* [Docker](https://docs.docker.com/engine/installation/mac/)

**Get the container:**
The latest build of this project is available as a Docker image from Docker Hub:
```
docker pull joshand/chronic_collector:latest
```

**Run the application:**
```
docker run -e chronicbus=<bus-dns-or-ip> -d --name collector joshand/chronic_collector:latest
```

**Check the logs to get the Channel ID:**
```
docker logs collector
```
```
Channel ID: xxxxxxxx
```

**With the Channel ID, you can then post messages to the Bus that the Collecter will retrieve and perform action on**

**Testing the app with the Bus:**
[Collector Testing](#test) See below for testing instructions

## Local Python Installation<a name="opt2"></a>

**Prerequisites:**
The following components are required to locally run this project:
* [Python 3.5](http://docs.python-guide.org/en/latest/starting/install/osx/) - Install via homebrew recommended if on a Mac
* git - Part of the Xcode Command Line Tools
* [pip](https://pip.pypa.io/en/stable/installing/)
* [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/)

**Get the code:**
The latest build of this project is available on Github:
```
mkdir ~/chronic_collector
cd ~/chronic_collector
git clone https://github.com/joshand/CHROnIC_Collector
```

**Set up virtual environment and PIP:**
```
virtualenv chronic
source chronic/bin/activate
pip install -r requirements.txt
```

**Execute the app:**
```
./genid.sh
python app.py
```

**Testing the app with the Bus:**
[Collector Testing](#test) See below for testing instructions

# Collector Testing<a name="test"></a>
To test the collector, you can test-load some data into the bus. To do this, you first need to set an export for the Bus address:
```
export chronicbus=<bus-dns-or-ip>
```

Next, you need to prepare the data to load into the bus. Sample UCS and vCenter data has been included. If you want to create new instructions or modify the existing ones, utilize the ucs and vcenter csv files as a starting point. Once you have formatted the data to your liking, convert your data to json format:
```
csvjson ucs.csv > ucs.json
csvjson vcenter.csv > vcenter.json
```

Next, you need to push the sample data to the bus. If you are running everything locally, genid.sh will have created the channel id for you. If you are running the app in a container, and trying to do the data load outside of the container, you will need to modify your local /tmp/channel.id to match the channel id that is present in your docker container. Once you are ready, use the samplepush.py script to push data onto the bus:
```
python samplepush.py ucs.json ucs ip_or_hostname username password
python samplepush.py vcenter.json vcenter ip_or_hostname username password
```

Finally, when you run the app (either locally or in the container), it will consume the messages, execute the instructions, and post results back to the bus.

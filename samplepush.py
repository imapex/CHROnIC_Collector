#!/usr/bin/python
import requests
import os
import sys
import base64

if len(sys.argv) < 4:
    sys.exit("Syntax: " + sys.argv[0] + " <file.json> <description,no_spaces> <ip> <un> <pw>")

#testfile = 'vcenter.json'
testfile = sys.argv[1]
testdesc = sys.argv[2]
testip = sys.argv[3]
testun = sys.argv[4]
testpw = sys.argv[5]
baseurl = os.environ['chronicbus']

def getfile(fn):
    with open(fn, 'r') as myfile:
        data = myfile.read()

    return data

def doreplace(data, sip, sun, spw):
    newdata = data
    newdata = newdata.replace('%ip%',sip)
    newdata = newdata.replace('%un%',sun)
    newdata = newdata.replace('%pw%',spw)

    #newdata = newdata.replace('\\\"','\"')
    #newdata = newdata.replace('\"','\\\"')

    return newdata

def dopost(url, data):
    headers = {'Content-type': 'application/json'}
    r = requests.post(url, data=data, headers=headers)

    return r

fdata = getfile(testfile)
ndata = doreplace(fdata, testip, testun, testpw)
colid = getfile("/tmp/channel.id").replace("\n", "")
url = "http://" + baseurl + "/api/send/" + colid
#print("[" + url + "]")
content = '{"msgdata":"' + base64.b64encode(bytes(ndata, "utf-8")).decode("ascii") + '", "status": "0", "desc":"' +  testdesc + '"}'
ret = dopost(url, content)
print(content)
print(ret)


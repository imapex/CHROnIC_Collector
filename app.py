#!/usr/bin/python
import base64
import json
import requests
import time
import os
import sys
import subprocess
from subprocess import call
from lxml import etree
from io import StringIO
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import random
import string

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

try:
    sparktoken = os.environ['sparktoken']
    sparkauth = "Bearer %s" % sparktoken
    sparkroom = os.environ['sparkroom']
except:
    sparktoken = ""
    sparkauth = ""
    sparkroom = ""

headers = {
    'authorization': sparkauth,
    'cache-control': "no-cache",
    'content-type': 'application/json'
    }


# -- sendMessage: Send message to Spark room
def sendMessage(roomid,message):
    if isinstance(message, dict) or isinstance(message, list):
        message = str(message)
    if sparktoken != "":
        url = "https://api.ciscospark.com/v1/messages"
        hookdata = {"roomId": roomid, "text": message}
        jsondata = json.dumps(hookdata)

        response = requests.request("POST", url, data=jsondata, headers=headers)


# -- forceString: Make sure input text is a string, convert dict's and list's to string
def forceString(vardata):
    retdata = vardata
    if isinstance(vardata, dict) or isinstance(vardata, list):
        retdata = str(retdata)

    return retdata


# -- id_generator: Generate 8 digit random string; used for a Channel ID
def id_generator(size=8, chars=string.ascii_uppercase + string.digits + string.ascii_lowercase):
    return ''.join(random.choice(chars) for _ in range(size))


# -- cleanxml: This strips the namespaces from imported XML to make processing simpler
def cleanxml(data):
    data = data.replace('<?xml version="1.0" encoding="UTF-8"?>', '')
    data = data.replace('<soapenv:', '<')
    data = data.replace('</soapenv:', '</')
    data = data.replace('xmlns:', 'disabledtag')
    data = data.replace('xmlns=', 'disabledtag=')
    data = data.replace('xsi:', 'xsi')
    return data


# -- getchannelid: This attempts to import an existing Channel ID from a stored file.
def getchannelid():
    try:
        with open('/tmp/channel.id', 'r') as myfile:
            data = myfile.read()
        data = data.replace("\n", "")
    except OSError as e:
        data = -1
    except IOError as e:
        data = -1

    return data


# -- writechannelid: This writes a generated Channel ID to a stored file.
def writechannelid(chid):
    try:
        with open('/tmp/channel.id', 'w') as myfile:
            myfile.write(chid)
    except OSError as e:
        pass
    except IOError as e:
        pass


# -- download_file: This downloads a specified file to disk.
def download_file(url, local_filename, creds):
    #http://stackoverflow.com/questions/16694907/how-to-download-large-file-in-python-with-requests-py
    #local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True, auth=creds, verify=False)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                #f.flush() commented by recommendation from J.F.Sebastian
    return local_filename


# -- ProcessXML: This processes XML code and retrieves specified data from the tree.
def ProcessXML(content, rootpath, retvals, con_json):
    try:
        fdata = cleanxml(content)
        f = StringIO(fdata)
        tree = etree.parse(f)

        jsonarr = {}
        retsingle = ""
        r = tree.xpath(rootpath)
        #print("step 1:", rootpath, retvals, len(r))
        for x in range(0, len(r)):
            jsonarr[x] = {}
            retarr = retvals.split(",")
            for orgret in retarr:
                #print("step 2:", orgret)
                retnum = ""
                if orgret.find(':') >= 0:
                    arrret = orgret.split(':')
                    ret = arrret[0]
                    srch = arrret[1]
                else:
                    ret = orgret
                    srch = ""

                if ret.find('|') >= 0:
                    arrret = orgret.split('|')
                    ret = arrret[0]
                    retnum = int(arrret[1])

                if ret == '~':
                    r2 = r[x].text
                    retsingle = r2
                    if r2:
                        r2 = r2.split()
                elif ret.find('/~') >= 0:
                    retrootarr = ret.split("/~")
                    r2a = r[x].xpath(retrootarr[0])
                    r2 = "".split()
                    if retnum != "":
                        if len(r2a) > 0:
                            r2.append(r2a[retnum].text)
                    else:
                        for y in range(0, len(r2a)):
                            #if retnum != "":
                            #    print(r2a[y].text)
                            r2.append(r2a[y].text)
                    #r2 = r[x].xpath(retrootarr[0])[0].text
                    #if r2:
                    #    r2 = r2.split()
                else:
                    r2 = r[x].xpath(ret)
                    retsingle = r2[0]
                    #print("Step 3:", ret, x, r2)

                if srch != "":
                    dodelete = 0
                    if len(r2) <= 0:
                        dodelete = 1
                    elif r2[0] != srch:
                        dodelete = 1

                    if dodelete == 1:
                        del jsonarr[x]
                        break
                elif srch == "":
                    jsonarr[x][ret] = r2

        if len(jsonarr) == 1:
            jsonarr = retsingle
        elif con_json == 1:
            print("---------------")
            newjsonarr = {}
            newtemparr = {}
            innercount = 0
            outercount = 0
            for k in jsonarr:
                newarr = jsonarr[k]
                for k2 in newarr:
                    if len(newarr[k2]) > 0:
                        newtemparr[k2] = newarr[k2]
                        innercount = innercount + 1
                        if innercount >= len(newarr):
                            newjsonarr[outercount] = newtemparr
                            innercount = 0
                            newtemparr = {}
                            outercount = outercount + 1

                    #print(k, k2, len(newarr), newarr[k2], len(newarr[k2]), "\n-----------\n")
            #print(newjsonarr)
            jsonarr = newjsonarr

        #retjsonarr = []
        #if isinstance(jsonarr, dict):
        #    for jsonelem in jsonarr:
        #        #print(jsonelem)
        #        retjsonarr.append(jsonarr[jsonelem])
        #else:
        #    retjsonarr = jsonarr
        #return retjsonarr
    except:
        sendMessage(sparkroom, "=================\nException Encountered in ProcessXML.\nContent:" + forceString(content) + "\nRoot Path(s):" + forceString(rootpath) + "\nReturn Values:" + forceString(retvals) + "\nConsolidate JSON:" + forceString(con_json) + "\n=================")
        jsonarr = []

    return jsonarr


# -- ProcessMessages: This function processes messages in the thread and performs action on those messages.
def ProcessMessages(msgdata, updateurl, msgdesc):
    try:
        msgdata = base64.b64decode(bytes(msgdata, "utf-8")).decode("ascii")
        if msgdata.find("\\") >= 0:
            msgdata = msgdata.replace('\"', '"')
        msgdata = msgdata.replace("\n","")
        #print(msgdata)
        jsondata = json.loads(msgdata)

        ret1 = ""
        ret2 = ""
        ret3 = ""
        founddata = ""
        foundjson = {}
        # ++ Loop through each message in the JSON data and parse out the individual fields
        for msg in jsondata:
            method = msg['method'].upper()
            url = msg['url']
            contenttype = msg['content_type']
            soapaction = msg['soap_action']
            basicauth = msg['basic_auth']
            postdata = msg['post_data']
            filekey = msg['file_key']
            postprocessing = msg['post_processing']
            cookie = msg['cookie']
            returndata = msg['return_data']
            cons_data = msg['consolidate_data']
            if cons_data == "":
                cons_data = 0
            else:
                cons_data = int(cons_data)

            # ++ Look for URLs in this format: https://%2:netConfig/candidateVnic/spec/ip...
            if url.find("%") > 0:
                arrurl = url.split("%")
                urlsubst = arrurl[1]
                # ++ Parse out the fields. In this example, %2 is taking return data from a previous call, and storing the data from netConfig
                arrurlsubst = urlsubst.split(":")
                replval = arrurlsubst[0]
                replkey = arrurlsubst[1]
                if replval == "2":
                    doretupdate = 2
                    arrrepldata = ret2

                jsonurl = {}
                urlcounter = 0
                # ++ Loop through the data previously stored, strip out the values and store them in a JSON array
                for repldata in arrrepldata:
                    #TypeError: list indices must be integers or slices, not dict
                    #print("###############", type(repldata), type(ret2), "==========", repldata, "==========", ret2)
                    replblock = ret2[repldata]
                    replentry = replblock[replkey]
                    replentry = replentry[0]
                    jsonurl[urlcounter] = arrurl[0] + replentry + arrurl[2]
                    urlcounter = urlcounter + 1

                url = jsonurl
            # ++ If Basic authentication is required, parse auth string and prepare credentials. If not, send clear string.
            if basicauth != "":
                if basicauth.find(":") >= 0:
                    basicauth = basicauth.split(":")
                    auth = (basicauth[0], basicauth[1])
                else:
                    auth = eval(basicauth)
            else:
                auth = ""

            # ++ Set up Headers for request
            headers = {}
            if contenttype != "":
                headers['content-type'] = contenttype

            if soapaction != "":
                headers['SOAPAction'] = soapaction

            # ++ If this is a request that has a content-body, prepare that content
            if postdata != "":
                # ++ Look for substitutions that need to be made
                # ++ For example, <configResolveClass cookie='%1%' classId='computeBlade' inHierarchical='true'>
                # ++ In this example, we will substitute in the data previously stored in return 1 for %1%
                if ret1 != "":
                    if postdata.find("%1%") >= 0:
                        if isinstance(ret1, dict) or isinstance(ret1, list):
                            ret1 = str(ret1)
                        postdata = postdata.replace("%1%", ret1)
                if ret2 != "":
                    if postdata.find("%2%") >= 0:
                        if isinstance(ret2, dict) or isinstance(ret2, list):
                            ret2 = str(ret2)
                        postdata = postdata.replace("%2%", ret2)

                data = postdata
            else:
                data = ""

            # ++
            if cookie == "%1%":
                if ret1 != "":
                    cookies = eval(ret1)
                else:
                    cookies = ""
            else:
                cookies = ""
            #print(type(cookies))

            if method == "DOWNLOAD":
                if not isinstance(url, dict):
                    jsonurl = {}
                    jsonurl[0] = url

                #print(jsonurl)
                for urlid in jsonurl:
                    url = jsonurl[urlid]
                    print(url)
                    sendMessage(sparkroom, "DOWNLOAD: " + url)

                    try:
                        d = download_file(url, filekey, auth)
                    except OSError:
                        pass
                        d = "0"

                    if d == "0":
                        founddata = "Unable to Access"
                        sendMessage(sparkroom, founddata)
                    else:
                        rval = subprocess.run(postprocessing, shell=True, stdout=subprocess.PIPE)
                        lines = rval.stdout.decode('UTF-8')
                        arrlines = lines.split('\n')
                        jsonarr = {}
                        lcounter = 0
                        for line in arrlines:
                            if line != "":
                                jsonarr[lcounter] = line
                                lcounter = lcounter + 1

                        founddata = jsonarr

                    if doretupdate == 2:
                        ret2[urlid][postdata] = founddata
                    #print(founddata)
            else:
                print(url)
                sendMessage(sparkroom, method + ":" + url)
                try:
                    r = requests.request(method, url, data=data, headers=headers, auth=auth, cookies=cookies, verify=False)
                except requests.exceptions.RequestException as e:
                    print(e)
                    r = ""

                if r:
                    rcontent = r.content.decode("UTF-8")
                else:
                    rcontent = ""

            if returndata == "*":
                founddata = rcontent
            #elif returndata[0:2] == "*=":
            #    founddata = rcontent
            #    rout = returndata[2:]
            elif returndata != "":
                #XML=/aaaLogin;@outCookie=ret1
                rdataarr = returndata.split("=")
                #['XML', '/aaaLogin;@outCookie', 'ret1']
                rtype = rdataarr[0]
                if len(rdataarr) > 1:
                    rdata = rdataarr[1]
                else:
                    rdata = ""

                if len(rdataarr) > 2:
                    rout = rdataarr[2]
                else:
                    rout = ""

                if rtype == "COOKIE":
                    #COOKIE=vmware_soap_session=ret1
                    tempdict = {}
                    tempdict[rdata] = r.cookies[rdata]
                    founddata = str(tempdict)
                elif rtype == "XML":
                    rvalsarr = rdata.split(";")
                    rootpath = rvalsarr[0]
                    retvals = rvalsarr[1]

                    founddata = ProcessXML(rcontent, rootpath, retvals, cons_data)

                if rout == "ret1":
                    ret1 = founddata
                elif rout == "ret2":
                    ret2 = founddata

            if rtype == "RETURN":
                if rdata == "ret1":
                    returndata = ret1
                elif rdata == "ret2":
                    returndata = ret2

                retjsonarr = []
                if isinstance(returndata, dict) or isinstance(returndata, list):
                    for jsonelem in returndata:
                        #print("*************", jsonelem, returndata[jsonelem])
                        retjsonarr.append(returndata[jsonelem])
                        #print("*************", jsonelem, returndata[jsonelem], retjsonarr)
                else:
                    retjsonarr = returndata

                returndata = str(retjsonarr)
                #print(returndata)

                returndata = "{'" + msgdesc + "':" + returndata + "}"
                returndata = base64.b64encode(bytes(returndata, "utf-8")).decode("ascii")
                #data = "{\"msgresp\":\"{'" + msgdesc + "':" + returndata + "}\"}"
                data = '{"msgresp":"' + returndata + '"}'
                headers = {"Content-Type": "application/json"}
                print(updateurl)
                sendMessage(sparkroom, "POST:" + updateurl)
                try:
                    r = requests.request("POST", updateurl, data=data, headers=headers, verify=False)
                except requests.exceptions.RequestException as e:
                    print(e)
                    sendMessage(sparkroom, "=================\nException Encountered in ProcessMessages.\nError:" + forceString(e) + "\n=================")
                    r = ""

                #print(rtype, rdata, data, r)

            ##print(msg)
            ##print("postdata", postdata)
            #print("content", rcontent)
            #print("cons_data", cons_data)
            #print("founddata", founddata)
            #print("ret1", ret1)
            #print("ret2", ret2)
            #print("\n\n")
    except:
        sendMessage(sparkroom, "=================\nException Encountered in ProcessMessages.\nMessage Data:" + forceString(msgdata) + "\nUpdate URL" + forceString(updateurl) + "\nMessage Description:" + forceString(msgdesc) + "\n=================")


# -- Main Program Start
mychid = getchannelid()
if mychid == -1:
    mychid = id_generator()
    writechannelid(mychid)

baseurl = os.environ['chronicbus']
url = 'http://' + baseurl + '/api/get/' + mychid
updateurl = 'http://' + baseurl + '/api/update/'
print("Channel ID: " + mychid)
sendMessage(sparkroom, "Collector Online: " + mychid)

# -- Main Program Loop
while True:
    print("Check Bus: " + url)
    try:
        r = requests.get(url)
    except requests.exceptions.RequestException as e:
        print(e)
        sendMessage(sparkroom, "=================\nException Encountered in Main.\nError:" + forceString(e) + "\n=================")
        r = ""

    if r:
        msgdata = r.content.decode("UTF-8")
    else:
        msgdata = ""

    if msgdata != "":
        msgjson = json.loads(msgdata)
        for msg in msgjson:
            if "desc" in msgdata:
                msgdesc = msg['desc']
            else:
                msgdesc = msg['id']

            ProcessMessages(msg['msgdata'], updateurl + str(msg['id']), msgdesc)
        #print(msgjson[0]['msgdata'])
    #break
    time.sleep(15)

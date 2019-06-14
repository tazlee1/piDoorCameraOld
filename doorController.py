#!/usr/bin/env python3

# Author: Tony Phillips
# Version: 2019-06-10
# Language: Python
# Language version: 3.5.3

###Files required
# none

#Notes: This file is to start on boot.  It will listen for door switch to be opened.  Once opened it will send a command (Process) to check the scale head for new data. It will also send a command to any cameras to take a picture.

import RPi.GPIO as GPIO
import os.path
import time
from datetime import datetime
from datetime import timedelta
from numbers import Number
from multiprocessing import Process
import sys
import signal
import socket
from os.path import join, dirname, abspath
import urllib.request
import urllib.parse
import sys, traceback

# Set Broadcom mode so we can address GPIO pins by number.
GPIO.setmode(GPIO.BCM) 
# This is the GPIO pin number we have one of the door sensor
# wires attached to, the other should be attached to a ground pin.
DOOR_SENSOR_PIN = 18

# Initially we don't know if the door sensor is open or closed...
isOpen = None
oldIsOpen = None 

# Set up the door sensor pin.
GPIO.setup(DOOR_SENSOR_PIN, GPIO.IN, pull_up_down = GPIO.PUD_UP)

# setup port for remote cameras
port = 12145
uploadPort = 12146
# IP addresses for cameras
camlist = ['piCam1.local'] # ie: , '192.168.0.17']

# Backup flag
backup = False

# setup log file and working path
wDir = dirname(abspath(__file__))
os.chdir(wDir)
debug = True

def write_log(message):
    file_name = "log_{}.log".format(datetime.now().isoformat()[:10])
    file_name = file_name.replace(":","")
    year = numToString(datetime.now().year, 4)
    month = numToString(datetime.now().month, 2)
    completeName = os.path.join(wDir, 'log', year, month, file_name)

    directory = os.path.dirname(completeName)
    if not os.path.exists(directory):
        os.makedirs(directory)
        print("Making directory. Did not exist.")
    with open(completeName, "a") as myfile:
        myfile.write("{}\n".format(message))

def sendCameraCommand():
    for cam in camlist:
        try:
            camAddress = socket.gethostbyname(cam.strip())
            s = socket.socket()
            s.connect((camAddress, port))
            print(s.recv(1024))
            s.close()
            print("Camera command sent to {}".format(cam))
        except Exception as e:
            print("Could not connect to ", cam)
            write_log(traceback.format_exc())

def sendUploadCommand():
    global backup
    for cam in camlist:
        try:
            camAddress = socket.gethostbyname(cam.strip())
            s = socket.socket()
            s.connect((camAddress, uploadPort))
            print(s.recv(1024))
            s.close()
            print("Upload command sent to {}".format(cam))
        except Exception as e:
            print("Could not connect to ", cam)
            write_log(traceback.format_exc())


def numToString(num, length):
    retVal = '{}'.format(num)
    while len(retVal) < length:
        retVal = "0{}".format(num)
    return retVal

def backup_file(contents):
    file_name = "scales-{}.htm".format(datetime.now().isoformat())
    file_name = file_name.replace(":","")
    year = numToString(datetime.now().year, 4)
    month = numToString(datetime.now().month, 2)
    completeName = os.path.join(wDir, 'log', year, month, file_name)

    directory = os.path.dirname(completeName)
    if not os.path.exists(directory):
        os.makedirs(directory)
        print("Making directory. Did not exist.")

    with open(completeName, 'w') as file:
        file.write(contents.decode("utf-8"))
    write_log(' Saved backup to: {}'.format(completeName))

def getUrlContents(url):
    try:
        resp = urllib.request.urlopen(url)
        respData = resp.read()
        t = respData#.decode("utf-8")
        return t
    except urllib.error.HTTPError as e:
        print('Error code: ', e.code)
        raise
    except urllib.error.URLError as e:
        print('Reason: ', 'Site timed out')
        print('Error code: ', e.reason)
        raise
    except Exception as e:
        print('Exception error code: ', e.code)
        raise

def logBadRows(data):
    with open("incomplete_rows.log", "a") as myfile:
        myfile.write("{0}: {1}\n".format(datetime.now().isoformat(timespec='microseconds'), data))
        message = {'title':'Incomplete data found on scale import', 
            'body':'The following row was found with incomplete data.\n{}\n\nPlease look into'.format(data),
            'sendto':'tony@maplerowdairy.com'}
        post_data = urllib.parse.urlencode(message).encode('ascii')
        headers = {}
        headers['Content-Type'] = 'application/json'
        r = urllib.request.urlopen(url = "http://mobi.mrdfarm.com/sendnotifications.php", data = post_data)
        print(r.read())

def updateScales():
    print("Updating Scales")
    try:
        # get web contents
        write_log(" Getting file")
        r = getUrlContents('http://192.168.0.131/escapethree.htm')
        print("File length: {}".format(len(r)))
        #write_log("    Got file with {} charcters.".format(len(r)))
        if (len(r) > 444):
            #save a backup of original file
            backup_file(r)
            write_log(" File backed up")
            # run command to clear scale
            clear = getUrlContents('http://192.168.0.131/q.htm?inputbox=submit')

            #proceed to process file.  Get contents with in the PRE tags
            pre = b"<PRE>"
            post = b"</PRE>"

            startIndex = r.find(pre)
            endIndex = r.find(post)
            write_log(" Start to process file")
            if (startIndex != -1 and startIndex < endIndex):
                r = r[startIndex + 5:endIndex]

                t = r.replace(b'\n', b'').replace(b'\r',b';').decode("utf-8")
                t = t.split(";")
                for row in t:
                    print(row)
                    #write_log("        Row: {}".format(row))
                    #write_log("        Row length: {}".format(len(row)))
                    st = row.split(",")
                    print("Row has {} columns".format(len(st)))
                    if len(st) == 10:
                        st[3] = st[3].replace(" lb", "")
                        dt = st[1].split("/")
                        st[1] = "20" + dt[2] + "-" + dt[0] + "-" + dt[1]
                        url = 'http://mobi.mrdfarm.com/scales/s_import.php?DT={} {}&CO={}&WT={}&TR={}&PO={}&TA={}&NH={}&FD={}&MO={}'.format(st[1], st[0], st[2].strip(), st[3].strip(), st[4].strip(), st[5].strip(), st[6].strip(), st[7].strip(), st[8].strip(), st[9].strip()).replace(' ','\%20')
                        write_log("         {}".format(url))
                        results = getUrlContents(url)
                        print(results)
                        write_log("         {}".format(results))
                    elif len(st) > 1:
                        write_log("Row has {} columns".format(len(st)))
                        logBadRows(row)
                        write_log("Skipped partial row. See incomplete_rows.log")
                        print("Skipped partial row. See incomplete_rows.log")
                    else:
                        print("Skipped")
                        write_log("     Skipped. Missing data. Size: {0}, Data: {1}".format(len(row), row))
            else:
                write_log(" No records found")

            print("Update is completed.")
            write_log("{} Successfully finished scale update.".format(datetime.now().isoformat()))
        else:
            print("No new records to process")
            write_log("No new records to process. Finished at {}.".format(datetime.now().isoformat()))
    except Exception as e:
        write_log(traceback.format_exc())
        print(traceback.format_exc())
try:
    while True:
        oldIsOpen = isOpen
        isOpen = GPIO.input(DOOR_SENSOR_PIN)
        if (isOpen and (isOpen != oldIsOpen)):
            # log when the door is opened
            write_log("Door opened at {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            print("Opened")

            Process(target = updateScales).start()
            # send command to take pictures to all remote cameras
            Process(target = sendCameraCommand).start()
            # Uncomment following line and add more lines for more camera
            #Process(target = notifyCamera2).start()
            backup = datetime.now() + timedelta(minutes=5)

        elif (isOpen != oldIsOpen):
            print("Closed")
            # log when the door is closed
            write_log("Door closed at {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        if (backup != False):
            if (backup < datetime.now()):
                write_log("Sending upload command")
                Process(target = sendUploadCommand).start()
                backup = False
        time.sleep(0.1)
except KeyboardInterrupt:
    pass

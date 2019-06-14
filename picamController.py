#!/usr/bin/python3.5

# Author: Tony Phillips
# Version: 2019-06-10

import time
from datetime import datetime
import picamera
import sys, os
import socket
import subprocess
from subprocess import Popen, PIPE
from multiprocessing import Process

# Format photo will be saved as e.g. jpeg
PHOTOFORMAT = 'jpeg'

# Camera identifier
CAMERA_NAME = "_cam1"

#The directory to sync
imgdir="/home/pi/img/"

# Create a camera object and capture image using generated filename
camera = picamera.PiCamera()
# setup camera and start preview
camera.resolution = (1920, 1080)
camera.start_preview()

def numToString(num, length):
    retVal = '{}'.format(num)
    while len(retVal) < length:
        retVal = "0{}".format(num)
    return retVal
    
def write_log(message):
    file_name = "camera_{}.log".format(datetime.now().isoformat()[:10])
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

if __name__ == '__main__':
    write_log("picamController started at {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    if not os.path.exists(imgdir):
        os.makedirs(imgdir)
    try:
        # start listening to socket request
        s = socket.socket()
        host = "" #socket.gethostname() #ip of raspberry pi
        port = 12145
        s.bind((host, port))
        s.listen(5)
    
        while True:
            c, addr = s.accept()
            print ('Got connection from',addr)
            write_log('Got connection from {} at {}'.format(addr, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            fullFileName = filename + CAMERA_NAME + "." + PHOTOFORMAT
            cdir = os.getcwd()
            os.chdir(imgdir)
            print("Photo: %s"%fullFileName)
            camera.capture(fullFileName, format=PHOTOFORMAT)
            write_log("Created file: {}".format(fullFileName))
            os.chdir(cdir)
            print("Photo captured and saved ...")
            c.send(str.encode('Thank you for connecting'))
            c.close()
    except KeyboardInterrupt:
        pass
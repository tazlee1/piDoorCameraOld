#!/usr/bin/env python3.4

# Author: Tony Phillips
# Version: 2019-06-06

import time
import datetime
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

#trigger when to take picture
takePicture = False


# Create a camera object and capture image using generated filename
def camCapture():
    global takePicture
    with picamera.PiCamera() as camera:
        # setup camera and start preview
        camera.resolution = (1920, 1080)
        camera.start_preview()
        while True:
            if takePicture:
                filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                fullFileName = filename + CAMERA_NAME + "." + PHOTOFORMAT
                cdir = os.getcwd()
                os.chdir(imgdir)
                
                print("Photo: %s"%fullFileName)
                
                camera.capture(fullFileName, format=PHOTOFORMAT)
                os.chdir(cdir)
                print("Photo captured and saved ...")
                return fullFileName
                takePicture = False
            time.sleep(1)


if __name__ == '__main__':
    global takePicture

    # run command to start camera
    Process(target = camCapture).start()

    # start listening to socket request
    s = socket.socket()
    host = "" #socket.gethostname() #ip of raspberry pi
    port = 12145
    s.bind((host, port))
    s.listen(5)
    
    while True:
        c, addr = s.accept()
        print ('Got connection from',addr)
        takePicture = True;
        c.send(str.encode('Thank you for connecting'))
        c.close()

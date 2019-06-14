#!/usr/bin/env python3

# Author: Tony Phillips
# Version: 2019-06-10

import time
from datetime import datetime
import sys, os
import socket
from multiprocessing import Process

#The directory to sync
syncdir="/home/pi/img/"
#Path to the Dropbox-uploaded shell script
uploader = "/home/pi/Dropbox-Uploader/dropbox_uploader.sh"

#If 1 then files will be uploaded. Set to 0 for testing
upload = 1
#If 1 then don't check to see if the file already exists just upload it, if 0 don't upload if already exists
overwrite = 0
#If 1 then crawl sub directories for files to upload
recursive = 1
#Delete local file on successfull upload
deleteLocal = 1

isRunning = False


#Prints indented output
def print_output(msg, level):
    print((" " * level * 2) + msg)

def write_log(message):
    file_name = "dropbox_{}.log".format(datetime.now().isoformat()[:10])
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

#Gets a list of files in a dropbox directory
def list_files(path):
    p = Popen([uploader, "list", path], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output = p.communicate()[0].decode("utf-8")

    fileList = list()
    lines = output.splitlines()

    for line in lines:
        if line.startswith(" [F]"):
            line = line[5:]
            line = line[line.index(' ')+1:]
            fileList.append(line)

    return fileList

#Uploads a single file
def upload_file(localPath, remotePath):
    p = Popen([uploader, "upload", localPath, remotePath], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output = p.communicate()[0].decode("utf-8").strip()
    if output.startswith("> Uploading") and output.endswith("DONE"):
        return 1
    else:
        return 0

#Uploads files in a directory
def upload_files(path, level):
    fullpath = os.path.join(syncdir,path)
    print_output("Syncing " + fullpath,level)
    if not os.path.exists(fullpath):
        print_output("Path not found: " + path, level)
    else:

        #Get a list of file/dir in the path
        filesAndDirs = os.listdir(fullpath)

        #Group files and directories

        files = list()
        dirs = list()

        for file in filesAndDirs:
            filepath = os.path.join(fullpath,file)
            if os.path.isfile(filepath):
                files.append(file)
            if os.path.isdir(filepath):
                dirs.append(file)

        print_output(str(len(files)) + " Files, " + str(len(dirs)) + " Directories",level)

        #If the path contains files and we don't want to override get a list of files in dropbox
        if len(files) > 0 and overwrite == 0:
            dfiles = list_files(path)

        #Loop through the files to check to upload
        for f in files:
            print_output("Found File: " + f,level)
            if upload == 1 and (overwrite == 1 or not f in dfiles):
                fullFilePath = os.path.join(fullpath,f)
                relativeFilePath = os.path.join(path,f)
                print_output("Uploading File: " + f,level+1)
                if upload_file(fullFilePath, relativeFilePath) == 1:
                    print_output("Uploaded File: " + f,level + 1)
                    write_log('Uploaded File: ' + f)
                    if deleteLocal == 1:
                        print_output("Deleting File: " + f,level + 1)
                        write_log("Deleting File: " + f)
                        os.remove(fullFilePath)
                else:
                    print_output("Error Uploading File: " + f,level + 1)

        #If recursive loop through the directories
        if recursive == 1:
            for d in dirs:
                print_output("Found Directory: " + d, level)
                relativePath = os.path.join(path,d)
                upload_files(relativePath, level + 1)
    global isRunning
    isRunning = False



def main():
    global isRunning
    if (isRunning):
        print("Process is already running")
    else:
        isRunning = True
        write_log('Starting upload process to dropbox - {}'.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        upload_files("",1)



if __name__ == '__main__':
    try:
        write_log("piDropboxController started at {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        s = socket.socket()
        host = "" #socket.gethostname() #ip of raspberry pi
        port = 12146
        s.bind((host, port))

        s.listen(5)
        while True:
            c, addr = s.accept()
            print ('Got connection from',addr)
            write_log('Got connection from {} at {}'.format(addr, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            c.send(str.encode('Thank you for connecting'))
            c.close()
            # run command to take picture
            Process(target = main).start()
    except Exception as e:
        write_log(traceback.format_exc())
        print(traceback.format_exc())
    except KeyboardInterrupt:
        pass
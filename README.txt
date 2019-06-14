Program description:
Have a python script (doorController.py) continuiously run and listen for input from door switch.  Once opened it will log when it was opened and fire several functions without waiting for them. (aka fire them as a seperate process).
The functions are:
	check scale head for new data
	send command to cameras with predetermined ip address to take a picture and send picture to dropbox


-picamController.py
	Program to run on cameras.  It will start the camera preview and listen to port 12145. Once activity is heard it will trigger the camera to take a picture and same to /home/pi/img/

-piDropboxController.py
	Program to run on camera.  It will listen to port 12146.  Once activity is heard it will trigger the upload process.  If the upload process is already running it will do nothing.

TODO:
Edit files to make changes
In doorController.py update variable with list of remote computers' name
Default pin for doorController.py is 18

Copy *Controller.sh files for the scripts that you want to run on start up to the /etc/init.d/ directory.
Run the following commande for each file transfered
sudo chmod +x FILENAME
sudo update-rc.d FILENAME defaults

Reboot ~ sudo reboot

import os
import sys
import subprocess
from zipfile import ZipFile

os.system('sudo pigpiod')

import pigpio

switch = pigpio.pi()
switch.set_mode(17, pigpio.INPUT)
switch.set_pull_up_down(17, pigpio.PUD_UP)
led = pigpio.pi()

os.system("sudo chmod a+rwx -R /var/www/html/") # ensure web server can write to uploads folder for updates and logs

if switch.read(17) == 0: # need to start as Mini
    print ('Starting as eFinder Mini')
    subprocess.Popen(["venv-efinder/bin/python","Solver/eFinder_mini.py"])
    sys.exit(0)

reboot_flag = False
filename = '/home/efinder/uploads/efinderUpdate.zip'
runfile = '/home/efinder/uploads/update.py'

if os.path.isfile(filename):
	led.hardware_PWM(18,10,500000) # blink led very fast to indicate update in progress
	try:
		with ZipFile(filename, 'r') as file:
			print("Following files found to be installed/updated")
			file.printdir()
			print('Starting update')
			for name in file.namelist():
				file.extract(name,path="/")
				os.system('sudo chmod a+rwx /'+name)
				print (name, 'update written')
			os.system('sudo rm '+filename)
			print('All files updated and zip file deleted')
	except Exception as ex:
		print(f"An unexpected error occurred: {ex}")
		os.system('sudo rm '+filename) # remove the zip file to prevent repeated errors on reboot
	reboot_flag = True
	led.hardware_PWM(18,200,0) # turn off LED

if os.path.isfile(runfile):
	led.hardware_PWM(18,10,500000) # blink led very fast to indicate update in progress
	print('Running update script')
	try:
		subprocess.run(["/home/efinder/venv-efinder/bin/python",runfile])
		print('Update script completed successfully')
	except Exception as ex:
		print(f"An unexpected error occurred while running the update script: {ex}")
	os.system('sudo rm ' +runfile) # remove the update script to prevent repeated runs on reboot
	led.hardware_PWM(18,200,0) # turn off LED
	reboot_flag = True

if reboot_flag:
	os.system('sudo killall pigpiod')
	os.system('sudo reboot')

else:
	print('no zip file or update.py found')
	subprocess.Popen(["/home/efinder/venv-efinder/bin/python","/home/efinder/Solver/eFinder.py"])
	sys.exit(0)
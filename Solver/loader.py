import os
import sys
import subprocess
from zipfile import ZipFile

os.system('sudo pigpiod')

import pigpio

switch = pigpio.pi()
switch.set_mode(17, pigpio.INPUT)
switch.set_pull_up_down(17, pigpio.PUD_UP)

if switch.read(17) == 0: # need to start as Mini
    print ('Starting as eFinder Mini')
    subprocess.Popen(["venv-efinder/bin/python","Solver/eFinder_mini.py"])
    sys.exit(0)
    
filename = '/home/efinder/uploads/efinderUpdate.zip'

if os.path.isfile(filename): 
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
        os.system('sudo reboot now')
else:
    print('no zip file found')
    subprocess.Popen(["/home/efinder/venv-efinder/bin/python","/home/efinder/Solver/eFinder.py"])
    sys.exit(0)
#!/usr/bin/python3

# Program to implement an eFinder (electronic finder)
# Copyright (C) 2025 Keith Venables.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import os
import sys

os.system('sudo pigpiod')

import math
import RPi.GPIO as GPIO
import subprocess
import pigpio


switch = pigpio.pi()
switch.set_mode(18, pigpio.INPUT)
switch.set_pull_up_down(18, pigpio.PUD_UP)

led = pigpio.pi()
led.hardware_PWM(18,1,500000)

if switch.read(18) == 0: # need to restart as Mini
    print ('Restarting as eFinder Mini')
    subprocess.Popen(["venv-efinder/bin/python","Solver/eFinder_mini.py"])
    sys.exit(0)

global radec

if len(sys.argv) > 1:
    print ('Killing running version')
    os.system('pkill -9 -f eFinder.py') # stops the autostart eFinder program running
from pathlib import Path
home_path = str(Path.home())
param = dict()
if os.path.exists(home_path + "/Solver/eFinder.config") == True:
    with open(home_path + "/Solver/eFinder.config") as h:
        for line in h:
            line = line.strip("\n").split(":")
            param[line[0]] = str(line[1])

version = "8.5"
radec = ('%6.4f %+6.4f' % (0,0))

print ('Nexus eFinder','Version '+ version)
print ('Loading program')
import time
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps
import numpy as np
import NexusUsb_2
import RPICamera_Nexus_4
import servocat_usb
import tetra3
import csv
from io import BytesIO


try:
    import board
    import adafruit_adxl34x
    i2c = board.I2C()
    angle = adafruit_adxl34x.ADXL343(i2c)
    altAngle = True
    print('accelerometer found')
except:
    print('no acceleromater fitted')
    altAngle = False

expInc = 0.1 # sets how much exposure changes when using handpad adjust (seconds)
gainInc = 5 # ditto for gain
offset_flag = False
offset_str = "0,0"
solve = False
testMode = False
stars = peak = '0'
eTime = "9.9"
patch = np.zeros((32,32),dtype=np.uint8)
psfArray = np.zeros((32,32),dtype=np.uint8)
capArray = np.zeros((760,960),dtype=np.uint8)
auto = False
hotspot = False
hotspotSet = False
infraSet = False
fnt = ImageFont.truetype("/home/efinder/Solver/text.ttf",16)
frame = 0
keep = False
hemi = 'N'


def pixel2dxdy(pix_x, pix_y):  # converts a pixel position, into a delta angular offset from the image centre
    deg_x = (float(pix_x) - cam[0]/2) * cam[2] / 3600  # in degrees
    deg_y = (cam[1]/2 - float(pix_y)) * cam[2] / 3600
    return (deg_x, deg_y)

def dxdy2pixel(dx, dy): # converts offsets in arcseconds to pixel position
    pix_x = dx * 3600 / cam[2] + cam[0]/2
    pix_y = cam[1]/2 - dy * 3600 / cam[2]
    return (pix_x, pix_y)

def capture():
    global capArray
    if testMode == True:
        if offset_flag == False:
            test = True
            offset = False
        else:
            test = False
            offset = True
    else:
        test = False
        offset = False
    capArray = camera.capture(test,offset,hemi)
    return capArray


def solveImage(img):
    global offset_flag, solve, eTime, firstStar, solution, cam, stars, peak, radec
    start_time = time.time()
    print ("Started solving")

    np_image = np.asarray(img, dtype=np.uint8)
    centroids = tetra3.get_centroids_from_image(
        np_image,
        downsample=1,
        )   
    print ('centroids',len(centroids), '  peak',np.max(np_image))
    if len(centroids) < 15:
        print ("Bad image","only "+ str(len(centroids))," centroids")
        solve = False
        if keep:
            txt = "Bad image - " + str(len(centroids)) + " stars" + "    Exp = "+str(param['Exposure'])+ 's.   Gain = ' + str(param["Gain"])
            saveImage(img,txt)
        return
    stars = ('%4d' % (len(centroids)))
    peak = ('%3d' % (np.max(np_image)))
    solution = t3.solve_from_centroids(
                    centroids,
                    (760,960),
                    fov_estimate=cam[3],
                    fov_max_error=1,
                    target_pixel=offset,
                    return_matches=True,
                )
    elapsed_time = time.time() - start_time
    eTime = ('%2.2f' % (elapsed_time)).zfill(5)
    if solution['RA'] == None:
        print ("Not Solved",stars + " centroids", "")
        if keep:
            txt = "Not Solved - " + stars + " stars" + "    Exp = "+str(param['Exposure'])+ 's.   Gain = ' + str(param["Gain"])
            saveImage(img,txt)
        solve = False
        return
    firstStar = centroids[0]
    ra = solution['RA_target']
    dec = solution['Dec_target']
    radec = ('%6.4f %+6.4f' % (ra,dec))
    print ('RA,Dec',radec)
    if keep:
        txt = "Peak = "+ str(np.max(np_image)) + "   Stars = "+ str(int(centroids.size/2)) + "    Exp = "+str(param['Exposure'])+ 's.   Gain = ' + str(param["Gain"])
        saveImage(img,txt)
    solve = True
    
def measure_offset():
    global offset_str, offset_flag, offset, param
    offset_flag = True
    print ("started capture")
    solveImage(capture())
    if solve == False:
        print ("solve failed")
        return ("fail")
    tempExp = param['Exposure']
    while float(peak) > 255:
        tempExp = tempExp * 0.75
        camera.set(tempExp, param["Gain"])
        solveImage(capture())
    if solve == False:
        print ("solve failed")
        return ("fail")
    scope_x = firstStar[1]
    scope_y = firstStar[0]
    offset = firstStar
    d_x, d_y = pixel2dxdy(scope_x, scope_y)
    param["d_x"] = "{: .2f}".format(float(60 * d_x))
    param["d_y"] = "{: .2f}".format(float(60 * d_y))
    save_param()
    offset_str = ('%1.3f,%1.3f' % (d_x,d_y))
    hipId = str(solution['matched_catID'][0])
    name = secondname = ""
    with open(home_path+'/Solver/starnames.csv') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                nam = row[0].strip()
                hip = row[1]
                if str(row[1]) == str(solution['matched_catID'][0]):
                    hipId = hip
                    name = nam
                    if len(row[2].strip())==0:
                        secondname = ""
                    else:
                        secondname = " ("+row[2].strip()+")"
                    break       
    print (name + ', HIP ' + hipId)
    offset_flag = False
    return(name+secondname+',HIP'+hipId+','+offset_str)

def saveImage(array,txt):
    global frame, keep
    frame +=1
    #start = time.time()
    img = Image.fromarray(array)
    img2 = ImageEnhance.Contrast(img).enhance(5)
    img2 = img2.rotate(angle=180)
    img3 = ImageDraw.Draw(img2)
    txt = txt + "      Frame " + str(frame)
    #print(txt)
    img3.text((70,5), txt, font = fnt, fill='white')
    img2 = ImageOps.expand(img2,border=5,fill='red')
    img2 = img2.save('/home/efinder/Solver/images/capture.jpg')
    #print ('save %5.3f secs' % (time.time()-start))
    if frame > 99:
        keep = False
        frame = 0
        nexus.write(':IS0#')

def ctlSaveImage(f):
    global keep, frame
    if f == '1':
        keep = True
        return '1'
    else:
        keep = False
        frame = 0
        return "0"

def go_solve():
    solveImage(capture())
    if solve == True:
        print ("Solved", "", "")
        return('1')
    else:
        print ("Not Solved", "", "")
        return('0')

def reset_offset():
    global param, offset, offset_str
    param["d_x"] = 0
    param["d_y"] = 0
    offset = (cam[1]/2, cam[0]/2) # default centre of the image
    offset_str = ('%1.3f,%1.3f' % (float(param["d_x"])/60, float(param["d_y"])/60))
    save_param()
    return('1')
  

def save_param():
    with open(home_path + "/Solver/eFinder.config", "w") as h:
        for key, value in param.items():
            h.write("%s:%s\n" % (key, value))


def adjExp(i): #manual
    global param
    param['Exposure'] = ('%.1f' % (float(param['Exposure']) + i*expInc))
    if float(param['Exposure']) < 0:
        param['Exposure'] = '0.1'
    exp = ('%.1f' % float((param['Exposure'])))
    save_param()
    camera.set(float(param["Exposure"]),param["Gain"])
    return str(exp)

def adjGain(i): #manual
    global param
    param['Gain'] = ('%.1f' % (float(param['Gain']) + i*gainInc))
    if float(param['Gain']) < 0:
        param['Gain'] = '5'
    elif float(param['Gain']) > 50:
        param['Gain'] = '50'
    gain = ('%3.1f' % (float(param['Gain'])))
    camera.set(float(param["Exposure"]),param["Gain"])
    save_param()
    return str(gain)

def doFocus(x):
    global solve, patch, psfArray, peak, stars
    imgf = capture()
    np_image = np.asarray(imgf, dtype=np.uint8)
    img2 = Image.fromarray(np_image)
    img2 = ImageEnhance.Contrast(img2).enhance(5)
    img2 = ImageOps.expand(img2,border=5,fill='red')
    img2 = img2.save('/home/efinder/Solver/images/capture.jpg')
    centroids = tetra3.get_centroids_from_image(
        np_image,
        downsample=1,
        )
    if centroids.size < 1: 
        print ('No stars found','','')
        solve = False
        if x == 1:
            return('0')
        return
    stars = str(len(centroids))
    peak = ('%3d' % (np.max(np_image)))
    solve = True
    
    w=16
    x1=int(centroids[0][0]-w)
    if x1 < 0:
        x1 = 0
    x2=int(centroids[0][0]+w)
    if x2 > 760:
        x2 = 760
    y1=int(centroids[0][1]-w)
    if y1 < 0:
        y1 = 0
    y2=int(centroids[0][1]+w)
    if y2 > 960:
        y2 = 960

    patch = np_image[x1:x2,y1:y2] # 32x32 array of star
    print('patch',patch)

    img_supersample = Image.new("L",(32*8,32*8))
    shape=[]
    for h in range (x1,x2):
        shape.append(((h-x1)*8,int((255-np_image[h][y1+w]))))
    draw = ImageDraw.Draw(img_supersample)
    draw.line(shape,fill="white",width=8,joint="curve")
    shape=[]
    for h in range (y1,y2):
        shape.append(((h-y1)*8,int((255-np_image[x1+w][h]))))
    draw = ImageDraw.Draw(img_supersample)
    draw.line(shape,fill="white",width=8,joint="curve")

    psfPlot = img_supersample.resize((32, 32), Image.Resampling.LANCZOS)
    psfArray = np.asarray(psfPlot, dtype=np.uint8) # 32x32 PSF np.array
    print('PSF',psfArray)
    if x == 1:
        return('1')

def setExp(a):
    global param
    param["Exposure"] = float(a)
    save_param()
    camera.set(float(a),param["Gain"])
    return '1'

def getAutoExp():
    expAuto = float(param["Exposure"])
    camera.set(expAuto,param["Gain"])
    np_image = capture()
    while True:
        pk = np.max(np_image)
        centroids = tetra3.get_centroids_from_image(
            np_image,
            downsample=1,
            )
        print ('%4d %s   %3d %s ' % (len(centroids),"stars",pk,"peak signal"))

        if len(centroids) < 20:
            expAuto = expAuto * 2
            camera.set(expAuto,param["Gain"])
            capture()
        elif len(centroids) > 50 and pk > 250:
            expAuto = int((expAuto / 2) * 10)/10
            camera.set(expAuto,param["Gain"])
            capture()
        else:
            break
    return (str(expAuto))
            

def flipTestMode(mode,s):
    global testMode, hemi
    testMode = mode
    print('s',s)
    if s == 'TS#' or s == 'TSN#':
        hemi = 'N'
        print('North')
    elif s == 'TSS#':
        hemi = 'S'
        print('South')
    return('1')

def array_to_bytes(x: np.ndarray) -> bytes:
    np_bytes = BytesIO()
    np.save(np_bytes, x, allow_pickle=True)
    return np_bytes.getvalue()[128:]

def getScopeAlt():
    print('getting scope Alt')
    if altAngle:
        x,y,z = angle.acceleration
        print(x,y,z)
        if z > 0:
            print('below horizon')
            alt = '-1'    
        elif x > 0:
            print('over zenith')
            alt = '99'
        else:
            try:
                alt = -180/math.pi * math.asin(z/10)
            except:
                alt = 89
            alt = ('%2d' % (alt))
            print('scope alt',alt)   
    else:
        print ('No accelerometer')
        alt = '-2'
    return alt


def checkWifiCon(con):
    cmd = ['nmcli'] + ['con'] + ['show'] + ['--active']
    result = subprocess.run(cmd,capture_output=True,text=True)
    if con in str(result.stdout):
        return True
    else:
        return False
    
def checkWifi(con):
    cmd = ['nmcli'] + ['radio'] + ['wifi']
    result = subprocess.run(cmd,capture_output=True,text=True)
    if con in str(result.stdout):
        return True
    else:
        return False
    
def setWifi(msg):
    global hotspot
    if msg == "":
        if checkWifi('enabled'):
            reply = '1'
        else:
            reply = '0'
        if checkWifiCon('Hotspot'):
            reply = reply + '1'
        else:
            reply = reply + '0'
        return reply
    elif msg == "0":
        os.system('sudo nmcli conn up preconfigured')
        hotspot = False
        return '1'
    elif msg == '1':
        os.system('sudo nmcli con up Hotspot')
        hotspot = True
        return '1'
    else:
        return '0'

def wifiOnOff(msg):
    if msg == '0':
        os.system('sudo nmcli radio wifi off')
        print('wifi off')
    else:
        os.system('sudo nmcli radio wifi on')
        print('wifi on')
    return "1"
    
def configHotspotWifi(msg):
    global hotspot
    try:
        os.system("sudo nmcli con delete Hotspot")
    except:
        pass
    sid,pswd = msg.split(" ")
    ssid = 'efinder'+sid
    os.system("sudo nmcli dev wifi hotspot ssid '"+ ssid +"' password '" + pswd + "'")
    hotspot = True
    return '1'

def setLED(b):
    global param,led
    led_duty_cycle = int(b) * 10000
    led.hardware_PWM(18,200,led_duty_cycle)
    param["LED"] = int(b)
    save_param()
    return ('1')

# main code starts here

nexus = NexusUsb_2.Nexus()
camera = RPICamera_Nexus_4.RPICamera()
camera.set(float(param["Exposure"]),param["Gain"])
servocat = servocat_usb.ServoCat()

cam = (960,760,50.8,13.5)   
t3 = tetra3.Tetra3('t3_fov14_mag8')
print ('Done')

pix_x, pix_y = dxdy2pixel(float(param["d_x"])/60, float(param["d_y"])/60)
offset_str = ('%1.3f,%1.3f' % (float(param["d_x"])/60, float(param["d_y"])/60))

offset = (pix_y, pix_x) 
print('offset',offset)
np_image = np.zeros((760,960),dtype=np.uint8)

cmd = {
    "PS" : "nexus.write(':PS'+go_solve()+'#')",
    "OF" : "nexus.write(':OF'+measure_offset()+'#')",
    "FS" : "nexus.write(':FS'+doFocus(1)+'#')",
    "GP" : "nexus.writeBytes(':GP',array_to_bytes(psfArray))",
    "GI" : "nexus.writeBytes(':GI',array_to_bytes(patch))",
    "GR" : "nexus.write(':GR'+radec+'#')",
    "TS" : "nexus.write(':TS'+flipTestMode(True,msg[1:])+'#')",
    "TO" : "nexus.write(':TO'+flipTestMode(False,' ')+'#')",
    "GV" : "nexus.write(':GV'+version+'#')",
    "GO" : "nexus.write(':GO'+offset_str+'#')",
    "SO" : "nexus.write(':SO'+reset_offset()+'#')",
    "GS" : "nexus.write(':GS'+str(stars)+'#')",
    "GK" : "nexus.write(':GK'+str(peak)+'#')",
    "Gt" : "nexus.write(':Gt'+eTime+'#')",
    "SE" : "nexus.write(':SE'+adjExp(float(msg[3:5]))+'#')",
    "SG" : "nexus.write(':SG'+adjGain(float(msg[3:5]))+'#')",
    "SX" : "nexus.write(':SX'+setExp(msg.strip('#')[3:])+'#')",
    "GX" : "nexus.write(':GX'+getAutoExp()+'#')",
    "GA" : "nexus.write(':GA'+getScopeAlt()+'#')",
    "SB" : "nexus.write(':SB'+setLED(float(msg[3:].strip('#')))+'#')",
    "SW" : "nexus.write(':SW'+setWifi(msg.strip('#')[3:])+'#')",
    "SH" : "nexus.write(':SH'+configHotspotWifi(msg.strip('#')[3:])+'#')",
    "SI" : "nexus.write(':SI'+configInfraWifi(msg.strip('#')[3:])+'#')",
    "SQ" : "nexus.write(':SQ'+wifiOnOff(msg.strip('#')[3:])+'#')",
    "IS" : "nexus.write(':IS'+ctlSaveImage(msg.strip('#')[3:])+'#')"
}
led_duty_cycle = int(float(param["LED"])) * 10000
led.hardware_PWM(18,200,led_duty_cycle)


nexus.write(':ID=eFinderLite#')

while True:
    msg = nexus.scan()
    if msg != None:
        print ('received from Nexus',msg)
        if msg[1:3] == 'SC':
            pass
            servocat.write(msg[3:].strip('#'))
        else:
            try:
                exec(cmd[msg[1:3]])
            except Exception as error:
                nexus.write(':EF'+str(error)+'#')
                print ('Error',error) 
    
    sct = servocat.scan()
    if sct != None:
        print ('received from ServoCat',msg)
        nexus.write(':SC'+sct+'#')
    
    time.sleep(0.05) 
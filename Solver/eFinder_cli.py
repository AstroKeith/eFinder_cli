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
import RPi.GPIO as GPIO
import math

pinLED = 17
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)    
GPIO.setup(pinLED, GPIO.OUT)   
p = GPIO.PWM(pinLED,2)
p.start(50) # pulse LED while loading all the code.

if len(sys.argv) > 1:
    print ('Killing running version')
    os.system('pkill -9 -f eFinder_cli.py') # stops the autostart eFinder program running
from pathlib import Path
home_path = str(Path.home())
param = dict()
if os.path.exists(home_path + "/Solver/eFinder.config") == True:
    with open(home_path + "/Solver/eFinder.config") as h:
        for line in h:
            line = line.strip("\n").split(":")
            param[line[0]] = str(line[1])

version = "03_01"

print ('Nexus eFinder','Version '+ version)
print ('Loading program')
import time

from PIL import Image, ImageDraw, ImageEnhance

import numpy as np
import NexusUsb
from tetra3 import Tetra3
import tetra3
import csv
from io import BytesIO

try:
    import board
    import adafruit_adxl34x
    i2c = board.I2C()
    angle = adafruit_adxl34x.ADXL345(i2c)
    altAngle = True
    print('accelerometer found')
except:
    print('no acceleromater fitted')
    altAngle = False


x = y = 0  # x, y  define what page the display is showing
deltaAz = deltaAlt = 0
expInc = 0.1 # sets how much exposure changes when using handpad adjust (seconds)
gainInc = 5 # ditto for gain
offset_flag = False
offset_str = "0,0"
solve = False
testMode = False
stars = peak = '0'
patch = np.zeros((32,32),dtype=np.uint8)
psfArray = np.zeros((32,32),dtype=np.uint8)
auto = False

if len(sys.argv) > 1:
    os.system('pkill -9 -f eFinder_cli.py') # stops the autostart eFinder program running
try:
    os.mkdir("/var/tmp/solve")
except:
    pass

def pixel2dxdy(pix_x, pix_y):  # converts a pixel position, into a delta angular offset from the image centre
    deg_x = (float(pix_x) - cam[0]/2) * cam[2]/3600  # in degrees
    deg_y = (cam[1]/2 - float(pix_y)) * cam[2] / 3600
    dxstr = "{: .1f}".format(float(60 * deg_x))  # +ve if finder is left of main scope
    dystr = "{: .1f}".format(float(60 * deg_y))  # +ve if finder is looking below main scope
    return (deg_x, deg_y, dxstr, dystr)

def dxdy2pixel(dx, dy): # converts offsets in arcseconds to pixel position
    pix_x = dx * 3600 / cam[2] + cam[0]/2
    pix_y = cam[1]/2 - dy * 3600 / cam[2]
    dxstr = "{: .1f}".format(float(60 * dx))  # +ve if finder is left of main scope
    dystr = "{: .1f}".format(float(60 * dy))  # +ve if finder is looking below main scope
    return (pix_x, pix_y, dxstr, dystr)

def capture(exp ):
    if testMode == True:
        if offset_flag == False:
            m13 = True
            polaris_cap = False
        else:
            m13 = False
            polaris_cap = True
    else:
        m13 = False
        polaris_cap = False
    camera.capture(
        int(exp * 1000000),
        int(float(param["Gain"])),
        m13,
        polaris_cap,
        destPath,
    )


def solveImage():
    global offset_flag, solve, solvedPos, eTime, solved_radec, solved_altaz, firstStar, solution, cam, stars, peak, radec
    start_time = time.time()
    print ("Started solving", "", "")
    captureFile = destPath + "capture.png"
    with Image.open(captureFile).convert('L') as img:
        np_image = np.asarray(img, dtype=np.uint8)
        centroids = tetra3.get_centroids_from_image(
            np_image,
            downsample=1,
            )
        
        print ('centroids',len(centroids))
        print ('peak',np.max(np_image))
        if len(centroids) < 15:
            print ("Bad image","only "+ str(len(centroids))," centroids")
            solve = False
            time.sleep(3)
            return
        stars = ('%4d' % (len(centroids)))
        peak = ('%3d' % (np.max(np_image)))
        
        solution = t3.solve_from_centroids(
                        centroids,
                        (img.size[1],img.size[0]),
                        fov_estimate=cam[3],
                        fov_max_error=1,
                        match_max_error=0.002,
                        target_pixel=offset,
                        return_matches=True,
                    )
        elapsed_time = time.time() - start_time
        eTime = ('%2.2f' % (elapsed_time)).zfill(5)
    if solution['RA'] == None:
        print ("Not Solved",stars + " centroids", "")
        solve = False
        return
    firstStar = centroids[0]
    ra = solution['RA_target']
    dec = solution['Dec_target']
    radec = ('%6.4f %+6.4f#' % (ra/15,dec))
    solve = True

    
def measure_offset():
    global offset_str, offset_flag, offset, param
    offset_flag = True
    print ("started capture")
    capture(float(param['Exposure']))
    solveImage()
    if solve == False:
        print ("solve failed")
        nexus.write('0#')
        return
    tempExp = param['Exposure']
    while float(peak) > 255:
        tempExp = tempExp * 0.75
        capture(tempExp)
        solveImage()

    if solve == False:
        print ("solve failed")
        nexus.write('0#')
        return

    scope_x = firstStar[1]
    scope_y = firstStar[0]
    offset = firstStar
    d_x, d_y, dxstr, dystr = pixel2dxdy(scope_x, scope_y)
    param["d_x"] = "{: .2f}".format(float(60 * d_x))
    param["d_y"] = "{: .2f}".format(float(60 * d_y))
    save_param()
    offset_str = ('%1.3f,%1.3f' % (d_x,d_y))

    hipId = str(solution['matched_catID'][0])
    name = ""
    with open(home_path+'/Solver/starnames.csv') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                nam = row[0].strip()
                hip = row[1]
                if str(row[1]) == str(solution['matched_catID'][0]):
                    hipId = hip
                    name = nam
                    break       
    print (name + ', HIP ' + hipId)
    offset_flag = False
    return(name+',HIP'+hipId+','+offset_str)

def go_solve():
    capture(float(param['Exposure']))
    solveImage()
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
    offset = (cam[0]/2, cam[1]/2) # default centre of the image
    offset_str = ('%1.3f,%1.3f' % (float(param["d_x"])/60, float(param["d_y"])/60))
    save_param()
    return('1')

def get_param():
    global param
    if os.path.exists(home_path + "/Solver/eFinder.config") == True:
        with open(home_path + "/Solver/eFinder.config") as h:
            for line in h:
                line = line.strip("\n").split(":")
                param[line[0]] = str(line[1])
                

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
    return str(exp)

def adjGain(i): #manual
    global param
    param['Gain'] = ('%.1f' % (float(param['Gain']) + i*gainInc))
    if float(param['Gain']) < 0:
        param['Gain'] = '5'
    elif float(param['Gain']) > 50:
        param['Gain'] = '50'
    gain = ('%3.1f' % (float(param['Gain'])))
    save_param
    return str(gain)

def loopFocus(x):
    global solve, patch, psfArray, peak, stars
    capture(float(param['Exposure']))
    with Image.open("/var/tmp/solve/capture.png") as img:
        img = img.convert(mode='L')
        np_image = np.asarray(img, dtype=np.uint8)
        pk = np.max(np_image)
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
        if x2 > img.size[1]:
            x2 = img.size[1]
        y1=int(centroids[0][1]-w)
        if y1 < 0:
            y1 = 0
        y2=int(centroids[0][1]+w)
        if y2 > img.size[0]:
            y2 = img.size[0]

        patch = np_image[x1:x2,y1:y2] # 32x32 array of star
        print('patch',patch)

        psfPlot = Image.new("1",(32,32))
        shape=[]
        for h in range (x1,x2):
            shape.append(((h-x1),int((255-np_image[h][y1+w])/8)))
        draw = ImageDraw.Draw(psfPlot)
        draw.line(shape,fill="white",width=1)
        shape=[]
        for h in range (y1,y2):
            shape.append(((h-y1),int((255-np_image[x1+w][h])/8)))
        draw = ImageDraw.Draw(psfPlot)
        draw.line(shape,fill="white",width=1)

        psfArray = np.asarray(psfPlot, dtype=np.uint8) # 32x32 PSF np.array
        print('PSF',psfArray)
        if x == 1:
            return('1')
    
def setExp(a):
    global param
    param["Exposure"] = float(a)
    save_param()
    return '1'

def getAutoExp():
    expAuto = float(param["Exposure"])
    capture(expAuto)
    while True:
        with Image.open("/var/tmp/solve/capture.png") as img:
            img = img.convert(mode='L')
            np_image = np.asarray(img, dtype=np.uint8)
            pk = np.max(np_image)
            centroids = tetra3.get_centroids_from_image(
                np_image,
                downsample=1,
                )
            print ('%4d %s   %3d %s ' % (len(centroids),"stars",pk,"peak signal"))

            if len(centroids) < 20:
                expAuto = expAuto * 2
                capture(expAuto)
            elif len(centroids) > 50 and pk > 250:
                expAuto = int((expAuto / 2) * 10)/10
                capture(expAuto)
            else:
                break
    return (str(expAuto))
            

def flipTestMode(mode):
    global cam, t3, testMode
    if mode == True:
        cam = Testcam
        t3 = Tetra3('t3_fov14_mag8')
        testMode = True
        return('1')
    else:
        testMode = False
        cam = camCam
        t3 = Tetra3(dataBase)
        return('0')

def array_to_bytes(x: np.ndarray) -> bytes:
    np_bytes = BytesIO()
    np.save(np_bytes, x, allow_pickle=True)
    return np_bytes.getvalue()


def bytes_to_array(b: bytes) -> np.ndarray:
    np_bytes = BytesIO(b)
    return np.load(np_bytes, allow_pickle=True)

def loopImage():
    loopFocus(0)
    nexus.writeBytes(array_to_bytes(patch))

def loopPsf():
    loopFocus(0)
    nexus.writeBytes(array_to_bytes(psfArray))

def setLED(b):
    global p, param
    p.stop()
    p = GPIO.PWM(pinLED,100)
    p.start(int(b))
    param["LED"] = int(b)
    save_param()
    return ('1')

def getScopeAlt():
    print('getting scope Alt')
    if altAngle:
        x,y,z = angle.acceleration
        if z < 0:
            print('below horizon')
            alt = '-1'
    
        elif x > 0:
            print('over zenith')
            alt = '99'

        else:
            try:
                alt = 180/math.pi * math.asin(z/11.5)
            except:
                alt = 89
            alt = ('%2d' % (alt))
            print('scope alt',alt)
      
    else:
        print ('No accelerometer')
        alt = '-2'
    return alt

def getImage(msg):
    global np_image
    n = int(float(msg[3:]))
    
    if n == 0:
        x,y,a,b = dxdy2pixel(float(param["d_x"])/60,float(param["d_y"])/60)
        print('offset in pixels',x,y)
        try:
            with Image.open("/var/tmp/solve/capture.png") as img:
                img = img.convert(mode='L')
                img = ImageEnhance.Contrast(img).enhance(5)
                draw = ImageDraw.Draw(img)
                draw.ellipse(
                    [x - 15,y - 15,x + 15,y + 15],
                    fill=None,
                    outline=255,
                    width=1,
                )
                img = img.rotate(180)
                np_image = np.asarray(img, dtype=np.uint8)
        except:
            print ('no image saved yet')
    h,w = np.shape(np_image)
    block = np_image[n:n+4,0:w]
    return block

def getCrop(x,y):
    xl = x - 128
    xr = x + 128
    yu = y - 128
    yl = y + 128
    if xl < 0:
        xl = 0
        xr = 256
    elif xr > 960:
        xl = 960 - 256
        xr = 960
    if yu < 0:
        yu = 0
        yl = 256
    elif yl > 760:
        yu = 760 - 256
        yl = 760
    box = (xl,yu,xr,yl)
    return box

def getCropImage(msg):
    global np_image
    n = int(float(msg[3:]))
    
    if n == 0:
        x,y,a,b = dxdy2pixel(float(param["d_x"])/60,float(param["d_y"])/60)
        print('offset in pixels',x,y)
        box = getCrop(int(x),int(y))
        print ('box',box)
        try:
            with Image.open("/var/tmp/solve/capture.png") as img:
                img = img.convert(mode='L')
                img = ImageEnhance.Contrast(img).enhance(10)
                draw = ImageDraw.Draw(img)
                draw.ellipse(
                    [x - 10,y - 10,x + 10,y + 10],
                    fill=None,
                    outline=255,
                    width=1,
                )
                img = img.crop(box)
                img = img.rotate(180)
                np_image = np.asarray(img, dtype=np.uint8)
        except:
            print ('no image saved yet')
    h,w = np.shape(np_image)
    block = np_image[n:n+8,0:w]
    return block

# main code starts here

nexus = NexusUsb.Nexus()

if param["Camera"]=='ASI':
    import ASICamera_Nexus
    camera = ASICamera_Nexus.ASICamera()
    if param["Lens_focal_length"] == '50':
        dataBase = 't3_fov5_mag8'
        camCam = (1280,960,15.4,5.5) # width pixels,height pixels,pixel scale, width field of view
    elif param["Lens_focal_length"] == '25':
        dataBase = 't3_fov11_mag8'
        camCam = (1280,960,30.8,11)
elif param["Camera"]=='RPI':
    import RPICamera_Nexus
    camera = RPICamera_Nexus.RPICamera()
    if param["Lens_focal_length"] == '50':
        dataBase = 't3_fov7_mag8'
        camCam = (960,760,25.4,6.8)
    elif param["Lens_focal_length"] == '25':
        pass
dataBase = 't3_fov14_mag8'
camCam = (960,760,50.8,13.5)   

Testcam = (960,760,50.8,13.5)
print ('Please wait','loading Tetra3','database')

cam = camCam
t3 = Tetra3(dataBase)
print ('Done','','')

pix_x, pix_y, dxstr, dystr = dxdy2pixel(float(param["d_x"])/60, float(param["d_y"])/60)
offset_str = ('%1.3f,%1.3f' % (float(param["d_x"])/60, float(param["d_y"])/60))

offset = (pix_y, pix_x) 
print(offset)
np_image = np.zeros((760,960),dtype=np.uint8)
destPath = "/var/tmp/solve/"

flipTestMode(True)
go_solve()
flipTestMode(False)

cmd = {
    "PS" : "nexus.write('PS'+go_solve()+'#')",
    "OF" : "nexus.write('OF'+measure_offset()+'#')",
    "FS" : "nexus.write('FS'+loopFocus(1)+'#')",
    "GP" : "nexus.writeBytes(array_to_bytes(psfArray))",
    "GI" : "nexus.writeBytes(array_to_bytes(patch))",
    "GR" : "nexus.write('GR'+radec)",
    "TS" : "nexus.write('TS'+flipTestMode(True)+'#')",
    "TO" : "nexus.write('TO'+flipTestMode(False)+'#')",
    "GV" : "nexus.write('GV'+version)",
    "GO" : "nexus.write('GO'+offset_str+'#')",
    "SO" : "nexus.write('SO'+reset_offset()+'#')",
    "GS" : "nexus.write('GS'+str(stars)+'#')",
    "GK" : "nexus.write('GK'+str(peak)+'#')",
    "Gt" : "nexus.write('Gt'+eTime+'#')",
    "SE" : "nexus.write('SE'+adjExp(float(msg[3:5]))+'#')",
    "SG" : "nexus.write('SG'+adjGain(float(msg[3:5]))+'#')",
    "SX" : "nexus.write('SX'+setExp(msg.strip('#')[3:])+'#')",
    "GX" : "nexus.write('GX'+getAutoExp()+'#')",
    "LI" : "loopImage()",
    "LP" : "loopPsf()",
    "SB" : "nexus.write('SB'+setLED(float(msg[3:5]))+'#')",
    "GA" : "nexus.write('GA'+getScopeAlt()+'#')",
    "GZ" : "nexus.writeBytes(array_to_bytes(getImage(msg.strip('#'))))",
    "Gz" : "nexus.writeBytes(array_to_bytes(getCropImage(msg.strip('#'))))"
}
p.stop()
p = GPIO.PWM(pinLED,100)
p.start(int(float(param["LED"])))
nexus.write('ID=eFinder')

while True:
    msg = nexus.scan()
    if msg != None:
        print ('received',msg)
        try:
            exec(cmd[msg[1:3]])
        except Exception as error:
            nexus.write('Error')
            print ('Error',error) 
    time.sleep(0.05) 
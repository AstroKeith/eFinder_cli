#!/usr/bin/python3

# Program to implement an eFinder (electronic finder)
# Copyright (C) 2024 Keith Venables.
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
if len(sys.argv) > 1:
    print ('Killing running version')
    os.system('pkill -9 -f eFinder_Nexus.py') # stops the autostart eFinder program running
from pathlib import Path
home_path = str(Path.home())
param = dict()
if os.path.exists(home_path + "/Solver/eFinder.config") == True:
    with open(home_path + "/Solver/eFinder.config") as h:
        for line in h:
            line = line.strip("\n").split(":")
            param[line[0]] = str(line[1])

version = "NexusLite_1_1"

print ('Nexus eFinder','Version '+ version)
import time

from PIL import Image, ImageDraw

from skyfield.api import Star
import numpy as np
import Nexus_Usb
import Coordinates_Lite
from tetra3 import Tetra3, cedar_detect_client
cedar_detect = cedar_detect_client.CedarDetectClient()
import tetra3
import csv

print ('ScopeDog eFinder','Lite','Loading program')
x = y = 0  # x, y  define what page the display is showing
deltaAz = deltaAlt = 0
expInc = 0.1 # sets how much exposure changes when using handpad adjust (seconds)
gainInc = 5 # ditto for gain
offset_flag = False
offset_str = "0,0"
solve = False
testMode = False
stars = peak = 0

if len(sys.argv) > 1:
    os.system('pkill -9 -f eFinder_cli.py') # stops the autostart eFinder program running
try:
    os.mkdir("/var/tmp/solve")
except:
    pass

def pixel2dxdy(pix_x, pix_y):  # converts a pixel position, into a delta angular offset from the image centre
    global cam
    deg_x = (float(pix_x) - cam[0]/2) * cam[2]/3600  # in degrees
    deg_y = (cam[1]/2 - float(pix_y)) * cam[2] / 3600
    dxstr = "{: .1f}".format(float(60 * deg_x))  # +ve if finder is left of main scope
    dystr = "{: .1f}".format(float(60 * deg_y))  # +ve if finder is looking below main scope
    return (deg_x, deg_y, dxstr, dystr)

def dxdy2pixel(dx, dy): # converts offsets in arcseconds to pixel position
    global cam
    pix_x = dx * 3600 / cam[2] + cam[0]/2
    pix_y = cam[1]/2 - dy * 3600 / cam[2]
    dxstr = "{: .1f}".format(float(60 * dx))  # +ve if finder is left of main scope
    dystr = "{: .1f}".format(float(60 * dy))  # +ve if finder is looking below main scope
    return (pix_x, pix_y, dxstr, dystr)


def capture():
    global param
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
        int(float(param["Exposure"]) * 1000000),
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
        centroids = cedar_detect.extract_centroids(
            img,
            max_size=10,
            sigma=8,
            use_binned=False,
            )

        if len(centroids) < 30:
            print ("Bad image","only"+ stars," centroids")
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
        eTime = ('%2.2f' % (elapsed_time))
    if solution['RA'] == None:
        print ("Not Solved",stars + " centroids", "")
        solve = False
        return
    firstStar = centroids[0]
    ra = solution['RA_target']
    dec = solution['Dec_target']
    solved = Star(
        ra_hours=ra / 15, dec_degrees=dec
    )  # will set as J2000 as no epoch input
    solvedPos = (
        nexus.get_location().at(coordinates.get_ts().now()).observe(solved)
    )  # now at Jnow and current location

    ra, dec, d = solvedPos.apparent().radec(coordinates.get_ts().now())
    solved_radec = ra.hours, dec.degrees
    solved_altaz = coordinates.conv_altaz(nexus, *(solved_radec))
    radec = ('g%5.3f %+5.3f#' % (solved_radec[0],solved_radec[1]))
    solve = True
   

def measure_offset():
    global offset_str, offset_flag, offset, param, scope_x, scope_y, firstStar
    offset_flag = True
    print ("started capture", "", "")
    capture()
    solveImage()
    if solve == False:
        print ("solve failed", "", "")
        return
    scope_x = firstStar[1]
    scope_y = firstStar[0]
    offset = firstStar
    d_x, d_y, dxstr, dystr = pixel2dxdy(scope_x, scope_y)
    param["d_x"] = "{: .2f}".format(float(60 * d_x))
    param["d_y"] = "{: .2f}".format(float(60 * d_y))
    save_param()
    offset_str = ('%1.4f,%1.4f' % (d_x,d_y))

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

def go_solve():
    global x, y, solve

    print ("Image capture", "", "")
    capture()

    print ("Plate solving", "", "")
    solveImage()
    if solve == True:
        print ("Solved", "", "")
    else:
        print ("Not Solved", "", "")
        return



def reset_offset():
    global param, arr, offset
    param["d_x"] = 0
    param["d_y"] = 0
    offset = (cam[0]/2, cam[1]/2) # default centre of the image
    save_param()

def get_param():
    global param, offset_str, pix_scale
    if os.path.exists(home_path + "/Solver/eFinder.config") == True:
        with open(home_path + "/Solver/eFinder.config") as h:
            for line in h:
                line = line.strip("\n").split(":")
                param[line[0]] = str(line[1])
                


def save_param():
    global param, cam, Testcam, camCam, dataBase, t3
    with open(home_path + "/Solver/eFinder.config", "w") as h:
        for key, value in param.items():
            h.write("%s:%s\n" % (key, value))



def adjExposure(pk): # auto
    global param
    if pk > 250:
        param['Exposure'] = (int(10 * (float(param['Exposure'])/2)))/10
    elif pk < 200:
        param['Exposure'] = (int(10*(float(param['Exposure']) * 225/pk)))/10


def adjExp(i): #manual
    global param
    param['Exposure'] = ('%.1f' % (float(param['Exposure']) + i*expInc))
    if float(param['Exposure']) < 0:
        param['Exposure'] = '0.1'
    exp = ('%3.1f' % float((param['Exposure'])))
    return str(exp)

def adjGain(i): #manual
    global param
    param['Gain'] = ('%.1f' % (float(param['Gain']) + i*gainInc))
    if float(param['Gain']) < 0:
        param['Gain'] = '5'
    elif float(param['Gain']) > 50:
        param['Gain'] = '50'
    gain = ('%3.1f' % (float(param['Gain'])))
    return str(gain)

def loopFocus(auto):
    global solve
    capture()
    with Image.open("/var/tmp/solve/capture.png") as img:
        img = img.convert(mode='L')
        np_image = np.asarray(img, dtype=np.uint8)
        pk = np.max(np_image)
        if auto == 1 and (pk < 200 or pk > 250):
            adjExposure(pk)
            print ('Adjusting Exposure','trying',str(param['Exposure']) + ' sec')
            loopFocus(1)
        elif auto == 1 and (200 <= pk <= 250):
            print ('Exposure OK','','')
        centroids = tetra3.get_centroids_from_image(
            np_image,
            downsample=1,
            )
        if centroids.size < 1: 
            print ('No stars found','','')
            solve = False
            return
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

        psfArray = np.asarray(psfPlot, dtype=np.uint8) # 32x32 PSF array
        print('PSF',psfArray)
        

def flipTestMode(mode):
    global cam, t3, testMode
    if mode == True:
        cam = Testcam
        t3 = Tetra3('t3_fov14_mag8')
        testMode = True
    else:
        testMode = False
        cam = camCam
        t3 = Tetra3(dataBase)


# main code starts here

coordinates = Coordinates_Lite.Coordinates()
nexus = Nexus_Usb.Nexus(coordinates)
nexus.read()

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
offset_str = ('%1.4f,%1.4f' % (float(param["d_x"])/60, float(param["d_y"])/60))

offset = (pix_y, pix_x) 
print(offset)

destPath = "/var/tmp/solve/"

while True:
    msg = nexus.scan()
    if msg != None:
        print ('received',msg)
        if msg == ':PS#':
            go_solve()
            if solve == True:
                nexus.write('1')
            else:
                nexus.write('0')
        elif msg == ':OF#':
            measure_offset()
            if solve == True:
                nexus.write('1')
            else:
                nexus.write('0')
        elif msg == ':FS#':
            loopFocus(0)
            if solve == True:
                nexus.write('1')
            else:
                nexus.write('0')
        elif msg == ':GR#':
            nexus.write(radec)
        elif msg == ':TS#':
            flipTestMode(True)
            nexus.write('1')
        elif msg == ':TO#':
            flipTestMode(False)
            nexus.write('0')
        elif msg == ':GV#':
            nexus.write(version)
        elif msg == ':GO#':
            nexus.write(offset_str)
        elif msg == ':SO#':
            reset_offset()
            nexus.write('1')
        elif msg == ':GS#':
            nexus.write(str(stars))
        elif msg == ':GK#':
            nexus.write(str(peak))
        elif msg == ':Gt#':
            nexus.write(eTime)
        elif msg[1:3] == 'SE':
            value = adjExp(float(msg[3:5]))
            nexus.write(value)
        elif msg[1:3] == 'SG':
            value = adjGain(float(msg[3:5]))
            nexus.write(value)
        else:
            nexus.write('bad command')
    time.sleep(0.1) 
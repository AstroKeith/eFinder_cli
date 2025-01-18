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

from PIL import Image, ImageDraw, ImageEnhance

from skyfield.api import Star
import numpy as np
import Nexus_Lite
import Coordinates_Lite
import select
from tetra3 import Tetra3, cedar_detect_client
cedar_detect = cedar_detect_client.CedarDetectClient()
import tetra3
import csv
import serial

print ('ScopeDog eFinder','Lite','Loading program')
x = y = 0  # x, y  define what page the display is showing
deltaAz = deltaAlt = 0
expInc = 0.1 # sets how much exposure changes when using handpad adjust (seconds)
gainInc = 5 # ditto for gain
offset_flag = False
solve = False

if len(sys.argv) > 1:
    os.system('pkill -9 -f eFinder_Lite.py') # stops the autostart eFinder program running
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
    if param["Test_mode"] == "1" or param["Test_mode"] == "True":
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
    global offset_flag, solve, solvedPos, elapsed_time, solved_radec, solved_altaz, firstStar, solution, cam, stars

    start_time = time.time()
    print ("Started solving", "", "")
    captureFile = destPath + "capture.png"
    with Image.open(captureFile).convert('L') as img:
        centroids = cedar_detect.extract_centroids(
            img,
            max_size=10,
            sigma=8,
            use_binned=False,
            )
        stars = str(len(centroids))
        if len(centroids) < 30:
            print ("Bad image","only"+ stars," centroids")
            solve = False
            time.sleep(3)
            return
        solution = t3.solve_from_centroids(
                        centroids,
                        (img.size[1],img.size[0]),
                        fov_estimate=cam[3],
                        fov_max_error=1,
                        match_max_error=0.002,
                        target_pixel=offset,
                        return_matches=True,
                    )
        elapsed_time = str(time.time() - start_time)[0:3]

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
    offset_str = dxstr + "," + dystr

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


def loopFocus(auto):
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
            time.sleep(3)
            return
        
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

        

        patch = np_image[x1:x2,y1:y2]
        imp = Image.fromarray(np.uint8(patch),'L')
        imp = imp.resize((32,32),Image.LANCZOS)
        im = imp.convert(mode='1')

        imgPlot = Image.new("1",(32,32))
        shape=[]

        for h in range (x1,x2):
            shape.append(((h-x1),int((255-np_image[h][y1+w])/8)))
        draw = ImageDraw.Draw(imgPlot)
        draw.line(shape,fill="white",width=1)

        shape=[]

        for h in range (y1,y2):
            shape.append(((h-y1),int((255-np_image[x1+w][h])/8)))

        draw = ImageDraw.Draw(imgPlot)
        draw.line(shape,fill="white",width=1)

        txtPlot = Image.new("1",(50,32))
        txt = ImageDraw.Draw(txtPlot)
        txt.text((0,0),"Pk="+ str(np.max(np_image)),font = fnt,fill='white')
        txt.text((0,10),"No="+ str(int(centroids.size/2)),font = fnt,fill='white')
        txt.text((0,20),"Ex="+str(param['Exposure']),font = fnt,fill='white')
        screen = Image.new("1",(128,32))
        screen.paste(im,box=(0,0))
        screen.paste(txtPlot,box=(35,0))
        screen.paste(imgPlot,box=(80,0))
        # create image for saving
        img = ImageEnhance.Contrast(img).enhance(5)
        combo = ImageDraw.Draw(img)
        combo.rectangle((0,0,65,65),outline='white',width=2)
        combo.rectangle((0,0,img.size[0],img.size[1]),outline='white',width=2)
        combo.text((70,5),"Peak = "+ str(np.max(np_image)) + "   Number of centroids = "+ str(int(centroids.size/2)) + "    Exposure = "+str(param['Exposure'])+ 'secs',font = fnt,fill='white')
        imp = imp.resize((64,64),Image.LANCZOS)
        imp = ImageEnhance.Contrast(imp).enhance(5)
        img.paste(imp,box=(1,1))
        img.save('/home/efinder/Solver/images/image.png')

    # need to send handpad.dispFocus(screen)

def doTestSolve():
    global cam, t3
    cam = Testcam
    t3 = Tetra3('t3_fov14_mag8')
    # now do a solve and reply

    cam = camCam
    t3 = Tetra3(dataBase)


# main code starts here

coordinates = Coordinates_Lite.Coordinates()
nexus = Nexus_Lite.Nexus(coordinates)
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
        dataBase = 't3_fov14_mag8'
        camCam = (960,760,50.8,13.5)   

Testcam = (960,760,50.8,13.5)
print ('Please wait','loading Tetra3','database')

cam = camCam
t3 = Tetra3(dataBase)
print ('Done','','')

pix_x, pix_y, dxstr, dystr = dxdy2pixel(float(param["d_x"])/60, float(param["d_y"])/60)
offset_str = dxstr + "," + dystr

offset = (pix_y, pix_x) 
print(offset)

destPath = "/var/tmp/solve/"

while True:
    if nexus.get_usb() in select.select([nexus.get_usb], [], [], 0)[0]:
        msg = nexus.get_usb.readline().decode("ascii").strip("\r\n")
        # need to parse msg and call function as required
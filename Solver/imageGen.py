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
import socket
from threading import Thread
import pigpio

led = pigpio.pi()
led.hardware_PWM(18,4,500000)

switch = pigpio.pi()
switch.set_mode(17, pigpio.INPUT)
switch.set_pull_up_down(17, pigpio.PUD_UP)

global radec

if len(sys.argv) > 1:
    print ('Killing running version')
    os.system('pkill -9 -f eFinder.py') # stops the autostart eFinder program running
from pathlib import Path
home_path = str(Path.home())
param = dict()
if os.path.exists("Solver/eFinder.config") == True:
    print('file exists')
    with open("Solver/eFinder.config") as h:
        for line in h:
            line = line.strip("\n").split(":")
            print (line)
            param[line[0]] = str(line[1])

version = "1.0"
radec = ('%6.4f %+6.4f' % (0,0))

print ('eFinder ImageGen','Version '+ version)
print ('Loading program')
import time
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps
import numpy as np
import NexusUsb_2
import RPICamera_High_Res

import csv
from io import BytesIO
import subprocess


print('no acceleromater fitted')
altAngle = False

expInc = 0.1 # sets how much exposure changes when using handpad adjust (seconds)
gainInc = 5 # ditto for gain

capArray = np.zeros((760,960),dtype=np.uint8)
hotspot = False

fnt = ImageFont.truetype("/home/efinder/Solver/text.ttf",16)
frame = 0

def serveWifi(): # serve WiFi port
    global solved_radec, addr, param, keep, frame
    print ('starting wifi server')
    host = ''
    port = 4060
    backlog = 50
    size = 1024
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host,port))
    s.listen(backlog)
    raStr = decStr = ""
    timeOffset = '0'
    timeStr = '23:00:00'
    try:
        while True:
            client, address = s.accept()
            while True:
                data = client.recv(size)
                if not data:
                    break
                if data:
                    pkt = data.decode("utf-8","ignore")
                    time.sleep(0.02)
                    a = pkt.split('#')
                    print(a)
                    raPacket = coordinates.hh2dms(solved_radec[0]/15)+'#'
                    decPacket = coordinates.dd2aligndms(solved_radec[1])+'#'
                    for x in a:
                        if x != '':
                            #print (x)
                            if x == ':GR':
                                client.send(bytes(raPacket.encode('ascii')))
                            elif x == ':GD':
                                client.send(bytes(decPacket.encode('ascii')))
                            elif x[1:3] == 'St':
                                client.send(b'1')
                                Lat = x[3:].split('*')
                                Lat = int(Lat[0]) + int(Lat[1])/60 # Latitude as decimal degrees North +Ve
                            elif x[1:3] == 'Sg':
                                client.send(b'1')
                                Long = x[3:].split('*')
                                Long = int(Long[0]) + int(Long[1])/60 # Longitude as decimal degrees West +ve
                            elif x[1:3] == 'SG':
                                client.send(b'1')
                                timeOffset = x[3:]
                            elif x[1:3] == 'SL':
                                client.send(b'1')
                                timeStr = x[3:]
                            elif x[1:3] == 'SC':
                                client.send(b'Updating Planetary Data#                              #')
                                print('dateSet',timeOffset,timeStr,x[3:])
                                coordinates.dateSet(timeOffset,timeStr,x[3:])
                            elif x[1:3] == 'RG': # set minimum exp/gain
                                selectExp(0.1,10)
                            elif x[1:3] == 'RC': # set med exp/gain
                                selectExp(0.1,20)
                            elif x[1:3] == 'RM': # set high exp/gain
                                selectExp(0.2,20)
                            elif x[1:3] == 'RS': # set very high exp/gain
                                selectExp(0.5,30)
                            elif x[1:3] == 'Sr': # target RA
                                raStr = x[3:]
                                client.send(b'1')
                            elif x[1:3] == 'Sd': # target Dec
                                decStr = x[3:]
                                client.send(b'1')  
                            elif x[1:3] == 'MS': # 'goto' aka start saving images
                                client.send(b'0')
                            elif x[1:3] == 'Ms':
                                adjExp(-1)
                            elif x[1:3] == 'Mn':
                                adjExp(1)
                            elif x[1:3] == 'Mw':
                                keep = False
                                frame = 0
                            elif x[1:3] == 'Me':
                                print('Started saving images')
                                keep = True
                            elif x[1:3] == 'CM': # do offset
                                client.send(b'0')
                                measure_offset()
                                ra = raStr.split(':')
                                targetRa = int(ra[0])+int(ra[1])/60+int(ra[2])/3600
                                dec = decStr.split('*')
                                decdec = dec[1].split(':')
                                targetDec = int(dec[0]) + math.copysign((int(decdec[0])/60+int(decdec[1])/3600),float(dec[0]))
                                print('Align target received:',targetRa, targetDec) # decimal hours and degrees
                            elif x[-1] == 'Q':
                                print('Stop saving images')
                                keep = False
                                frame = 0
    except:
        pass


def selectExp(e,g):
    camera.set(e,g)
    param['Exposure'] = str(e)
    param['Gain'] = str(g)
    save_param()
    

def capture():
    global capArray
    capArray = camera.capture()
    return capArray


def saveImage(array,txt):
    global frame
    frame +=1
    img = Image.fromarray(array)
    img2 = ImageEnhance.Contrast(img).enhance(5)
    img2 = img2.rotate(angle=180)
    img3 = ImageDraw.Draw(img2)
    txt = txt + "      Frame " + str(frame)
    img3.text((70,5), txt, font = fnt, fill='white')
    img2 = ImageOps.expand(img2,border=5,fill='red')
    img2 = img2.save('/home/efinder/Solver/images/capture.jpg')


def loop_solve():
    while True:
        im = capture()
        txt = "Focus mode"
        saveImage(im,txt)


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

def setExp(a):
    global param
    param["Exposure"] = float(a)
    save_param()
    camera.set(float(a),param["Gain"])
    return '1'
            

def flipTestMode(mode):
    global testMode
    testMode = mode
    return('1')

def array_to_bytes(x: np.ndarray) -> bytes:
    np_bytes = BytesIO()
    np.save(np_bytes, x, allow_pickle=True)
    return np_bytes.getvalue()[128:]


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

def flipWifi():
    global led, hotspot, led_duty_cycle
    led.hardware_PWM(18,4,500000)
    if checkWifiCon('Hotspot'):
        os.system('sudo nmcli conn up preconfigured')
        hotspot = False
    else:
        os.system('sudo nmcli con up Hotspot')
        hotspot = True
    time.sleep(2)
    led.hardware_PWM(18,200,led_duty_cycle)

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
    os.system("sudo nmcli dev wifi hotspot ssid '"+ sid +"' password '" + pswd + "'")
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
camera = RPICamera_High_Res.RPICamera()
camera.set(float(param["Exposure"]),param["Gain"])



cmd = {
    "TS" : "nexus.write(':TS'+flipTestMode(True)+'#')",
    "TO" : "nexus.write(':TO'+flipTestMode(False)+'#')",
    "GV" : "nexus.write(':GV'+version+'#')",
    "SE" : "nexus.write(':SE'+adjExp(float(msg[3:5]))+'#')",
    "SG" : "nexus.write(':SG'+adjGain(float(msg[3:5]))+'#')",
    "SX" : "nexus.write(':SX'+setExp(msg.strip('#')[3:])+'#')",
    "SB" : "nexus.write(':SB'+setLED(float(msg[3:].strip('#')))+'#')",
    "SW" : "nexus.write(':SW'+setWifi(msg.strip('#')[3:])+'#')",
    "SH" : "nexus.write(':SH'+configHotspotWifi(msg.strip('#')[3:])+'#')",
    "SI" : "nexus.write(':SI'+configInfraWifi(msg.strip('#')[3:])+'#')",
    "SQ" : "nexus.write(':SQ'+wifiOnOff(msg.strip('#')[3:])+'#')"
}

led_duty_cycle = int(float(param["LED"])) * 10000
led.hardware_PWM(18,200,led_duty_cycle)

loop = True
solveloop = Thread(target=loop_solve)
solveloop.start()
time.sleep(0.5)

wifiloop = Thread(target=serveWifi)
wifiloop.start()
time.sleep(0.5)

while True:
    if switch.read(17) == 0:
        flipWifi()
    msg = nexus.scan()
    if msg != None:
        print ('received',msg)
        try:
            exec(cmd[msg[1:3]])
        except Exception as error:
            nexus.write(':EF'+str(error)+'#')
            print ('Error',error) 
    time.sleep(0.05) 
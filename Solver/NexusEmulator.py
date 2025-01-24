#!/usr/bin/python3

# Code to emulate a Nexus DSC when testing an eFinder cli
# Start this code before booting the eFinder
# if /dev/ttyACM0 not found, try replugging the USB cable.

import serial
from datetime import datetime
import time
import numpy as np
from io import BytesIO
from matplotlib import pyplot as plt

ser = serial.Serial('/dev/ttyACM0',baudrate=9600)

def readUsb():
    while True:
        if ser.in_waiting > 0:
            time.sleep(0.1) # make sure whole packet is got
            reply = ser.read(ser.in_waiting)
            msg = reply.decode("utf-8")
            print ('reply',msg)
            if msg[0] == ':':
                if msg == ':Gt#':
                    ser.write(b'+51*20#')
                elif msg == ':Gg#':
                    ser.write(b'+000*50#')
                elif msg == ':GL#':
                    now = datetime.now()
                    timet = now.strftime("%H:%M:%S#") 
                    ser.write(bytes(timet.encode("ascii")))
                elif msg == ':GC#':
                    now = datetime.now()
                    date = now.strftime("%m/%d/%y#") 
                    ser.write(bytes(date.encode("ascii")))
                elif msg == ':GG#':
                    ser.write(b'+00.0#')
                    break # finished initial geoloc download

        time.sleep(0.05)

def bytes_to_array(b: bytes) -> np.ndarray:
    np_bytes = BytesIO(b)
    return np.load(np_bytes, allow_pickle=True)

print ('Waiting for eFinder to Initialise')

readUsb()
time.sleep(8) # allow eFinder to load dBases etc
print ('eFinder ready')

while True:

        txt = input(' enter string to send ')
        txt = ':'+txt+'#'
        
        if txt == ':GI#' or txt == ':GP#': # get image bytes
            ser.write(bytes(txt.encode("ascii")))
            while ser.in_waiting == 0:
                time.sleep(0.1)
            reply = ser.read(ser.in_waiting)
            imArray = bytes_to_array(reply)
            plt.imshow(imArray, interpolation='nearest')
            plt.show() # close plot window on screen when done
        
        elif txt == ':LI#' or txt == ':LP#': # looping get image bytes
            try:
                while True:
                    ser.write(bytes(txt.encode("ascii")))
                    while ser.in_waiting == 0:
                        time.sleep(0.1)
                    reply = ser.read(ser.in_waiting)
                    imArray = bytes_to_array(reply)
                    plt.imshow(imArray, interpolation='nearest')
                    plt.show(block=False)
                    plt.pause(2)
                    
            except KeyboardInterrupt:
                plt.close("all")
                continue

        else: # all other commands
            ser.write(bytes(txt.encode("ascii")))
            while ser.in_waiting == 0:
                time.sleep(0.1)
            reply = ser.read(ser.in_waiting).decode("utf-8")
            print ('Reply ',reply)


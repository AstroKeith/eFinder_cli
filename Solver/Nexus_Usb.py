import serial
import time
import socket
from skyfield.api import wgs84
from datetime import datetime, timedelta
import os
import math
import re
import Coordinates_Lite
import subprocess
import sys

class Nexus:
    """The Nexus utility class"""

    def __init__(self, coordinates: Coordinates_Lite) -> None:
        """Initializes the Nexus DSC

        Parameters:
        handpad (Display): The handpad that is connected to the eFinder
        coordinates (Coordinates): The coordinates utility class to be used in the eFinder
        """

        self.aligned = False
        self.nexus_link = "none"
        self.coordinates = coordinates
        self.long = 0
        self.lat = 0
        self.earth = coordinates.get_earth()
        self.ts = coordinates.get_ts()
        #self.ts = load.timescale()

        try:
            #self.ser = serial.Serial("/dev/serial0", baudrate=9600)
            self.ser = serial.Serial('/dev/ttyGS0',baudrate=9600)
            time.sleep(0.1)
            '''
            self.ser.write(b":G#")
            time.sleep(0.1)
            p = str(self.ser.read(self.ser.in_waiting), "ascii")
            if p[0] != "1":
                print ('Nexus not responding')
                #return
            '''
            self.nexus_link = "USB"
        except:
            print ("cant open USB to Nexus")

    def write(self, txt: str) -> None:
        """Write a message to the Nexus DSC

        Parameters:
        txt (str): The text to send to the Nexus DSC
        """

        self.ser.write(bytes(txt.encode("ascii")))

        print("sent", txt, "to Nexus")

    def writeBytes(self,byt):
        self.ser.write(byt)

    def get(self, txt: str) -> str:
        """Receive a message from the Nexus DSC

        Parameters:
        txt (str): The string to send (to tell the Nexus DSC what you want to receive)

        Returns:
        str:  The requested information from the DSC
        """

        self.ser.write(bytes(txt.encode("ascii")))
        time.sleep(0.2)
        res = str(self.ser.read(self.ser.in_waiting).decode("ascii")).strip("#")
        #print("sent", txt, "got", res, "from Nexus")
        return res

    def scan(self):
        if self.ser.in_waiting > 0:
            a = str(self.ser.read(self.ser.in_waiting).decode("ascii"))
            return a

    def read(self) -> None:
        """Establishes that Nexus DSC is talking to us and get observer location and time data"""
        Lt = self.get(":Gt#")[0:6].split("*")
        self.lat = float(Lt[0] + "." + Lt[1])
        Lg = self.get(":Gg#")[0:7].split("*")
        self.long = -1 * float(Lg[0] + "." + Lg[1])
        self.location = self.coordinates.get_earth() + wgs84.latlon(self.lat, self.long)
        self.site = wgs84.latlon(self.lat,self.long)
        local_time = self.get(":GL#")
        local_date = self.get(":GC#")
        local_offset = float(self.get(":GG#"))
        print(
            "Nexus reports: local datetime as",
            local_date,
            local_time,
            " local offset:",
            local_offset,
        )
        date_parts = local_date.split("/")
        local_date = date_parts[0] + "/" + date_parts[1] + "/20" + date_parts[2]
        dt_str = local_date + " " + local_time
        format = "%m/%d/%Y %H:%M:%S"
        local_dt = datetime.strptime(dt_str, format)
        new_dt = local_dt + timedelta(hours=local_offset)
        #print("Calculated UTC", new_dt)
        #print("setting pi clock to:", end=" ")
        os.system('sudo date -u --set "%s"' % new_dt + ".000Z")

        time.sleep(0.2)

        
    def get_location(self):
        """Returns the location in space of the observer

        Returns:
        location: The location
        """
        return self.location
    
    def get_site(self):
        """Returns the location on earth of the observer

        Returns:
        location: The site
        """
        return self.site
    
    def get_long(self):
        """Returns the longitude of the observer

        Returns:
        long: The lonogitude
        """
        return self.long

    def get_lat(self):
        """Returns the latitude of the observer

        Returns:
        lat: The latitude
        """
        return self.lat

    def get_usb(self) -> serial.Serial:
        """Returns the usb variable

        Returns:
        serial.Serial: The usb variable"""
        return self.ser
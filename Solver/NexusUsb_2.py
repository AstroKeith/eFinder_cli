import serial
import time
from datetime import datetime, timedelta
import os

class Nexus:
    """The Nexus utility class"""

    def __init__(self):
        """Opens channel to the Nexus DSC """

        try:
            #self.ser = serial.Serial("/dev/serial0", baudrate=9600)
            self.ser = serial.Serial('/dev/ttyGS0',baudrate=115200)
            time.sleep(0.1)

        except:
            print ("cant open USB to Nexus")

    def write(self, txt: str):
        """Write a message to the Nexus DSC

        Parameters:
        txt (str): The text to send to the Nexus DSC
        """

        self.ser.write(bytes(txt.encode("ascii")))
        print("sent", txt, "to Nexus")

    def writeBytes(self,txt,byt):
        #print('byte array length',len(byt))
        self.ser.write(bytes(txt.encode("ascii")))
        time.sleep(0.01)
        for i in range (0,1024,32):
            pkt = byt[i:i+32]
            #print('pkt',len(pkt),pkt)
            self.ser.write(pkt)
            time.sleep(0.01)

    def get(self, txt: str):
        """Receive a message from the Nexus DSC

        Parameters:
        txt (str): The string to send (to tell the Nexus DSC what you want to receive)

        Returns:
        str:  The requested information from the DSC
        """

        self.ser.write(bytes(txt.encode("ascii")))
        time.sleep(0.2)
        res = str(self.ser.read(self.ser.in_waiting).decode("ascii")).strip("#")
        return res

    def scan(self):
        if self.ser.in_waiting > 0:
            a = str(self.ser.read(self.ser.in_waiting).decode("ascii"))
            return a

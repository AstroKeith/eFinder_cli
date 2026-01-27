#!/usr/bin/python3

# Program to implement the interface between a Nexus DSC Pro and
# a Nexus eFinder (electronic finder)
# Copyright (C) 2026 Keith Venables.

import serial
import time
import socket

class Nexus:
    """The Nexus utility class"""
    def __init__(self,setPort=4061):
        """Opens channel to the Nexus DSC """
        try:
            self.ser = serial.Serial('/dev/ttyGS0',baudrate=115200, write_timeout=1)
            time.sleep(0.1)
            self.ser.write(b':ID=eFinderLite#')
            self.conn = 'usb'
            print ("Connected to Nexus DSC via USB")
        except:
            if setPort != 9999:
                print ("cant open USB to Nexus")
                print('Starting wifi server - waiting for Nexus connection')
                self.host = ''
                self.port = setPort
                self.backlog = 50
                self.size = 1024
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.s.bind((self.host,self.port))
                self.s.listen(self.backlog)
                print ('wifi server established')
                self.client, self.address = self.s.accept()
                print ('Connected to Nexus DSC via wifi',self.client,self.address)
                self.conn = 'wifi'
            else:
                pass

        
    def write(self, txt: str):
        if self.conn == 'wifi':
            try:
                if txt == ':ID=eFinderLite#':
                    return
                self.client.send(bytes(txt.encode('cp1253')))
                print("sent", txt, "to Nexus")
            except:
                self.reOpenSocket()
        else:
            self.ser.write(bytes(txt.encode("cp1253")))
            print("sent", txt, "to Nexus")

    def writeBytes(self,txt,byt):
        print('byte array length',len(byt))
        if self.conn == 'wifi':
            try:
                self.client.send(bytes(txt.encode('cp1253')))
                self.client.send(byt)
            except:
                self.reOpenSocket()
                return
        else:
            self.ser.write(bytes(txt.encode('cp1253')))
            time.sleep(0.01)
            for i in range (0,1024,32):
                pkt = byt[i:i+32]
                self.ser.write(pkt)
                time.sleep(0.01)

    def get(self, txt: str):
        if self.conn == 'wifi':
            try:
                self.client.send(bytes(txt.encode('cp1253')))
                time.sleep(0.2)
                data = self.client.recv(self.size)
                if data:
                    msg = data.decode("utf-8","ignore")
                    return msg.strip('#')
            except:
                self.reOpenSocket()
                return ''
        else:
            self.ser.write(bytes(txt.encode('cp1253')))
            time.sleep(0.2)
            res = str(self.ser.read(self.ser.in_waiting).decode('cp1253')).strip("#")
            return res
    
    def reOpenSocket(self):
        print('connection dropped - reopening socket')
        self.s.close()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((self.host,self.port))
        self.s.listen(self.backlog)
        print ('wifi server established')
        self.client, self.address = self.s.accept()
        print ('Connected to Nexus DSC via wifi',self.client,self.address)
    
    def scan(self):
        if self.conn == 'usb':
            try:
                if self.ser.in_waiting > 0:
                    a = str(self.ser.read(self.ser.in_waiting).decode('cp1253'))
                    return a
            except:
                self.ser = serial.Serial('/dev/ttyGS0',baudrate=115200, write_timeout=1)
                if self.ser.is_open:
                    txt = ':ID=eFinderLite#'
                    self.ser.write(bytes(txt.encode('cp1253')))
        else:
            try:
                print('waiting')
                data = self.client.recv(self.size)
                if len(data) == 0:
                    self.reOpenSocket()
                if data:
                    msg = data.decode("cp1253","ignore")
                    if msg[1:3] == 'ID':
                        self.client.send(b':ID=eFinderLite#')
                    else:
                        return msg
            except:
                self.reOpenSocket()


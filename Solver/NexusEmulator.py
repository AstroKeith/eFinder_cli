import serial

from threading import Thread
from datetime import datetime
import time
flag = False
wait = True
byteFlag = False
ser = serial.Serial('/dev/ttyACM0',baudrate=9600)

def readUsb():
    global msg, flag, byteFlag
    print('readUsb starting')
    time.sleep(0.1)
    while True:
        if ser.in_waiting > 0:
            time.sleep(0.1)
            reply = ser.read(ser.in_waiting)
            if byteFlag == True:
                print('bytes',reply)
                flag = True
                byteFlag = False
                continue
            else:
                msg = reply.decode("utf-8")

            if msg[0] == ':':
                print(msg)
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
                    flag = True # finished initial geoloc download
            else:
                print ('reply',msg)
                flag = True
        time.sleep(0.05)
        
serveLoop = Thread(target=readUsb)
serveLoop.start()


while True:
    if flag == True:
        txt = input(' enter string to send ')
        txt = ':'+txt+'#'
        ser.write(bytes(txt.encode("ascii")))
        if txt == ':GI#' or txt == ':GP#':
            byteFlag=True
        flag = False
        time.sleep(0.5)




#time.sleep(0.1)
#print('got reply: ',ser.read(ser.in_waiting).decode("ascii"))
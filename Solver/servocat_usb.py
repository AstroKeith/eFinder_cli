import serial
import time

class ServoCat:
    """The ServoCat utility class"""

    def __init__(self):
        try:
            self.ser = serial.Serial('/dev/serial0',baudrate=9600)
        except:
            print ("cant open USB to ServoCat")

    def write(self, txt: str):
        self.ser.write(bytes(txt.encode("cp1253")))
        print("sent", txt, "to ServoCat")

    def scan(self):
        try:
            if self.ser.in_waiting > 0:
                time.sleep(0.1)
                a = str(self.ser.read(self.ser.in_waiting).decode("ascii"))
                return a
        except:
            self.ser = serial.Serial('/dev/serial0',baudrate=9600)

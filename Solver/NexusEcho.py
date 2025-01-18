import serial

NexUsb = serial.Serial('/dev/ttyGS0',baudrate=9600)

while True:
    if NexUsb.in_waiting > 0:
        a = str(NexUsb.read(NexUsb.in_waiting).decode("ascii"))
        print('Received',a)
        NexUsb.write(bytes(a.encode("ascii")))

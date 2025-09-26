import uuid
import os

ssid = 'efinder'+(hex(uuid.getnode())[-4:])
pswd = "12345678"
with open ('/home/efinder/Solver/default_hotspot.txt','w') as f:
    f.write('ssid:'+ssid+'\n')
    f.write('password:'+pswd+'\n')

os.system("sudo nmcli dev wifi hotspot ssid '"+ ssid +"' password '" + pswd + "'")

os.system('sudo nmcli conn up preconfigured')
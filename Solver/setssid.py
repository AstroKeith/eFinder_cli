import uuid
mac = (hex(uuid.getnode())[-4:])
pswd = "12345678"
with open ('/home/efinder/Solver/default_hotspot.txt','w') as f:
    f.write('ssid:efinder'+mac+'\n')
    f.write('password:'+pswd+'\n')

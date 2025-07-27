import os

with open('/boot/firmware/cmdline.txt', mode='r') as file:
    content = file.readline()
print (content)

os.system("rm /boot/firmware/cmdline.txt")

content_parts = content.split('rootwait')
newline = content_parts[0] + 'rootwait modules-load=dwc2,g_serial' + content_parts[1]

with open('/boot/firmware/cmdline.txt', mode='w') as file:
    file.write(newline)

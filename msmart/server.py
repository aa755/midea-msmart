#!/usr/bin/env python3
from msmart.device import device as midea_device
from msmart.device import air_conditioning_device as ac
from datetime import datetime
import time

import socket

client = midea_device('/dev/ttyUSB0', '1')
device = client.setup()
lastresp = bytearray()
subscribers=[]
HOST='0.0.0.0'
PORT=6655
#device.power_state = True
#device.target_temperature = 19.0
socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.bind((HOST, PORT))
    s.settimeout(1)#1 second
    while True:
        data, addr = sock.recvfrom(2)
        try:
            print (addr)
        except:
            sleep(8)
            lastresp=device.refresh()

#!/usr/bin/env python3
from msmart.device import device as midea_device
from msmart.device import air_conditioning_device as ac
from datetime import datetime
import time

import socket

client = midea_device('/dev/ttyUSB0', 12345)
device = client.setup()
#device.farenheit_unit=True
subscribers=[]
HOST='0.0.0.0'
PORT=6655
#device.power_state = True
#device.target_temperature = 19.0
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as recv, socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sends:
    recv.bind((HOST, PORT))
    recv.settimeout(1)#1 second
    while True:
        try:
            data, addr = recv.recvfrom(2)
            print(f'received {data} of size {len(data)}')
            if data[0]==0:
                addr = (addr[0],2000+data[1])
                if (addr in subscribers):
                    print(f'{addr} was alreadyy subscribed')
                else:
                    subscribers.extend([addr])
                    print(f'subscribing {addr}.')
                print(f'current subscribers are {subscribers}')
            elif (data[0] == 1):
                device.power_state = (data[1] == 1)
                device.apply()
            elif (data[0] == 2):
                device.target_temperature=16.0+ ((data[1])/2.0)
                device.apply()
            elif (data[0] == 3):
                device.operational_mode = ac.operational_mode_enum.get(data[1])
                device.apply()
            elif (data[0] == 4):
                device.turbo_mode = (data[1] == 1)
                device.apply()
            elif (data[0] == 5):
                device.fan_speed = ac.fan_speed_enum.get(data[1])
                device.apply()
            elif (data[0] == 6):
                device.swing_mode = ac.swing_mode_enum.get(data[1])
                device.apply()
            else:
                print(f'invalid command {addr}')

        except socket.timeout:
            lastresp=device.refresh()
            print(len(lastresp))#31
            lastrespa=bytearray(lastresp)
            lastrespa.extend([199])
            for addr in subscribers:
                sends.sendto(lastrespa, addr)
            time.sleep(8)

#!/usr/bin/env python3
from msmart.device import device as midea_device
from msmart.device import air_conditioning_device as ac
from datetime import datetime
import time

import socket

client = midea_device('/dev/ttyUSB0', 12345)
device = client.setup()
lastresp = bytearray()
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
            host, port = addr # port is useless, it is something chosen by the socket lib. the other is probably not listening on it
            print(f'received {data} of size {len(data)}')
            if (data[0] == 0):
                if (host in subscribers):
                    print(f'{host} was already subscribed')
                else:
                    subscribers.extend([host])
                    print(f'subscribing {host}.')
            elif (data[0] == 1):
                device.power_state = (data[1] == 1)
                device.apply()
            elif (data[0] == 2):
                device.target_temperature=16.0+ ((data[1])/2.0)
                device.apply()
            elif (data[0] == 3):
                device.operational_mode=data[1]
                device.apply()
            elif (data[0] == 4):
                device.turbo_mode = (data[1] == 1)
                device.apply()
            else:
                print(f'invalid command {data}')

        except:
            lastresp=device.refresh()
            print(len(lastresp))#31
            for host in subscribers:
                sends.sendto(lastresp, (host, PORT))
            time.sleep(8)

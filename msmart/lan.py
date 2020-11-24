# -*- coding: UTF-8 -*-
import logging
import datetime
import sys
import serial
import time

# The Midea cloud client is by far the more obscure part of this library, and without some serious reverse engineering
# this would not have been possible. Thanks Yitsushi for the ruby implementation. This is an adaptation to Python 3

VERSION = '0.1.19'

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

#size 62 chars. 2 hex digits=1 byte. so 31 bytes
#aa1eac00000000000002c001ae667f7f000000000071850000000000003734

#device response on refresh
#aa1eac00000000000003c000ae667f7f00000000006b6b0000000000005833
#aa1eac00000000000003c000ae667f7f00000000006b6b0000000000005833

#refresh response
#aa23ac0000000000000240818e6603ff000000000000000000000000000018000000ce92

class lan:
    def __init__(self, device_ip, device_id):
        # Get this from any of the Midea based apps, you can find one on Yitsushi's github page
        self.device_ip = device_ip

    def appliance_transparent_send(self, data):
        ser = serial.Serial(self.device_ip, timeout=None, baudrate=9600)
#        print('connected')
        ser.write(data)
        resp=ser.read(31)
        ser.close()
        return resp

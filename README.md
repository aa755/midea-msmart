This is a library to allow communicating to a Midea AC via the Local area network.

# midea-msmart

This a form from the repo at [mac-zhou/midea-msmart](https://github.com/mac-zhou/midea-msmart), which itself was derived from
[yitsushi's project](https://github.com/yitsushi/midea-air-condition), [NeoAcheron's project](https://github.com/NeoAcheron/midea-ac-py) and [andersonshatch's project](https://github.com/andersonshatch/midea-ac-py).

But this library just allow communicating to a Midea AC without the wifi dongle: in place of the wifi dongle, you connect a UART directy to the AC.
If you are suffering from unreliability of the wifi dongle or the wifi network, you can use this library to have a fully wired control of your AC.

# usage example:
```
from msmart.device import device as midea_device
from msmart.device import air_conditioning_device as ac
from datetime import datetime
import time

garbage_not_used="1234" # any value is fine. not used
mbr = ('/dev/ttyUSB0', garbage_not_used)
client2 = midea_device(mbr[0], int(mbr[1]))
device = client2.setup()
print("setup done, doing device refresh")
device.power_state = True
device.target_temperature = 19.0
#device.farenheit_unit = True
device.operational_mode = ac.operational_mode_enum.heat
# commit the changes with apply()
print("starting apply")
device.apply()

while True:
    device.refresh()
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)
    print({
        'id': device.id,
        'power_state': device.power_state,
        'target_temperature': device.target_temperature,
        'operational_mode': device.operational_mode,
        'fan_speed': device.fan_speed,
        'swing_mode': device.swing_mode,
        'eco_mode': device.eco_mode,
        'turbo_mode': device.turbo_mode
    })
    time.sleep(10)
```
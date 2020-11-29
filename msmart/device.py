
import logging
from enum import Enum

import msmart.crc8 as crc8
from msmart.lan import lan
from msmart.command import appliance_response
from msmart.command import base_command as request_status_command
from msmart.command import set_command
from msmart.packet_builder import packet_builder
import traceback
VERSION = '0.1.19'

_LOGGER = logging.getLogger(__name__)

class device:

    def __init__(self, device_ip: str, device_id: int):
        self._lan_service = lan(device_ip)
        self._ip = device_ip
        self._id = device_id
        self._type = 0xac
        self._half_temp_step = False
        self._support = False

    def setup(self):
        # self.air_conditioning_device.refresh()
        device = air_conditioning_device(self._ip, self._id)
        return device

    # def set_device_detail(self, device_detail: dict):
    #     self._id = device_detail['id']
    #     self._name = device_detail['name']
    #     self._model_number = device_detail['modelNumber']
    #     self._serial_number = device_detail['sn']
    #     self._type = int(device_detail['type'], 0)
    #     self._active = device_detail['activeStatus'] == '1'
    #     self._online = device_detail['onlineStatus'] == '1'

    def refresh(self):
        pass

    def apply(self):
        pass

    @property
    def id(self):
        return self._id

    @property
    def ip(self):
        return self._ip

    @property
    def name(self):
        return self._name

    @property
    def model_number(self):
        return self._model_number

    @property
    def serial_number(self):
        return self._serial_number

    @property
    def type(self):
        return self._type

    @property
    def active(self):
        return True

    @property
    def online(self):
        return True

    @property
    def support(self):
        return self._support


class air_conditioning_device(device):

    class fan_speed_enum(Enum):
        Auto = 102
        High = 80
        Medium = 60
        Low = 30
        Silent = 20

        @staticmethod
        def list():
            return list(map(lambda c: c.name, air_conditioning_device.fan_speed_enum))

        @staticmethod
        def get(value):
            if(value in air_conditioning_device.fan_speed_enum._value2member_map_):
                return air_conditioning_device.fan_speed_enum(value)
            _LOGGER.debug("Unknown Fan Speed: {}".format(value))
            return air_conditioning_device.fan_speed_enum.Auto

    class operational_mode_enum(Enum):
        auto = 1
        cool = 2
        dry = 3
        heat = 4
        fan_only = 5

        @staticmethod
        def list():
            return list(map(lambda c: c.name, air_conditioning_device.operational_mode_enum))

        @staticmethod
        def get(value):
            if(value in air_conditioning_device.operational_mode_enum._value2member_map_):
                return air_conditioning_device.operational_mode_enum(value)
            _LOGGER.debug("Unknown Operational Mode: {}".format(value))
            return air_conditioning_device.operational_mode_enum.fan_only

    class swing_mode_enum(Enum):
        Off = 0x0
        Vertical = 0xC
        Horizontal = 0x3
        Both = 0xF

        @staticmethod
        def list():
            return list(map(lambda c: c.name, air_conditioning_device.swing_mode_enum))

        @staticmethod
        def get(value):
            if(value in air_conditioning_device.swing_mode_enum._value2member_map_):
                return air_conditioning_device.swing_mode_enum(value)
            _LOGGER.debug("Unknown Swing Mode: {}".format(value))
            return air_conditioning_device.swing_mode_enum.Off

    def __init__(self, device_ip: str, device_id: int):
        super().__init__(device_ip, (device_id))
        self._prompt_tone = False
        self._power_state = False
        self._target_temperature = 17.0
        self._operational_mode = air_conditioning_device.operational_mode_enum.auto
        self._fan_speed = air_conditioning_device.fan_speed_enum.Auto
        self._swing_mode = air_conditioning_device.swing_mode_enum.Off
        self._eco_mode = False
        self._turbo_mode = False
        self.farenheit_unit = False # default unit is Celcius. this is just to control the temperatue unit of the AC's display. the target_temperature setter always expects a celcius temperature (resolution of 0.5C), as does the midea API
        self.tempcontrol_overriden_fan=False#restarting off hass will be a problem. AC wont change its state. need to manually change mode to heat/cool opposite temporarily after restart
        self.tempcontrol_usermode=air_conditioning_device.operational_mode_enum.auto

        self._on_timer = None
        self._off_timer = None
        self._indoor_temperature = 0.0
        self._outdoor_temperature = 0.0
        self._finectrl = True
        self._tswing = 1.0

    def overdone(self, mode, target, actual):
        if (mode==air_conditioning_device.operational_mode_enum.cool):
            return (actual<=target-self._tswing)
        elif (mode==air_conditioning_device.operational_mode_enum.heat):
            return (actual>=target+self._tswing)

    def underdone(self, mode, target, actual):
        if (mode==air_conditioning_device.operational_mode_enum.cool):
            return (actual>=target+self._tswing)
        elif (mode==air_conditioning_device.operational_mode_enum.heat):
            return (actual<=target-self._tswing)

    def refresh(self):
        cmd = request_status_command(self.type)
        pkt_builder = packet_builder(self.id)
        pkt_builder.set_command(cmd)

        data = pkt_builder.finalize()
        data = self._lan_service.appliance_transparent_send(data)
        _LOGGER.debug(
            "refresh - Recieved from {}, {}: {}".format(self.ip, self.id, data.hex()))
        if len(data) > 0:
            response = appliance_response(data)
            self._support = True
            if data[0xa] != 0xc0:
                _LOGGER.debug(
                    "refresh - Not status(0xc0) respone, defer update. {}, {}: {}".format(self.ip, self.id, data[0xa:].hex()))
            else:
                self.update(response)
        return data

    def apply(self):
        try:
            cmd = set_command(self.type)
            cmd.prompt_tone = self._prompt_tone
            cmd.power_state = self._power_state
            cmd.target_temperature = self._target_temperature
            cmd.operational_mode = self._operational_mode.value
            cmd.fan_speed = self._fan_speed.value
            cmd.swing_mode = self._swing_mode.value
            cmd.eco_mode = self._eco_mode
            cmd.turbo_mode = self._turbo_mode
            pkt_builder = packet_builder(self.id)
#            cmd.night_light = False
            cmd.fahrenheit = self.farenheit_unit
            pkt_builder.set_command(cmd)

            data = pkt_builder.finalize()
            data = self._lan_service.appliance_transparent_send(data)
            _LOGGER.debug(
                "apply - Recieved from {}, {}: {}".format(self.ip, self.id, data.hex()))
            if len(data) > 0:
                response = appliance_response(data)
                self._support = True
                if data[0xa] != 0xc0:
                    _LOGGER.debug(
                        "apply - Not status(0xc0) respone, defer update. {}, {}: {}".format(self.ip, self.id, data[0xa:].hex()))
                else:
                    self.update(response)
        except:
            print(traceback.format_exc())
            print('error occurred')

    def updateha(self, data):
        res=appliance_response(data)
        self.update(res, finectrl=False)

    def update(self, res: appliance_response, finectrl=True):
        self._power_state = res.power_state
        self._target_temperature = res.target_temperature
        oldmode = air_conditioning_device.operational_mode_enum.get(res.operational_mode)
        self._fan_speed = air_conditioning_device.fan_speed_enum.get(
            res.fan_speed)
        print(f"fan speed:{res.fan_speed}, {self._fan_speed}")
        self._swing_mode = air_conditioning_device.swing_mode_enum.get(
            res.swing_mode)
        self._eco_mode = res.eco_mode
        self._turbo_mode = res.turbo_mode
        self._indoor_temperature = res.indoor_temperature
        self._outdoor_temperature = res.outdoor_temperature
        self._timer_on = res.on_timer
        self._timer_off = res.off_timer
        if (not finectrl) or (not self._finectrl):
            self._operational_mode=oldmode
            print(f'oldnewmode:{oldmode}, usermode:{self.tempcontrol_usermode}, \n target:{self._target_temperature}, curtemp: {self._indoor_temperature}, fan_overridden: {self.tempcontrol_overriden_fan}')
            return
        if (oldmode != air_conditioning_device.operational_mode_enum.fan_only or self._power_state==False):
            self.tempcontrol_overriden_fan=False # if the automation made it fan_only, the user manually changed         if (self._power_state):
            if self._power_state==False:
                print(f'powered off. oldnewmode:{oldmode}, usermode:{self.tempcontrol_usermode}, \n target:{self._target_temperature}, curtemp: {self._indoor_temperature}, fan_overridden: {self.tempcontrol_overriden_fan}')
                return
        newmode=oldmode
        if self.tempcontrol_overriden_fan and oldmode==air_conditioning_device.operational_mode_enum.fan_only:
            if (not self.underdone(self.tempcontrol_usermode, self._target_temperature, self._indoor_temperature)):
                self.tempcontrol_overriden_fan=True
                newmode=air_conditioning_device.operational_mode_enum.fan_only
            else:
                self.tempcontrol_overriden_fan=False
                newmode=self.tempcontrol_usermode# restore old mode
        elif self.overdone(self.operational_mode, self._target_temperature, self._indoor_temperature):
            self.tempcontrol_overriden_fan=True
            self.tempcontrol_usermode=self._operational_mode
            newmode=air_conditioning_device.operational_mode_enum.fan_only
        self._operational_mode = newmode
        print(f'oldmode:{oldmode}, newmode:{self._operational_mode}, usermode:{self.tempcontrol_usermode}, \n target:{self._target_temperature}, curtemp: {self._indoor_temperature}, fan_overridden: {self.tempcontrol_overriden_fan}')
        if (self._operational_mode!=oldmode):
            self.apply()

    @property
    def prompt_tone(self):
        return self._prompt_tone

    @prompt_tone.setter
    def prompt_tone(self, feedback: bool):
        self._prompt_tone = feedback

    @property
    def power_state(self):
        return self._power_state

    @power_state.setter
    def power_state(self, state: bool):
        self._power_state = state

    @property
    def target_temperature(self):
        return self._target_temperature

    @target_temperature.setter
    def target_temperature(self, temperature_celsius: float): # the implementation later rounds the temperature down to the nearest 0.5'C resolution.
        self._target_temperature = temperature_celsius

    @property
    def operational_mode(self):
        return self._operational_mode

    @operational_mode.setter
    def operational_mode(self, mode: operational_mode_enum):
        self._operational_mode = mode

    @property
    def fan_speed(self):
        return self._fan_speed

    @fan_speed.setter
    def fan_speed(self, speed: fan_speed_enum):
        self._fan_speed = speed

    @property
    def swing_mode(self):
        return self._swing_mode

    @swing_mode.setter
    def swing_mode(self, mode: swing_mode_enum):
        self._swing_mode = mode

    @property
    def eco_mode(self):
        return self._eco_mode

    @eco_mode.setter
    def eco_mode(self, enabled: bool):
        self._eco_mode = enabled

    @property
    def turbo_mode(self):
        return self._turbo_mode

    @turbo_mode.setter
    def turbo_mode(self, enabled: bool):
        self._turbo_mode = enabled

    @property
    def indoor_temperature(self):
        return self._indoor_temperature

    @property
    def outdoor_temperature(self):
        return self._outdoor_temperature

    @property
    def on_timer(self):
        return self._on_timer

    @property
    def off_timer(self):
        return self._off_timer


class unknown_device(device):

    def __init__(self, lan_service: lan):
        super().__init__(lan_service)

    def refresh(self):
        cmd = request_status_command(self.type)
        cmd.night_light=True
        pkt_builder = packet_builder()
        pkt_builder.set_command(cmd)

        data = pkt_builder.finalize()
        data = self._lan_service.appliance_transparent_send(self.id, data)
        if len(data) > 0:
            response = appliance_response(data)
            _LOGGER.debug("Decoded Data: {}".format({
                'prompt_tone': response.prompt_tone,
                'target_temperature': response.target_temperature,
                'indoor_temperature': response.indoor_temperature,
                'outdoor_temperature': response.outdoor_temperature,
                'operational_mode': response.operational_mode,
                'fan_speed': response.fan_speed,
                'swing_mode': response.swing_mode,
                'eco_mode': response.eco_mode,
                'turbo_mode': response.turbo_mode
            }))

    def apply(self):
        _LOGGER.debug("Cannot apply, device not fully supported yet")


class dehumidifier_device(unknown_device):

    def __init__(self, lan_service: lan):
        super().__init__(lan_service)

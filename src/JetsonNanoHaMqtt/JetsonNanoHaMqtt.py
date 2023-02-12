from enum import Enum
import uuid
from jtop import jtop

import time

from paho.mqtt.client import Client

from HaMqtt.MQTTThermometer import MQTTThermometer
from HaMqtt.MQTTSwitch import MQTTSwitch
from HaMqtt.MQTTUtil import HaDeviceClass
from HaMqtt.MQTTDevice import MQTTDevice
from HaMqtt.MQTTSensor import MQTTSensor
from .mqtt.MQTTCamera import MQTTCamera
from .mqtt.MQTTText import MQTTText

class JetsonNanoHaMqtt:
    '''
    Jetson Nano Home Assistant MQTT
    
    This class sets up a Jetson Nano device to be used with Home Assistant 
    via MQTT.
    '''
    _dev = None
    _jetson = None
    _client = None
    _name = 'Jetson Nano'
    _hw_sensors_enabled = False
    _camera_enabled = False
    _inference_enabled = False
    _camera_input = None
    _camera_output = None
    _detnet_inference_network = None
    _detnet_inference_threshold = 0.5
    _imgnet_inference_network = None
    _imgnet_inference_threshold = 0.5
    th_ao = None
    th_cpu = None
    th_gpu = None
    th_pll = None
    th_thermal = None
    cpu1_pct = None
    cpu2_pct = None
    cpu3_pct = None
    cpu4_pct = None
    fan_pct = None
    pwr_cur = None
    pwr_avg = None
    cam_motion = None
    camera = None
    detnet = None
    imgnet = None

    def __init__(self, name: str, client: Client, jtop: jtop):
        self._client = client
        self._jetson = jtop
        self._name = name

    def initialize_device(self, jetson: jtop):
        '''
        Initialize the device
        
        This method initializes the device and sets up the Home Assistant
        MQTT device.
        '''
        print(jetson.board)
        self._dev = {
            "identifiers": [self._jetson.board['hardware']['Model'], self._jetson.board['hardware']['Serial Number']],
            "name": self._name,
            "manufacturer": 'NVIDIA',
            "model": self._jetson.board['hardware']['Model'],
            "sw_version": self._jetson.board['platform']['Release'],
        }
        
    def initialize_hardware_sensors(self):
        '''
        Initialize the hardware sensors
        
        This method initializes  the Home Assistant MQTT sensors.
        '''
        self.cpu1_pct = MQTTSensor("Jetson CPU1", "jetson_cpu1_pct", self._client, "%", HaDeviceClass.POWER_FACTOR, unique_id=str(uuid.uuid4()), device_dict=self._dev)
        self.cpu2_pct = MQTTSensor("Jetson CPU2", "jetson_cpu2_pct", self._client, "%", HaDeviceClass.POWER_FACTOR, unique_id=str(uuid.uuid4()), device_dict=self._dev)
        self.cpu3_pct = MQTTSensor("Jetson CPU3", "jetson_cpu3_pct", self._client, "%", HaDeviceClass.POWER_FACTOR, unique_id=str(uuid.uuid4()), device_dict=self._dev)
        self.cpu4_pct = MQTTSensor("Jetson CPU4", "jetson_cpu4_pct", self._client, "%", HaDeviceClass.POWER_FACTOR, unique_id=str(uuid.uuid4()), device_dict=self._dev)
        self.gpu1_pct = MQTTSensor("Jetson GPU1", "jetson_gpu1_pct", self._client, "%", HaDeviceClass.POWER_FACTOR, unique_id=str(uuid.uuid4()), device_dict=self._dev)
        self.fan_pct = MQTTSensor("Jetson Fan", "jetson_fan_pct", self._client, "%", HaDeviceClass.POWER_FACTOR, unique_id=str(uuid.uuid4()), device_dict=self._dev)
        self.th_ao = MQTTThermometer("Jetson Temp AO", "jetson_t_ao", self._client, "C", device_dict=self._dev)
        self.th_cpu = MQTTThermometer("Jetson Temp CPU", "jetson_t_cpu", self._client, "C", device_dict=self._dev)
        self.th_gpu = MQTTThermometer("Jetson Temp GPU", "jetson_t_gpu", self._client, "C", device_dict=self._dev)
        self.th_pll = MQTTThermometer("Jetson Temp PLL", "jetson_t_pll", self._client, "C", device_dict=self._dev)
        self.th_thermal = MQTTThermometer("Jetson Temp Thermal", "jetson_t_thermal", self._client, "C", device_dict=self._dev)
        self.pwr_cur = MQTTSensor("Jetson Power Current", "jetson_pwr_cur", self._client, "mW", HaDeviceClass.POWER, unique_id=str(uuid.uuid4()), device_dict=self._dev)
        self.pwr_avg = MQTTSensor("Jetson Power Average", "jetson_pwr_avg", self._client, "mW", HaDeviceClass.POWER, unique_id=str(uuid.uuid4()), device_dict=self._dev)
        self._hw_sensors_enabled = True
    
    def close_hardware_sensors(self):
        '''
        Close the hardware sensors

        This method closes the Home Assistant MQTT sensors.
        '''
        if self._hw_sensors_enabled:
            self.cpu1_pct.close()
            self.cpu2_pct.close()
            self.cpu3_pct.close()
            self.cpu4_pct.close()
            self.gpu1_pct.close()
            self.fan_pct.close()
            self.th_ao.close()
            self.th_cpu.close()
            self.th_gpu.close()
            self.th_pll.close()
            self.th_thermal.close()
            self.pwr_cur.close()
            self.pwr_avg.close()
            self._hw_sensors_enabled = False

    def initialize_camera(self):
        '''
        Initialize the camera
        
        This method initializes the Home Assistant MQTT sensors for the camera.
        '''
        self.cam_motion = MQTTSensor("Jetson Camera Motion", "jetson_cam_motion", self._client, "mW", HaDeviceClass.POWER, unique_id=str(uuid.uuid4()), device_dict=self._dev)
        self.camera = MQTTText("Jetson Camera", "jetson_cam", self._client, unique_id=str(uuid.uuid4()), device_dict=self._dev)
        self._camera_enabled = True
    
    def close_camera(self):
        '''
        Close the camera
        
        This method closes the Home Assistant MQTT sensors for the camera.
        '''
        if self._camera_enabled:
            self.cam_motion.close()
            self.camera.close()
            self._camera_enabled = False
    
    def initialize_inference(self):
        '''
        Initialize the inference
        
        This method initializes the Home Assistant MQTT sensors for the inference.
        '''
        self.detnet = MQTTText("Jetson Detection Inference", "jetson_detnet_inference", self._client, unique_id=str(uuid.uuid4()), device_dict=self._dev)
        self.imgnet = MQTTText("Jetson Image Inference", "jetson_imgnet_inference", self._client, unique_id=str(uuid.uuid4()), device_dict=self._dev)
        self._inference_enabled = True

    def close_inference(self):
        '''
        Close the inference
        
        This method closes the Home Assistant MQTT sensors for the inference.
        '''
        if self._inference_enabled:
            self.detnet.close()
            self.imgnet.close()
            self._inference_enabled = False
    
    def publish_hardware_sensors(self, jetson: jtop):
        '''
        Publish the hardware sensors
        
        This method publishes the sensors metrics to Home Assistant.
        '''

        print(jetson.stats)
        self.cpu1_pct.publish_state(f'{jetson.stats["CPU1"]:3}')
        self.cpu2_pct.publish_state(f'{jetson.stats["CPU2"]:3.2f}')
        if jetson.stats["CPU3"] is "OFF":
            c3_pct = -1
        else:
            c3_pct = f'{jetson.stats["CPU3"]:3}'
        if jetson.stats["CPU4"] is "OFF":
            c4_pct = -1
        else:
            c4_pct = f'{jetson.stats["CPU4"]:3}'
        self.cpu3_pct.publish_state(c3_pct)
        self.cpu4_pct.publish_state(c4_pct)
        self.gpu1_pct.publish_state(f'{jetson.stats["GPU1"]:3.2f}')
        self.fan_pct.publish_state(f'{jetson.stats["fan"]:2.2f}')
        self.th_ao.publish_state(f'{jetson.stats["Temp AO"]:2.2f}')
        self.th_cpu.publish_state(f'{jetson.stats["Temp CPU"]:2.2f}')
        self.th_gpu.publish_state(f'{jetson.stats["Temp GPU"]:2.2f}')
        self.th_pll.publish_state(f'{jetson.stats["Temp PLL"]:2.2f}')
        self.th_thermal.publish_state(f'{jetson.stats["Temp thermal"]:2.2f}')
        self.pwr_cur.publish_state(jetson.stats['power cur'])
        self.pwr_avg.publish_state(jetson.stats['power avg'])


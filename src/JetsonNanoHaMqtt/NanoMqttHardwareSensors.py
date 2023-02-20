from paho.mqtt.client import Client
from HaMqtt.MQTTUtil import HaDeviceClass
from HaMqtt.MQTTSensor import MQTTSensor
from HaMqtt.MQTTThermometer import MQTTThermometer
import uuid
import threading
import time
from jtop import jtop

class NanoMqttHardwareSensors():
    '''
    Nano MQTT Hardware Sensors

    This class sets up a Nano MQTT Hardware Sensors.
    '''
    _client = None                        # The MQTT client
    _name = None                          # The name of the hardware sensors
    _dev = None                           # The device dictionary
    _hardware_sensors_enabled = False     # The hardware sensors status
    _jetson = None                        # The jetson object

    
    jetson_temp_ao = None                 # The jetson AO temperature
    jetson_temp_cpu = None                # The jetson CPU temperature
    jetson_temp_gpu = None                # The jetson GPU temperature
    jetson_temp_pll = None                # The jetson PLL temperature
    jetson_temp_thermal = None            # The jetson thermal temperature
    jetson_cpu1_pct = None                # The jetson CPU1 percentage
    jetson_cpu2_pct = None                # The jetson CPU2 percentage
    jetson_cpu3_pct = None                # The jetson CPU3 percentage
    jetson_cpu4_pct = None                # The jetson CPU4 percentage
    jetson_gpu1_pct = None                # The jetson GPU1 percentage
    jetson_fan_pct = None                 # The jetson fan speed percentage
    jetson_pwr_cur = None                 # The jetson power current
    jetson_pwr_avg = None                 # The jetson power average
    
    def __init__(self, name: str, client: Client, dev: dict, jetson: jtop):
        self._client = client
        self._name = name
        self._dev = dev
        self._jetson = jetson

    def initialize(self):
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
        self.th_ao = MQTTThermometer("Jetson Temp AO", "jetson_t_ao", self._client, "°C", device_dict=self._dev)
        self.th_cpu = MQTTThermometer("Jetson Temp CPU", "jetson_t_cpu", self._client, "°C", device_dict=self._dev)
        self.th_gpu = MQTTThermometer("Jetson Temp GPU", "jetson_t_gpu", self._client, "°C", device_dict=self._dev)
        self.th_pll = MQTTThermometer("Jetson Temp PLL", "jetson_t_pll", self._client, "°C", device_dict=self._dev)
        self.th_thermal = MQTTThermometer("Jetson Temp Thermal", "jetson_t_thermal", self._client, "°C", device_dict=self._dev)
        self.pwr_cur = MQTTSensor("Jetson Power Current", "jetson_pwr_cur", self._client, "mW", HaDeviceClass.POWER, unique_id=str(uuid.uuid4()), device_dict=self._dev)
        self.pwr_avg = MQTTSensor("Jetson Power Average", "jetson_pwr_avg", self._client, "mW", HaDeviceClass.POWER, unique_id=str(uuid.uuid4()), device_dict=self._dev)
        self._hw_sensors_enabled = True
    
    def close(self):
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
            self.stop()
            self._hw_sensors_enabled = False

    def publish_hardware_sensors(self, jetson: jtop):
        '''
        Publish the hardware sensors
        
        This method publishes the sensors metrics to Home Assistant.
        '''
        self.cpu1_pct.publish_state(f'{jetson.stats["CPU1"]:3}')
        self.cpu2_pct.publish_state(f'{jetson.stats["CPU2"]:3}')
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
        self.gpu1_pct.publish_state(f'{jetson.stats["GPU1"]:3}')
        self.fan_pct.publish_state(f'{jetson.stats["fan"]:2.2f}')
        self.th_ao.publish_state(f'{jetson.stats["Temp AO"]:2.2f}')
        self.th_cpu.publish_state(f'{jetson.stats["Temp CPU"]:2.2f}')
        self.th_gpu.publish_state(f'{jetson.stats["Temp GPU"]:2.2f}')
        self.th_pll.publish_state(f'{jetson.stats["Temp PLL"]:2.2f}')
        self.th_thermal.publish_state(f'{jetson.stats["Temp thermal"]:2.2f}')
        self.pwr_cur.publish_state(jetson.stats['power cur'])
        self.pwr_avg.publish_state(jetson.stats['power avg'])

    def publish_hardware_sensors_loop(self, jetson: jtop, frequency: int = 5):
        '''
        Publish the hardware sensors
        
        This method publishes the sensors metrics to Home Assistant.
        '''
        while jetson.ok():
            self.publish_hardware_sensors(jetson)
            time.sleep(frequency)
    
    def start(self, jetson: jtop, frequency: int = 5):
        '''
        Start the hardware sensors loop
        
        This method starts the hardware sensors loop.
        '''
        self._hw_sensors_thread = threading.Thread(target=self.publish_hardware_sensors_loop, args=(jetson, frequency))
        self._hw_sensors_thread.start()
    
    def stop(self):
        '''
        Stop the hardware sensors loop
        
        This method stops the hardware sensors loop.
        '''
        self._hw_sensors_thread.join()


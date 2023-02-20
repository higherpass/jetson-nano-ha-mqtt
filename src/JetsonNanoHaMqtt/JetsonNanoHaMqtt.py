from typing import List
from jtop import jtop
from paho.mqtt.client import Client
from .NanoMqttHardwareSensors import NanoMqttHardwareSensors
from .NanoMqttCamera import NanoMqttCamera
from .NanoMqttInference import NanoMqttInference

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
    _hw_sensors: NanoMqttHardwareSensors = None
    _camera_enabled = False
    _cameras: List[NanoMqttCamera] = []
    _inferences = []
    _inference_enabled = False

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

        This method initializes the hardware sensors and sets up the Home Assistant
        MQTT sensors.
        '''
        self._hw_sensors = NanoMqttHardwareSensors(self._name, self._client, self._dev, self._jetson)
        self._hw_sensors.initialize()
        self._hw_sensors_enabled = True
    
    def initialize_camera(self, name: str, client: Client, input: str = None, output: str = None, inference: bool = False, inference_network: str = None, inference_threshold: float = 0.5):
        '''
        Initialize the camera

        This method initializes the camera and sets up the Home Assistant
        MQTT camera.
        '''
        self._cameras.append(NanoMqttCamera(name, self._client, self._dev, input=input, 
                                            output=output, inference=inference, 
                                            inference_network=inference_network, 
                                            inference_threshold=inference_threshold))
        self._cameras[-1].initialize()
        self._camera_enabled = True
    
    def initialize_inference(self, name: str, client: Client, jetson_inference, network: str = None, threshold: float = 0.5):
        '''
        Initialize the inference entities

        
        '''
        self._inferences.append(NanoMqttInference(name, self._client, self._dev, jetson_inference, network=network))
        self._inferences[-1].initialize()
        self._inference_enabled = True

    def start_hardware_sensors(self):
        '''
        Start the hardware sensors

        This method starts the hardware sensors.
        '''
        if self._hw_sensors_enabled:
            self._hw_sensors.start(self._jetson)
    
    def stop_hardware_sensors(self):
        '''
        Stop the hardware sensors

        This method stops the hardware sensors.
        '''
        if self._hw_sensors_enabled:
            self._hw_sensors.stop()
    
    def start_camera(self):
        '''
        Start the camera

        This method starts the camera.
        '''
        if self._camera_enabled:
            for camera in self._cameras:
                camera.start()
    
    def stop_camera(self):
        '''
        Stop the camera

        This method stops the camera.
        '''
        if self._camera_enabled:
            for camera in self._cameras:
                camera.stop()
    
    def start_inference(self):
        '''
        Start the inference

        This method starts the inference.
        '''
        if self._inference_enabled:
            for inference in self._inferences:
                inference.start()
    
    def stop_inference(self):
        '''
        Stop the inference

        This method stops the inference.
        '''
        if self._inference_enabled:
            for inference in self._inferences:
                inference.stop()
    
    def start(self):
        '''
        Start the device

        This method starts the device.
        '''
        self.start_hardware_sensors()
        self.start_camera()
        self.start_inference()
    
    def stop(self):
        '''
        Stop the device

        This method stops the device.
        '''
        self.stop_camera()
        self.stop_hardware_sensors()
        self.stop_inference()

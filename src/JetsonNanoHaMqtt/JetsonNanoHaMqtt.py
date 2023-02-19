import base64
from datetime import datetime
from enum import Enum
import os
import threading
import uuid

import pytz
from jtop import jtop
import time
from PIL import Image
from numpy import asarray
from io import BytesIO
from paho.mqtt.client import Client

from HaMqtt.MQTTThermometer import MQTTThermometer
from HaMqtt.MQTTUtil import HaDeviceClass
from HaMqtt.MQTTSensor import MQTTSensor
from .mqtt.MQTTCamera import MQTTCamera
from .mqtt.MQTTText import MQTTText

from jetson.inference import detectNet
from jetson.utils import (videoSource, videoOutput, logUsage, cudaFromNumpy, 
                          cudaToNumpy, cudaAllocMapped, cudaCrop, 
                          cudaDeviceSynchronize)

class JetsonNanoHaMqtt:
    '''
    Jetson Nano Home Assistant MQTT
    
    This class sets up a Jetson Nano device to be used with Home Assistant 
    via MQTT.
    '''
    _dev = None
    _jetson = None
    _client = None
    _camera_input = None
    _camera_output = None
    _name = 'Jetson Nano'
    _hw_sensors_enabled = False
    _camera_enabled = False
    _camera_motion_enabled = False
    _inference_enabled = False
    _detnet_inference = None
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
    camera_inference = None
    detnet = None
    detnet_camera = None
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
        self.th_ao = MQTTThermometer("Jetson Temp AO", "jetson_t_ao", self._client, "°C", device_dict=self._dev)
        self.th_cpu = MQTTThermometer("Jetson Temp CPU", "jetson_t_cpu", self._client, "°C", device_dict=self._dev)
        self.th_gpu = MQTTThermometer("Jetson Temp GPU", "jetson_t_gpu", self._client, "°C", device_dict=self._dev)
        self.th_pll = MQTTThermometer("Jetson Temp PLL", "jetson_t_pll", self._client, "°C", device_dict=self._dev)
        self.th_thermal = MQTTThermometer("Jetson Temp Thermal", "jetson_t_thermal", self._client, "°C", device_dict=self._dev)
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
            self.stop_hardware_sensors()
            self._hw_sensors_enabled = False

    def publish_hardware_sensors(self, jetson: jtop):
        '''
        Publish the hardware sensors
        
        This method publishes the sensors metrics to Home Assistant.
        '''
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

    def publish_hardware_sensors_loop(self, jetson: jtop, frequency: int = 5):
        '''
        Publish the hardware sensors
        
        This method publishes the sensors metrics to Home Assistant.
        '''
        while jetson.ok():
            self.publish_hardware_sensors(jetson)
            time.sleep(frequency)
    
    def start_hardware_sensors(self, jetson: jtop, frequency: int = 5):
        '''
        Start the hardware sensors loop
        
        This method starts the hardware sensors loop.
        '''
        self._hw_sensors_thread = threading.Thread(target=self.publish_hardware_sensors_loop, args=(jetson, frequency))
        self._hw_sensors_thread.start()
    
    def stop_hardware_sensors(self):
        '''
        Stop the hardware sensors loop
        
        This method stops the hardware sensors loop.
        '''
        self._hw_sensors_thread.join()

    def initialize_camera(self, input: str = None, inference: bool = False):
        '''
        Initialize the camera
        
        This method initializes the Home Assistant MQTT sensors for the camera.
        '''
        if input is not None:
            self._camera_input = videoSource(input)
            self.camera = MQTTCamera("Jetson Camera", "jetson_cam", self._client, unique_id=str(uuid.uuid4()), device_dict=self._dev)
            if inference:
                self.cam_motion = MQTTText("Jetson Camera Motion", "jetson_cam_motion", self._client, unique_id=str(uuid.uuid4()), device_dict=self._dev)
                self.cam_motion_timestamp = MQTTSensor("Jetson Camera Motion Timestamp", "jetson_cam_motion_timestamp", self._client, "", HaDeviceClass.TIMESTAMP, unique_id=str(uuid.uuid4()), device_dict=self._dev)
                self.camera_inference = MQTTCamera("Jetson Camera Inference", "jetson_cam_inference", self._client, unique_id=str(uuid.uuid4()), device_dict=self._dev) 
                self._camera_motion_enabled = True
            self._camera_enabled = True
            return True
        else:
            return False
    
    def close_camera(self):
        '''
        Close the camera
        
        This method closes the Home Assistant MQTT sensors for the camera.
        '''
        if self._camera_enabled:
            self.stop_camera()
            if self._camera_motion_enabled:
                self.cam_motion.close()
                self.cam_motion_timestamp.close()
                self._camera_motion_enabled = False
            self.camera.close()
            self._camera_enabled = False
    
    def publish_camera(self, img):
        '''
        stream the camera snapshot to Home Assistant
        
        This method streams the camera and publishes the snapshot to Home Assistant.
        '''
        if self._camera_motion_enabled:
            if self._detnet_inference is not None:
                detections = self._detnet_inference.Detect(img, overlay="labels,conf")
            else:
                detections = []

            motion = None
            if (len(detections) > 0):
                det_left = img.width
                det_top = img.height
                det_right = 0
                det_bottom = 0
                # Set the ROI to the bounding box of the detections
                for detection in detections:
                    print(detection)
                    print(self._detnet_inference.GetClassDesc(detection.ClassID))
                    if detection.Left < det_left:
                        det_left = detection.Left
                    if detection.Top < det_top:
                        det_top = detection.Top
                    if detection.Right > det_right:
                        det_right = detection.Right
                    if detection.Bottom > det_bottom:
                        det_bottom = detection.Bottom
                roi = (int(det_left), int(det_top), int(det_right), int(det_bottom))
                motion = self._detnet_inference.GetClassDesc(detection.ClassID)
                self.cam_motion.publish_state(motion)
                self.cam_motion_timestamp.publish_state(datetime.now(pytz.timezone('US/Central')).isoformat())
                snapshot = cudaAllocMapped(width=roi[2]-roi[0], height=roi[3]-roi[1], format=img.format)
                cudaCrop(img, snapshot, roi)
                cudaDeviceSynchronize()
                out_np = cudaToNumpy(snapshot)
                out_img = Image.fromarray(out_np)
                img_byte_arr = BytesIO()
                out_img.save(img_byte_arr, format='JPEG')
                out_img = img_byte_arr.getvalue()
                self.camera_inference.publish_image(out_img)
                del snapshot
        cudaDeviceSynchronize()
        out_np = cudaToNumpy(img)
        out_img = Image.fromarray(out_np)
        img_byte_arr = BytesIO()
        out_img.save(img_byte_arr, format='JPEG')
        out_img = img_byte_arr.getvalue()
        self.camera.publish_image(out_img)
            

    def publish_camera_loop(self, frequency: int = 1):
        '''
        Publish the camera snapshot in a loop
        
        This method publishes the camera snapshot in a loop.
        '''
        while True:
            img = self._camera_input.Capture()
            self.publish_camera(img)
            time.sleep(frequency)
    
    def start_camera(self, frequency: int = 1):
        '''
        Start the camera
        
        This method starts the camera.
        '''
        if self._camera_enabled:
            self._camera_thread = threading.Thread(target=self.publish_camera_loop, args=(frequency,))
            self._camera_thread.start()
    
    def stop_camera(self):
        '''
        Stop the camera
        
        This method stops the camera.
        '''
        if self._camera_enabled:
            self._camera_thread.join()

    def initialize_inference(self):
        '''
        Initialize the inference
        
        This method initializes the Home Assistant MQTT sensors for the inference.
        '''
        self.detnet = MQTTText("Jetson Detection Inference", "jetson_detnet_inference", self._client, unique_id=str(uuid.uuid4()), device_dict=self._dev)
        self.detnet_camera = MQTTCamera("Jetson Detection Inference Camera", "jetson_detnet_inference_cam", self._client, unique_id=str(uuid.uuid4()), device_dict=self._dev)
        self.imgnet = MQTTText("Jetson Image Inference", "jetson_imgnet_inference", self._client, unique_id=str(uuid.uuid4()), device_dict=self._dev)
        self._detnet_inference = detectNet("ssd-mobilenet-v2", threshold=0.5)
        self._inference_enabled = True

    def close_inference(self):
        '''
        Close the inference
        
        This method closes the Home Assistant MQTT sensors for the inference.
        '''
        if self._inference_enabled:
            self.detnet.close()
            self.detnet_camera.close()
            self.imgnet.close()
            self._inference_enabled = False
        
    def publish_inference_detnet(self, client, userdata, msg):
        '''
        Publish the inference for detnet to Home Assistant
        
        This method publishes the detnet inference to Home Assistant.
        Executed when a message is received on the command topic.
        '''
        img_bytes = BytesIO(msg.payload)
        img = Image.open(img_bytes)
        cuda_img = cudaFromNumpy(asarray(img))
        detections = self._detnet_inference.Detect(cuda_img, overlay="lines,labels,conf")
        out_np = cudaToNumpy(cuda_img)
        cudaDeviceSynchronize()
        out_img = Image.fromarray(out_np)
        img_byte_arr = BytesIO()
        out_img.save(img_byte_arr, format=img.format)
        out_img = img_byte_arr.getvalue()
        # print the detections
        print("detected {:d} objects in image".format(len(detections)))

        if len(detections) > 0:
            for detection in detections:
                print(detection)
                print(self._detnet_inference.GetClassDesc(detection.ClassID))

            self.detnet.publish_state(self._detnet_inference.GetClassDesc(detections[0].ClassID))
            self.detnet_camera.publish_image(out_img)
        else:
            self.detnet.publish_state("None")
        del out_img
        del cuda_img
        del img
        del img_bytes
    
    def start_inference_detnet(self):
        '''
        Start the inference for detnet
        
        This method starts the detnet inference.
        '''
        if self._inference_enabled:
            self._client.subscribe(self.detnet.cmd_topic)
            self._client.message_callback_add(self.detnet.cmd_topic, self.publish_inference_detnet)
        
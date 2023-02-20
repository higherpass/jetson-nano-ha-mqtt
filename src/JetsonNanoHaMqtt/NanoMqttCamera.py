from paho.mqtt.client import Client
from HaMqtt.MQTTUtil import HaDeviceClass
from .mqtt.MQTTCamera import MQTTCamera
from HaMqtt.MQTTSensor import MQTTSensor
from .mqtt.MQTTText import MQTTText
import uuid
from jetson.inference import detectNet, imageNet
from jetson.utils import (videoSource, cudaToNumpy, cudaAllocMapped, cudaCrop, 
                          cudaDeviceSynchronize)
import threading
from PIL import Image
from numpy import asarray
from io import BytesIO
from datetime import datetime
import time
import pytz
import re

class NanoMqttCamera():
    '''
    Nano MQTT Camera

    This class sets up a Nano MQTT Camera.
    '''
    _client = None                      # The MQTT client
    _name = None                        # The name of the camera
    _dev = None                         # The device dictionary
    _camera_enabled = False             # The camera status
    _camera_input = None                # The camera input
    _camera_input_dev = None            # The camera input device
    _camera_output = None               # The camera output
    _camera_output_dev = None           # The camera output device
    _camera_inference_enabled = False   # The camera inference status
    _camera_inference_network = None    # The camera inference network
    _camera_inference_threshold = 0.5   # The camera inference threshold
    _camera_inference = None            # The camera inference object
    camera = None                       # The camera MQTT Entity
    camera_inference = None             # The camera inference MQTT Picture Entity
    camera_inference_labels = None      # The camera inference labels
    camera_inference_timestamp = None   # The camera inference timestamp MQTT Entity
    
    def __init__(self, name: str, client: Client, dev: dict, input: str = None, output: str = None, inference: bool = False, inference_network: str = None, inference_threshold: float = 0.5):
        print("Initializing NanoMqttCamera")
        print("Name: " + name)
        print("inf: " + str(inference))
        print("inf_net: " + str(inference_network))
        print("input: " + str(input))
        self._client = client
        self._name = name
        self._dev = dev
        self._camera_input = input
        self._camera_input_dev = None
        self._camera_output = output
        self._camera_inference_enabled = inference
        self._camera_inference_network = inference_network
        self._camera_inference_threshold = inference_threshold

    def initialize(self):
        '''
        Initialize the camera
        
        This method initializes the Home Assistant MQTT sensors for the camera.
        '''
        if self._camera_input is not None:
            self._camera_input_dev = videoSource(self._camera_input)
            camera_name = re.sub('[^A-Za-z0-9]', '_', self._name)
            self.camera = MQTTCamera(self._name, "jetson_cam_" + camera_name, self._client, unique_id=str(uuid.uuid4()), device_dict=self._dev)
            if self._camera_inference_enabled:
                self.camera_inference_labels = MQTTText(self._name + " Label", "jetson_cam_inference_label_" + camera_name, self._client, unique_id=str(uuid.uuid4()), device_dict=self._dev)
                self.camera_inference_timestamp = MQTTSensor(self._name + " Inference Timestamp", "jetson_cam_inference_timestamp_" + camera_name, self._client, "", HaDeviceClass.TIMESTAMP, unique_id=str(uuid.uuid4()), device_dict=self._dev)
                self.camera_inference = MQTTCamera(self._name + " Inference", "jetson_cam_inference_picture_" + camera_name, self._client, unique_id=str(uuid.uuid4()), device_dict=self._dev) 
                self._camera_inference = detectNet(self._camera_inference_network, threshold=self._camera_inference_threshold)
            self._camera_enabled = True
            return True
        else:
            return False
    
    def close(self):
        '''
        Close the camera
        
        This method closes the Home Assistant MQTT sensors for the camera.
        '''
        if self._camera_enabled:
            self.stop()
            if self._camera_inference_enabled:
                self.cam_motion.close()
                self.cam_motion_timestamp.close()
                self._camera_inference_enabled = False
            self.camera.close()
            self._camera_enabled = False
    
    def publish_camera(self, img):
        '''
        stream the camera snapshot to Home Assistant
        
        This method streams the camera and publishes the snapshot to Home Assistant.
        '''
        if self._camera_inference_enabled:
            if self._camera_inference is not None:
                detections = self._camera_inference.Detect(img, overlay="labels,conf")
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
                    print(self._camera_inference.GetClassDesc(detection.ClassID))
                    if detection.Left < det_left:
                        det_left = detection.Left
                    if detection.Top < det_top:
                        det_top = detection.Top
                    if detection.Right > det_right:
                        det_right = detection.Right
                    if detection.Bottom > det_bottom:
                        det_bottom = detection.Bottom
                roi = (int(det_left), int(det_top), int(det_right), int(det_bottom))
                motion = self._camera_inference.GetClassDesc(detection.ClassID)
                self.camera_inference_labels.publish_state(motion)
                self.camera_inference_timestamp.publish_state(datetime.now(pytz.timezone('US/Central')).isoformat())
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
            img = self._camera_input_dev.Capture()
            self.publish_camera(img)
            time.sleep(frequency)
    
    def start(self, frequency: int = 1):
        '''
        Start the camera
        
        This method starts the camera.
        '''
        if self._camera_enabled:
            self._camera_thread = threading.Thread(target=self.publish_camera_loop, args=(frequency,))
            self._camera_thread.start()
    
    def stop(self):
        '''
        Stop the camera
        
        This method stops the camera.
        '''
        if self._camera_enabled:
            self._camera_thread.join()

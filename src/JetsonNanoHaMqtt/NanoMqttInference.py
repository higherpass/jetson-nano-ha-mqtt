import re
from paho.mqtt.client import Client
from .mqtt.MQTTCamera import MQTTCamera
from .mqtt.MQTTText import MQTTText
import uuid
from jetson.inference import detectNet, imageNet
from jetson.utils import (cudaFromNumpy, cudaToNumpy, cudaDeviceSynchronize, 
                          cudaOverlay)
from PIL import Image
from numpy import asarray
from io import BytesIO

class NanoMqttInference():
    '''
    NanoMqttInference

    This class is used to initialize the inference for the Jetson Nano.
    '''

    _name = None
    _client = None
    _dev = None
    _inference_enabled = False
    _jetson_inference = None
    _inference_network = None
    _inference_threshold:float = 0.5
    _inference = None
    _overlay = None
    _default_overlay_detectNet = "box,labels,conf"
    _default_overlay_poseNet = "links,keypoints"
    _alpha: float = None
    #_default_alpha_segNet: float = 150.0
    _ignore_class: str = None
    #_default_ignore_class_segNet: str = "void"
    _filter_mode: str = None
    #_default_filter_mode_segNet: str = "point"
    #_segNet_buffers = None
    inference_camera: MQTTCamera = None
    inference_label: MQTTText = None

    def __init__(self, name: str, client: Client, dev: dict, jetson_inference, 
                 network: str, threshold: float = 0.5, overlay: str = None,
                 alpha: float = None):
        '''
        Initialize the inference
        
        This method initializes the inference.
        '''
        print(jetson_inference.__name__)
        self._client = client
        self._dev = dev
        self._name = name
        self._jetson_inference = jetson_inference
        self._inference_network = network
        if threshold:
            self._inference_threshold = threshold
        if overlay:
            self._overlay = overlay
        if alpha:
            self._alpha = alpha

    def initialize(self):
        '''
        Initialize the inference
        
        This method initializes the Home Assistant MQTT sensors for the inference.
        '''
        entity_name = re.sub('[^0-0A-Za-z]', '_', self._name)
        print(self._jetson_inference.__name__)
        if self._jetson_inference.__name__ == "imageNet":
            self._inference = self._jetson_inference(self._inference_network)
        elif self._jetson_inference.__name__ in ["detectNet", "poseNet"]:
            self._inference = self._jetson_inference(self._inference_network, threshold=self._inference_threshold)
        else:
            raise Exception("Inference not supported")
        
        self.inference_label = MQTTText(self._name + " Inference", "jetson_inference_" + entity_name, self._client, unique_id=str(uuid.uuid4()), device_dict=self._dev)
        self.inference_camera = MQTTCamera(self._name + " Inference Camera", "jetson_inference_camera_" + entity_name, self._client, unique_id=str(uuid.uuid4()), device_dict=self._dev)
        self._inference_enabled = True

    def close(self):
        '''
        Close the inference
        
        This method closes the Home Assistant MQTT sensors for the inference.
        '''
        if self._inference_enabled:
            self.inference_camera.close()
            self.inference_label.close()
            self.stop()
            self._inference_enabled = False
        
    def publish_inference(self, client, userdata, msg):
        '''
        Publish the inference to Home Assistant
        
        This method publishes the inference to Home Assistant.
        Executed when a message is received on the command topic.
        '''
        img_bytes = BytesIO(msg.payload)
        img = Image.open(img_bytes)
        print("Image received: " + self._jetson_inference.__name__)
        print(img.size)
        cuda_img = cudaFromNumpy(asarray(img))
        out_img: Image = None
        if self._jetson_inference.__name__ == "detectNet":
            detections = self._inference.Detect(cuda_img, overlay="lines,labels,conf")
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
                    print(self._inference.GetClassDesc(detection.ClassID))

                self.inference_label.publish_state(self._inference.GetClassDesc(detections[0].ClassID))
                self.inference_camera.publish_image(out_img)
            else:
                self.inference_label.publish_state("None")
            del out_img
        elif self._jetson_inference.__name__ == "imageNet":
            class_id, confidence = self._inference.Classify(cuda_img)
            self.inference_label.publish_state(self._inference.GetClassDesc(class_id))
            self.inference_camera.publish_image(img_bytes.getvalue())
        elif self._jetson_inference.__name__ == "poseNet":
            if self._overlay is None:
                self._overlay = self._default_overlay_poseNet
            poses = self._inference.Process(cuda_img, overlay=self._overlay)

            # print the pose results
            print("detected {:d} objects in image".format(len(poses)))
            
            for pose in poses:
                print(pose)
                print(pose.Keypoints)
                print('Links', pose.Links)

            out_np = cudaToNumpy(cuda_img)
            cudaDeviceSynchronize()
            out_img = Image.fromarray(out_np)
            img_byte_arr = BytesIO()
            out_img.save(img_byte_arr, format=img.format)
            out_img = img_byte_arr.getvalue()

            self.inference_label.publish_state(len(poses))
            self.inference_camera.publish_image(out_img)

            del poses

        del cuda_img
        del img
        del img_bytes
    
    def start(self):
        '''
        Start the inference listener
        
        This method starts the inference listener.  It subscribes to the 
        command topic and sets the callback for the message.
        '''
        if self._inference_enabled:
            self._client.subscribe(self.inference_label.cmd_topic)
            self._client.message_callback_add(self.inference_label.cmd_topic, self.publish_inference)
    
    def stop(self):
        '''
        Stop the inference
        
        This method stops the inference listener.  It unsubscribes to the
        command topic and removes the callback for the message.
        '''
        if self._inference_enabled:
            self._client.unsubscribe(self.inference_label.cmd_topic)
            self._client.message_callback_remove(self.inference_label.cmd_topic)

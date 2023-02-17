from paho.mqtt.client import Client
from HaMqtt.MQTTDevice import MQTTDevice
import uuid

class MQTTCamera(MQTTDevice):
    '''
    MQTT Camera device
    
    Sets up an MQTT camera device that can be used with Home Assistant.
    '''
    device_type = "camera"

    def __init__(self, name: str, node_id, client: Client, unique_id: str = str(uuid.uuid4()), device_dict=None):
        super().__init__(name, node_id, client, unique_id=unique_id, device_dict=device_dict)

    def initialize(self):
        self.topic = f'{self.base_topic}/state'
        self.camera_topic = f'{self.base_topic}/camera'
        self.add_config_option("topic", self.camera_topic)
        self.add_config_option("image_encoding", "b64")
    
    def publish_image(self, image):
        self._client.publish(self.camera_topic, image)
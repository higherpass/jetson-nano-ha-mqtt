from paho.mqtt.client import Client
from HaMqtt.MQTTDevice import MQTTDevice
import uuid

class MQTTText(MQTTDevice):
    '''
    MQTT Text device

    Sets up an MQTT text device that can be used with Home Assistant.
    '''
    device_type = "text"
    initial_text = ""

    def __init__(self, name: str, node_id: str, client: Client, unique_id: str = str(uuid.uuid4()), device_dict=None):
        self.state = self.__class__.initial_text
        self.cmd_topic = ""
        self.state_topic = ""
        super().__init__(name, node_id, client, unique_id=unique_id, device_dict=device_dict)

    def close(self):
        self._client.unsubscribe(self.cmd_topic)
        super(MQTTText, self).close()

    def initialize(self):
        self.cmd_topic = f'{self.base_topic}/text/cmd'
        self.state_topic = f'{self.base_topic}/text/state'
        self.add_config_option("mode", "text")


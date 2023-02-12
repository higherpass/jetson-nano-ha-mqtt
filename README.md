# Jetson Nano Home Asisstant MQTT Device

Turn a Nvidia Jetson Nano into a MQTT Device in Home Assistant.

## Prerequisites

### Home Assistant

An installation of Home Assistant is required.  Home Assistant needs to be configured with the MQTT integration connected to the MQTT broker.

### MQTT Broker

An MQTT broker such as Mosquitto.  Currently the MQTT broker needs to allow anonymous connections (TODO).

### Python Modules Used

The jetson_stats and paho-mqtt packages are leveraged to provide the Jetson hardware and MQTT functionality.  These packages are installed by the Python module.  

* [jetson_stats](https://github.com/rbonghi/jetson_stats)
* [paho-mqtt](https://pypi.org/project/paho-mqtt/)

## Installation

### Python Module

```bash
git clone https://github.com/higherpass/jetson-nano-ha-mqtt.git
cd jetson-nano-ha-mqtt
make build
python3 -m pip install dist/jetson-nano-ha-mqtt-0.0.1.tar.gz
```

## Usage

### Docker Container

The Docker container will be the easiest way to get started once it's built.

### Python Module

The Python module can be used to create a custom script to publish the Jetson hardware sensors to MQTT.

```python
from JetsonNanoHaMqtt import JetsonNanoHaMqtt
from jtop import jtop
from paho.mqtt.client import Client
import time

client = Client("testscript")
client.connect("IP_ADDRESS_OR_HOSTNAME_HERE", MQTT_PORT_NUMBER_HERE)
client.loop_start()

with jtop() as jetson:
    ha_jetson = JetsonNanoHaMqtt('Jetson Nano', client, jetson)
    ha_jetson.initialize_device(jetson)
    ha_jetson.initialize_hardware_sensors()
    while jetson.ok():
        ha_jetson.publish_hardware_sensors(jetson)
        time.sleep(5)
```

## Home Assitant Devices and Sensors

The following devices and sensors are created in Home Assistant under the MQTT integration.  The Nano itself is a device and the sensors are entities under the device.

### Jetson Hardware

The [jetson_stats](https://github.com/rbonghi/jetson_stats) package provides a monitoring service for the Jetson hardware.

|Name|Type|Details|
|----|----|-------|
|Jetson CPU1|MQTT Sensor|CPU1 % Utilization|
|Jetson CPU2|MQTT Sensor|CPU2 % Utilization|
|Jetson CPU3|MQTT Sensor|CPU3 % Utilization|
|Jetson CPU4|MQTT Sensor|CPU4 % Utilization|
|Jetson GPU1|MQTT Sensor|GPU1 % Utilization|
|Jetson Fan|MQTT Sensor|Fan Speed %|
|Jetson Temp AO|MQTT Thermometer|Jetson AO Temperature Sensor degrees C|
|Jetson Temp CPU|MQTT Thermometer|Jetson CPU Temperature Sensor degrees C|
|Jetson Temp GPU|MQTT Thermometer|Jetson GPU Temperature Sensor degrees C|
|Jetson Temp PLL|MQTT Thermometer|Jetson PLL Temperature Sensor degrees C|
|Jetson Temp Thermal|MQTT Thermometer|Jetson Thermal Temperature Sensor degrees C|
|Jetson Power Current|MQTT Sensor|Jetson current power consumption (mW)|
|Jetson Power Average|MQTT Sensor|Jetson average power consumption (mW)|

### MQTT Camera

Create a Home Assistant MQTT Camera device from a video input.

|Name|Type|Details|
|----|----|-------|
|Jetson Camera|MQTT Camera|Home Assistant MQTT Camera device from a video input (e.g. USB webcam) from the jetson-inference libraries|
|Jetson Camera Motion|MQTT Binary Sensor|Motion detection from the Jetson Camera|

## TODO

* Fix jetson_stats version.  Currently set on version installed on my Nano.
* Add tests
* Docker container
* Add Inferences
  * DetectNet
  * ImageNet
  * SegNet
  * Each inference should have a MQTT camera to render the image
  * Each inference should have a MQTT text sensor to display the results
* Add more sensors
* Convert camera motion sensor away from a binary switch
* Add a MQTT switch to enable/disable the camera
* Add a MQTT switch to enable/disable the camera motion sensor
* Add a MQTT switch to enable/disable the inferences
* Add a MQTT button to shutdown the Jetson
* Add a MQTT button to reboot the Jetson
* Add a MQTT button to take a camera snapshot
* Default executable to run
* Command line arguments
* MQTT Authentication

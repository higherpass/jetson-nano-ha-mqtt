# Jetson Nano Home Asisstant MQTT Device

Turn a Nvidia Jetson Nano into a MQTT Device in Home Assistant.  This is an early stage project.  See the Limitations, Known Issues, and TODO sections for more details.

## Prerequisites

### Home Assistant

An installation of Home Assistant is required.  Home Assistant needs to be configured with the MQTT integration connected to the MQTT broker.

### MQTT Broker

An MQTT broker such as Mosquitto.  Currently the MQTT broker needs to allow anonymous connections (TODO).

### Python Modules Used

The jetson_stats and paho-mqtt packages are leveraged to provide the Jetson hardware and MQTT functionality.  The homeassistant-mqtt-binding package is used to create the Home Assistant devices and sensors.  OpenCV is used to render camera images.  These packages are installed by the Python module.  

* [jetson_stats](https://github.com/rbonghi/jetson_stats)
* [paho-mqtt](https://pypi.org/project/paho-mqtt/)
* [homeassistant-mqtt-binding](https://gitlab.com/anphi/homeassistant-mqtt-binding)
* [Pillow](https://pypi.org/project/Pillow/)

## Installation

### Python Module

The python module should be installed in the environment where the [jetson-inference](https://github.com/dusty-nv/jetson-inference) libraries are installed.  The jetson-inference libraries are required to run the inferences.  

It's easier to build the python package on the Jetson Nano host OS then copy into the Docker container and install.

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
#!/usr/bin/env python3

from JetsonNanoHaMqtt import JetsonNanoHaMqtt
from jtop import jtop
from jetson.inference import detectNet, imageNet, poseNet
from paho.mqtt.client import Client

# Setup MQTT client
client = Client("testscript")
client.connect("MQTT_HOSTNAME", 1883)
client.loop_start()

with jtop() as jetson:
    ha_jetson = JetsonNanoHaMqtt('Jetson Nano', client, jetson)
    ha_jetson.initialize_device(jetson)
    ha_jetson.initialize_hardware_sensors() 
    ha_jetson.initialize_camera("Jetson Camera", client, input="/dev/video0", 
                                inference=True, inference_network="ssd-mobilenet-v2", 
                                inference_threshold=0.5)
    ha_jetson.initialize_camera("RTSP Camera", client, input="rtsp://LOGIN:PASSWORD@RTSP_HOSTNAME:RTSP_PORT/STREAM_NAME", 
                                inference=True, inference_network="pednet", 
                                inference_threshold=0.5)
    ha_jetson.initialize_inference("detectNet", client, detectNet, 
                                   network="ssd-mobilenet-v2")
    ha_jetson.initialize_inference("imageNet", client, imageNet, 
                                   network="googlenet")
    ha_jetson.initialize_inference("poseNet", client, poseNet, 
                                   network="resnet18-body")
    ha_jetson.start()
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

### Camera Input

Create a Home Assistant MQTT Camera device from a video input.

|Name|Type|Details|
|----|----|-------|
|Jetson Camera|MQTT Camera|Home Assistant MQTT Camera device from a video input (e.g. USB webcam) from the jetson-inference libraries|
|Jetson Camera Inference Label|MQTT Text|Detection inference from Camera image|
|Jetson Camera Inference Output|MQTT Camera|Home Assistant MQTT Camera device with cropped output from the Jetson inference detectnet libraries|
|Jetson Camera Inference Timestamp|MQTT Sensor|Timestamp of the last detection|

Multiple cameras are supported.  Initializing the camera will create the MQTT Camera device, a MQTT Text device for the inference label, a MQTT Camera device for the inference output, and a MQTT Sensor device for the inference timestamp.

```python
ha_jetson.initialize_camera("CAMERA_NAME", client, input="/dev/video0", 
                            inference=True, inference_network="ssd-mobilenet-v2", 
                            inference_threshold=0.5)
``` 

When initializing the camera, the following parameters are available:
* `CAMERA_NAME` - The name of the camera.  This will be used to create the MQTT Camera device. (Required)
* `client` - The MQTT client to use. (Required)
* `input` - The input to use.  This can be a video device (e.g. /dev/video0) or an RTSP stream (e.g. rtsp://LOGIN:PASSWORD@RTSP_HOSTNAME:RTSP_PORT/STREAM_NAME). (Required)
* `inference` - Whether to perform inference on the camera input. (Optional, default: False)
* `inference_network` - The inference network to use.  
* `inference_threshold` - The inference threshold to use. (Optional, default: 0.5)

### Inferences

Provide inference from images sent to the Jetson via MQTT.  The inference results are published to MQTT.  These leverage the [jetson-inference](https://github.com/dusty-nv/jetson-inference) libraries inference interfaces.

**Currently only detectNet, imageNet, and poseNet are supported.**  

|Name|Type|Details|
|----|----|-------|
|Jetson Inference Camera|MQTT Camera|Home Assistant MQTT Camera device with output from the Jetson inference|
|Jetson Image Inference Label|MQTT Text|Image inference from image sent to MQTT command topic|

Multiple inferences are supported.  Initializing the inference will create the MQTT Camera device and a MQTT Text device for the inference label.

```python
ha_jetson.initialize_inference("INFERENCE_NAME", client, INFERENCE_NETWORK, 
                               network="ssd-mobilenet-v2")
``` 

When initializing the inference, the following parameters are available:
* `INFERENCE_NAME` - The name of the inference.  This will be used to create the MQTT Camera device. (Required)
* `client` - The MQTT client to use. (Required)
* `INFERENCE_NETWORK` - The inference class to use.  This can be detectNet, imageNet, or poseNet. (Required)
* `network` - The inference network to use.

## Limitations

* Currently only detectNet, imageNet, and poseNet are supported.  Other inferences may be added in the future.
* Configuring the inference network is currently limited to the network name.
* No configuration of output image.

## Known Issues

* Attempting to run too many inferences at the same time may cause the Jetson to crash, hang, or invoke the OOM Killer.

## TODO

* Fix jetson_stats version.  Currently set on version installed on my Nano.
* Add tests
* Docker container
* Add Inferences
  * SegNet
  * depthNet
* Add more sensors
* Add a MQTT switch to enable/disable the cameras
* Add a MQTT switch to enable/disable the camera inferences
* Add a MQTT switch to enable/disable the inferences
* Add a MQTT button to shutdown the Jetson
* Add a MQTT button to reboot the Jetson
* Add a MQTT button to take a camera snapshot
* Default executable to run
* Command line arguments
* MQTT Authentication
* Enhance camera inference setup
  * Add a MQTT switch to enable/disable the inference camera
* Use Inference class inside the camera class
* Configurable output image
* Add filtering of inference responses

## Disclaimer

No warranty is expressed or implied.  Use at your own risk.  I am not responsible for any damage or loss of data or anything else.

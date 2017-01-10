import argparse
import logging
import socket
import sys

import paho.mqtt.client as paho

from defaults import FORMAT_DEFAULT
from mqtt_utils import CAMERA_NAME
from mqtt_utils import mqtt_server_info


def on_connect(client, userdata, flags, rc):
    print("Connected with result code: {0}".format(rc))
    client.subscribe("/{0}/#".format(userdata[CAMERA_NAME]))


def on_disconnect(client, userdata, rc):
    print("Disconnected with result code: {0}".format(rc))


def on_message(client, userdata, msg):
    print("{0} {1}".format(msg.topic, msg.payload))


if __name__ == "__main__":
    # Parse CLI args
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--grpc", required=True, help="gRPC location server hostname")
    parser.add_argument("-m", "--mqtt", required=True, help="MQTT server hostname")
    parser.add_argument("-c", "--camera", required=True, help="Camera name")
    args = vars(parser.parse_args())

    # Setup logging
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format=FORMAT_DEFAULT)

    # Determine MQTT server details
    mqtt_hostname, mqtt_port = mqtt_server_info(args["mqtt"])

    # Create userdata dictionary
    userdata = {CAMERA_NAME: args["camera"]}

    # Initialize MQTT client
    client = paho.Client(userdata=userdata)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    try:
        # Connect to MQTT server
        logging.info("Connecting to MQTT server at {0}:{1}".format(mqtt_hostname, mqtt_port))
        client.connect(mqtt_hostname, port=mqtt_port, keepalive=60)
        client.loop_forever()
    except socket.error:
        logging.error("Cannot connect to MQTT server at: {0}:{1}".format(mqtt_hostname, mqtt_port))
    except KeyboardInterrupt:
        pass

    print("Exiting...")

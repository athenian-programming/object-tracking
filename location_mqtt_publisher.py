#!/usr/bin/env python2

import argparse
import logging
import socket
import sys
from threading import Thread

import paho.mqtt.client as paho

from defaults import FORMAT_DEFAULT
from location_client import LocationClient
from mqtt_utils import CAMERA_NAME
from mqtt_utils import mqtt_server_info


def on_connect(client, userdata, flags, rc):
    print("Connected with result code: {0}".format(rc))
    Thread(target=publish_locations, args=(client, userdata)).start()


def on_disconnect(client, userdata, rc):
    print("Disconnected with result code: {0}".format(rc))


def on_publish(client, userdata, mid):
    print("Published message id: {0}".format(mid))


def publish_locations(client, userdata):
    while True:
        x_loc, y_loc = locations.get_xy()
        result, mid = client.publish("/{0}/x".format(userdata[CAMERA_NAME]), payload=x_loc[0])
        result, mid = client.publish("/{0}/y".format(userdata[CAMERA_NAME]), payload=y_loc[0])


if __name__ == "__main__":
    # Parse CLI args
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--grpc", required=True, help="gRPC location server hostname")
    parser.add_argument("-m", "--mqtt", required=True, help="MQTT server hostname")
    parser.add_argument("-c", "--camera", required=True, help="Camera name")
    args = vars(parser.parse_args())

    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format=FORMAT_DEFAULT)

    # Determine MQTT server details
    mqtt_hostname, mqtt_port = mqtt_server_info(args["mqtt"])

    # Create userdata dictionary
    userdata = {CAMERA_NAME: args["camera"]}

    # Start location reader in thread
    locations = LocationClient(args["grpc"])
    Thread(target=locations.read_locations).start()

    # Initialize MQTT client
    client = paho.Client(userdata=userdata)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish

    try:
        # Connect to MQTT server
        logging.info("Connecting to MQTT server at {0}:{1}".format(mqtt_hostname, mqtt_port))
        client.connect(mqtt_hostname, port=mqtt_port, keepalive=60)
        client.loop_forever()
    except socket.error:
        logging.error("Cannot connect to MQTT server at: {0}:{1}".format(mqtt_hostname, mqtt_port))
    except KeyboardInterrupt:
        pass
    finally:
        locations.stop()

    print("Exiting...")

#!/usr/bin/env python2

import argparse
import logging
import socket
import sys
from threading import Thread

import paho.mqtt.client as paho

from location_client import LocationClient

__CAMERA_NAME = "camera_name"


def on_connect(client, userdata, flags, rc):
    print("Connected with result code: {0}".format(rc))
    Thread(target=publish_locations, args=(client, userdata)).start()


def on_disconnect(client, userdata, flags, rc):
    print("Disconnected with result code: {0}".format(rc))


def on_publish(client, userdata, mid):
    print("Published message id: {0}".format(mid))


def publish_locations(client, userdata):
    while True:
        x_loc, y_loc = locations.get_xy()
        (result, mid) = client.publish("/{0}/x".format(userdata[__CAMERA_NAME]), payload=x_loc[0])
        (result, mid) = client.publish("/{0}/y".format(userdata[__CAMERA_NAME]), payload=y_loc[0])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--grpc", required=True, help="gRPC location server hostname")
    parser.add_argument("-m", "--mqtt", required=True, help="MQTT server hostname")
    parser.add_argument("-c", "--camera", required=True, help="Camera name")
    args = vars(parser.parse_args())

    logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                        format="%(asctime)s %(name)-10s %(funcName)-10s():%(lineno)i: %(levelname)-6s %(message)s")

    locations = LocationClient(args["grpc"])

    if ":" in args["mqtt"]:
        mqtt_hostname = args["mqtt"][:args["mqtt"].index(":")]
        mqtt_port = int(args["mqtt"][args["mqtt"].index(":") + 1:])
    else:
        mqtt_hostname = args["mqtt"]
        mqtt_port = 1883

    userdata = {__CAMERA_NAME: args["camera"]}

    Thread(target=locations.read_locations).start()

    client = paho.Client()
    client.user_data_set(userdata)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish

    try:
        logging.info("Connecting to MQTT server at {0}".format(args["mqtt"]))
        client.connect(mqtt_hostname, port=mqtt_port, keepalive=60)
        client.loop_forever()
    except socket.error:
        logging.error("Cannot connect to MQTT server at: {0}:{1}".format(mqtt_hostname, mqtt_port))
    except KeyboardInterrupt:
        pass
    finally:
        locations.stop()

    print("Exiting...")

#!/usr/bin/env python2

import argparse
import logging
from logging import info
from threading import Thread

from common_constants import CAMERA_NAME
from common_constants import LOGGING_ARGS
from common_utils import mqtt_broker_info
from common_utils import sleep
from location_client import LocationClient
from mqtt_connection import MqttConnection

if __name__ == "__main__":
    # Parse CLI args
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--grpc", required=True, help="gRPC location server hostname")
    parser.add_argument("-c", "--camera", required=True, help="Camera name")
    parser.add_argument("-m", "--mqtt", required=True, help="MQTT server hostname")
    args = vars(parser.parse_args())

    # Setup logging
    logging.basicConfig(**LOGGING_ARGS)

    # Start location reader
    locations = LocationClient(args["grpc"]).start()


    # Define MQTT callbacks
    def on_connect(client, userdata, flags, rc):
        info("Connected with result code: {0}".format(rc))
        Thread(target=publish_locations, args=(client, userdata)).start()


    def on_disconnect(client, userdata, rc):
        info("Disconnected with result code: {0}".format(rc))


    def on_publish(client, userdata, mid):
        print("Published message id: {0}".format(mid))


    def publish_locations(client, userdata):
        while True:
            x_loc, y_loc = locations.get_xy()
            if x_loc is not None and y_loc is not None:
                result, mid = client.publish("{0}/x".format(userdata[CAMERA_NAME]), payload=x_loc[0])
                result, mid = client.publish("{0}/y".format(userdata[CAMERA_NAME]), payload=y_loc[0])


    # Setup MQTT client
    hostname, port = mqtt_broker_info(args["mqtt"])
    mqtt_conn = MqttConnection(hostname, port, userdata={CAMERA_NAME: args["camera"]})
    mqtt_conn.client.on_connect = on_connect
    mqtt_conn.client.on_disconnect = on_disconnect
    mqtt_conn.client.on_publish = on_publish
    mqtt_conn.connect()

    try:
        sleep()
    except KeyboardInterrupt:
        mqtt_conn.disconnect()
    finally:
        locations.stop()

    print("Exiting...")

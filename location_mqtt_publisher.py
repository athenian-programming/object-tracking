#!/usr/bin/env python2

import logging
from threading import Thread

import cli_args  as cli
from cli_args import setup_cli_args
from constants import CAMERA_NAME
from location_client import LocationClient
from mqtt_connection import MqttConnection
from utils import mqtt_broker_info
from utils import setup_logging
from utils import sleep

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Parse CLI args
    args = setup_cli_args(cli.grpc_host, cli.mqtt_host, cli.camera_name, cli.verbose)

    # Setup logging
    setup_logging(args["loglevel"])

    # Start location reader
    locations = LocationClient(args["grpc_host"]).start()


    # Define MQTT callbacks
    def on_connect(client, userdata, flags, rc):
        logger.info("Connected with result code: {0}".format(rc))
        Thread(target=publish_locations, args=(client, userdata)).start()


    def on_disconnect(client, userdata, rc):
        logger.info("Disconnected with result code: {0}".format(rc))


    def on_publish(client, userdata, mid):
        print("Published message id: {0}".format(mid))


    def publish_locations(client, userdata):
        while True:
            x_loc, y_loc = locations.get_xy()
            if x_loc is not None and y_loc is not None:
                result, mid = client.publish("{0}/x".format(userdata[CAMERA_NAME]), payload=x_loc[0])
                result, mid = client.publish("{0}/y".format(userdata[CAMERA_NAME]), payload=y_loc[0])


    # Setup MQTT client
    hostname, port = mqtt_broker_info(args["mqtt_host"])
    mqtt_conn = MqttConnection(hostname, port, userdata={CAMERA_NAME: args["camera_name"]})
    mqtt_conn.client.on_connect = on_connect
    mqtt_conn.client.on_disconnect = on_disconnect
    mqtt_conn.client.on_publish = on_publish
    mqtt_conn.connect()

    try:
        sleep()
    except KeyboardInterrupt:
        pass
    finally:
        mqtt_conn.disconnect()
        locations.stop()

    logger.info("Exiting...")

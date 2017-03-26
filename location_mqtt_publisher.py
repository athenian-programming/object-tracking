#!/usr/bin/env python2

import logging
from threading import Thread

import cli_args  as cli
from cli_args import CAMERA_NAME, LOG_LEVEL, MQTT_HOST, GRPC_HOST
from cli_args import setup_cli_args
from location_client import LocationClient
from mqtt_connection import MqttConnection
from utils import setup_logging
from utils import sleep

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Parse CLI args
    args = setup_cli_args(cli.grpc_host, cli.mqtt_host, cli.camera_name, cli.verbose)

    # Setup logging
    setup_logging(level=args[LOG_LEVEL])

    # Start location reader
    with LocationClient(args[GRPC_HOST]) as client:

        # Define MQTT callbacks
        def on_connect(client, userdata, flags, rc):
            logger.info("Connected with result code: {0}".format(rc))
            Thread(target=publish_locations, args=(client, userdata)).start()


        def publish_locations(client, userdata):
            while True:
                x_loc, y_loc = client.get_xy()
                if x_loc is not None and y_loc is not None:
                    result, mid = client.publish("{0}/x".format(userdata[CAMERA_NAME]), payload=x_loc[0])
                    result, mid = client.publish("{0}/y".format(userdata[CAMERA_NAME]), payload=y_loc[0])


        # Setup MQTT client
        with MqttConnection(args[MQTT_HOST],
                            userdata={CAMERA_NAME: args[CAMERA_NAME]},
                            on_connect=on_connect):
            try:
                sleep()
            except KeyboardInterrupt:
                pass

    logger.info("Exiting...")

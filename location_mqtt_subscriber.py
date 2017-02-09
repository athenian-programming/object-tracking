import logging

import cli_args  as cli
from cli_args import setup_cli_args
from constants import CAMERA_NAME
from mqtt_connection import MqttConnection
from utils import setup_logging
from utils import sleep

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Parse CLI args
    args = setup_cli_args(cli.grpc_host, cli.mqtt_host, cli.camera_name, cli.verbose)

    # Setup logging
    setup_logging(level=args["loglevel"])


    # Define MQTT callbacks
    def on_connect(client, userdata, flags, rc):
        logger.info("Connected with result code: {0}".format(rc))
        client.subscribe("{0}/#".format(userdata[CAMERA_NAME]))


    def on_disconnect(client, userdata, rc):
        logger.info("Disconnected with result code: {0}".format(rc))


    def on_message(client, userdata, msg):
        print("{0} {1}".format(msg.topic, msg.payload))


    # Setup MQTT client
    mqtt_conn = MqttConnection(args["mqtt_host"],
                               userdata={CAMERA_NAME: args["camera_name"]},
                               on_connect=on_connect,
                               on_disconnect=on_disconnect,
                               on_message=on_message)
    mqtt_conn.connect()

    try:
        sleep()
    except KeyboardInterrupt:
        pass
    finally:
        mqtt_conn.disconnect()

    logger.info("Exiting...")

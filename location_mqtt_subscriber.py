import logging

import cli_args  as cli
from cli_args import CAMERA_NAME, MQTT_HOST, LOG_LEVEL
from cli_args import setup_cli_args
from mqtt_connection import MqttConnection
from utils import setup_logging, waitForKeyboardInterrupt

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Parse CLI args
    args = setup_cli_args(cli.grpc_host, cli.mqtt_host, cli.camera_name, cli.verbose)

    # Setup logging
    setup_logging(level=args[LOG_LEVEL])


    # Define MQTT callbacks
    def on_connect(client, userdata, flags, rc):
        logger.info("Connected with result code: {0}".format(rc))
        client.subscribe("{0}/#".format(userdata[CAMERA_NAME]))

    def on_message(client, userdata, msg):
        logger.info("{0} {1}".format(msg.topic, msg.payload))


    # Setup MQTT client
    with MqttConnection(args[MQTT_HOST],
                        userdata={CAMERA_NAME: args[CAMERA_NAME]},
                        on_connect=on_connect,
                        on_message=on_message):
        waitForKeyboardInterrupt()

    logger.info("Exiting...")

import argparse
import logging
from logging import info

from common_constants import CAMERA_NAME
from common_constants import LOGGING_ARGS
from common_utils import mqtt_broker_info
from common_utils import sleep
from mqtt_connection import MqttConnection

if __name__ == "__main__":
    # Parse CLI args
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--grpc", required=True, help="gRPC location server hostname")
    parser.add_argument("-m", "--mqtt", required=True, help="MQTT server hostname")
    parser.add_argument("-c", "--camera", required=True, help="Camera name")
    args = vars(parser.parse_args())

    # Setup logging
    logging.basicConfig(**LOGGING_ARGS)

    # Determine MQTT server details
    mqtt_hostname, mqtt_port = mqtt_broker_info(args["mqtt"])


    # Define MQTT callbacks
    def on_connect(client, userdata, flags, rc):
        info("Connected with result code: {0}".format(rc))
        client.subscribe("{0}/#".format(userdata[CAMERA_NAME]))


    def on_disconnect(client, userdata, rc):
        info("Disconnected with result code: {0}".format(rc))


    def on_message(client, userdata, msg):
        print("{0} {1}".format(msg.topic, msg.payload))


    # Setup MQTT client
    hostname, port = mqtt_broker_info(args["mqtt"])
    mqtt_conn = MqttConnection(hostname, port, userdata={CAMERA_NAME: args["camera"]})
    mqtt_conn.client.on_connect = on_connect
    mqtt_conn.client.on_disconnect = on_disconnect
    mqtt_conn.client.on_message = on_message
    mqtt_conn.connect()

    try:
        sleep()
    except KeyboardInterrupt:
        mqtt_conn.disconnect()

    print("Exiting...")

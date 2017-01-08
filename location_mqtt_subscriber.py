import argparse
import logging
import socket
import sys

import paho.mqtt.client as paho

__CAMERA_NAME = "camera_name"


def on_connect(client, userdata, flags, rc):
    print("Connected with result code: {0}".format(rc))
    client.subscribe("/{0}/#".format(userdata[__CAMERA_NAME]))


def on_disconnect(client, userdata, flags, rc):
    print("Disconnected with result code: {0}".format(rc))


def on_message(client, userdata, msg):
    print("{0} {1}".format(msg.topic, msg.payload))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--grpc", required=True, help="gRPC location server hostname")
    parser.add_argument("-m", "--mqtt", required=True, help="MQTT server hostname")
    parser.add_argument("-c", "--camera", required=True, help="Camera name")
    args = vars(parser.parse_args())

    logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                        format="%(asctime)s %(name)-10s %(funcName)-10s():%(lineno)i: %(levelname)-6s %(message)s")

    if ":" in args["mqtt"]:
        mqtt_hostname = args["mqtt"][:args["mqtt"].index(":")]
        mqtt_port = int(args["mqtt"][args["mqtt"].index(":") + 1:])
    else:
        mqtt_hostname = args["mqtt"]
        mqtt_port = 1883

    userdata = {__CAMERA_NAME: args["camera"]}

    client = paho.Client()
    client.user_data_set(userdata)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    try:
        logging.info("Connecting to MQTT server at {0}".format(args["mqtt"]))
        client.connect(mqtt_hostname, port=mqtt_port, keepalive=60)
        client.loop_forever()
    except socket.error:
        logging.error("Cannot connect to MQTT server at: {0}:{1}".format(mqtt_hostname, mqtt_port))
    except KeyboardInterrupt:
        pass

    print("Exiting...")

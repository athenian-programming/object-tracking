import cli_args as cli
from cli_args import setup_cli_args
from constants import LOG_LEVEL, MQTT_HOST, TOPIC, LED_NAME, LED_BRIGHTNESS_DEFAULT, LED_BRIGHTNESS
from mqtt_connection import MqttConnection
from utils import is_raspi, setup_logging, sleep

if is_raspi():
    from blinkt import set_pixel, show

import logging

logger = logging.getLogger(__name__)


class BlinktSubscriber(object):
    def __init__(self, brightness=LED_BRIGHTNESS_DEFAULT):
        self._brightness = brightness

    def set_leds(self, left_color, right_color):
        if is_raspi():
            for i in range(0, 4):
                set_pixel(i, left_color[2], left_color[1], left_color[0], brightness=self._brightness)
            for i in range(4, 8):
                set_pixel(i, right_color[2], right_color[1], right_color[0], brightness=self._brightness)
            show()

    def clear_leds(self):
        for i in range(8):
            set_pixel(i, 0, 0, 0, brightness=self._brightness)


if __name__ == "__main__":
    # Parse CLI args
    args = setup_cli_args(cli.grpc_host, cli.mqtt_host, cli.led_name, cli.led_brightness, cli.verbose)

    # Setup logging
    setup_logging(level=args[LOG_LEVEL])

    blinkt = BlinktSubscriber(args[LED_BRIGHTNESS])


    # Define MQTT callbacks
    def on_connect(client, userdata, flags, rc):
        logger.info("Connected with result code: {0}".format(rc))
        client.subscribe("leds/{0}".format(userdata[TOPIC]))


    def on_message(client, userdata, msg):
        logger.info("{0} {1}".format(msg.topic, msg.payload))


    # Setup MQTT client
    mqtt_conn = MqttConnection(args[MQTT_HOST],
                               userdata={TOPIC: args[LED_NAME]},
                               on_connect=on_connect,
                               on_message=on_message)
    mqtt_conn.connect()

    try:
        sleep()
    except KeyboardInterrupt:
        pass
    finally:
        mqtt_conn.disconnect()

    logger.info("Exiting...")

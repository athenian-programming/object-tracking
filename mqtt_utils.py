CAMERA_NAME = "camera_name"


def mqtt_server_info(val):
    return (val[:val.index(":")], int(val[val.index(":") + 1:])) if ":" in val else (val, 1883)

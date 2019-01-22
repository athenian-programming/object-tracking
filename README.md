[![Code Health](https://landscape.io/github/athenian-robotics/object-tracking/master/landscape.svg?style=flat)](https://landscape.io/github/athenian-robotics/object-tracking/master)
[![Code Climate](https://codeclimate.com/github/athenian-robotics/object-tracking/badges/gpa.svg)](https://codeclimate.com/github/athenian-robotics/object-tracking)

# OpenCV Object Tracking and Pan/Tilt Servo Control

## Package Dependencies

Using the *pysearchimages* Raspbian distro (which has OpenCV 3.2 bundled),
install the required Python packages with: 

```bash
source start_py2cv3.sh
pip install --upgrade pip
pip install -r pip/requirements.txt
sudo -H pip install arc852-robotics --extra-index-url https://pypi.fury.io/pambrose/
```

Info on arc852-robotics is [here](https://github.com/athenian-robotics/arc852-robotics).

## Color Picker 

color_picker.py is used to choose a target BGR value.

### Usage 

```bash
$ ./color_picker.py 
```

### CLI Options

| Option         | Description                                        | Default        |
|:---------------|----------------------------------------------------|----------------|
| -u, --usb      | Use USB Raspi camera                               | false          |
| -w, --width    | Image width                                        | 400            |
| --display      | Display image                                      | false          |
| -x, --flipx    | Flip image on X axis                               | false          |
| -y, --flipy    | Flip image on Y axis                               | false          |
| --http         | HTTP hostname:port                                 | localhost:8080 |
| --delay        | HTTP delay secs                                    | 0.25           |
| -i, --file     | HTTP template file                                 |                |
| --verbose-http | Enable verbose HTTP log                            | false          |
| -v, --verbose  | Enable debugging output                            | false          |
| -h, --help     | Summary of options                                 |                |

### Display Keystrokes

| Keystroke  | Action                                             |
|:----------:|----------------------------------------------------|
| c          | Print current BGR value to console                 |
| k          | Move ROI up                                        |
| j          | Move ROI down                                      |
| h          | Move ROI left                                      |
| k          | Move ROI right                                     |
| -          | Decrease ROI size                                  |
| +          | Increase ROI size                                  |
| <          | Decrease image size                                |
| >          | Increase image size                                |
| r          | Reset ROI size and image size                      |
| q          | Quit                                               |


## Single Object Tracker

The object_tracker.py script runs the LocationServer, which generates 
the location of the object having the target BGR value. It supplies data to 
clients like servo_controller.py via gRPC. The smaller the image width, the smaller 
the matching target area. Thus, decreasing the image width may require also 
decreasing the minimum target pixel area.

### Usage 

```bash
$ python single_object_tracker.py --bgr "174, 56, 5" --display 
```

### CLI Options

| Option         | Description                                        | Default        |
|:---------------|----------------------------------------------------|----------------|
| --bgr          | BGR target value                                   |                |
| -u, --usb      | Use USB Raspi camera                               | false          |
| -w, --width    | Image width                                        | 400            |
| -e, --percent  | Middle percent                                     | 15             |
| --min          | Minimum target pixel area                          | 100            |
| --range        | HSV Range                                          | 20             |
| --leds         | Enable Blinkt led feedback                         | false          |
| --display      | Display image                                      | false          |
| -x, --flipx    | Flip image on X axis                               | false          |
| -y, --flipy    | Flip image on Y axis                               | false          |
| -t, --http     | HTTP hostname:port                                 | localhost:8080 |
| --delay        | HTTP delay secs                                    | 0.25           |
| -i, --file     | HTTP template file                                 |                |
| -p, --port     | gRPC server port                                   | 50051          |
| --verbose-http | Enable verbose HTTP log                        | false          |
| -v, --verbose  | Enable debugging output                            | false          |
| -h, --help     | Summary of options                                 |                |


### Sample Image

![alt text](https://github.com/pambrose/opencv_object_tracking/raw/master/docs/target_img.png "Object Tracking")


### Display Keystrokes

| Keystroke  | Action                                             |
|:----------:|----------------------------------------------------|
| -          | Decrease center area                               |
| +          | Increase center area                               |
| w          | Decrease image size                                |
| W          | Increase image size                                |
| r          | Reset center area and image size                   |
| s          | Save current image to disk                         |
| q          | Quit                                               |


## FirmataServo Controller

The firmata_controller.py script reads the location values provided by single_object_tracker.py
and adjusts the pan/tilt servos accordingly.

### Usage 

```bash
$ firmata_controller.py --port ttyACM0 --grpc localhost
```

### CLI Options

| Option         | Description                                        | Default |
|:---------------|----------------------------------------------------|---------|
| -s, --serial   | Arduino serial port                                | ttyACM0 |
| -g, --grpc     | Object Tracker gRPC server hostname                |         |
| -x, --xservo   | X servo PWM pin                                    | 5       |
| -y, --xyservo  | Y servo PWM pin                                    | 6       |
| --calib        | Calibration mode                                   | false   |
| -v, --verbose  | Enable debugging output                            | false   |
| -h, --help     | Summary of options                                 |         |



## Relevant Links

### Hardware
* [Raspberry Pi Camera](https://www.adafruit.com/products/3099)
* [Pan/Tilt Kit](https://www.adafruit.com/product/1967)
* [Blinkt](http://www.athenian-robotics.org/blinkt/)

### Software
* [pyfirmata](http://www.athenian-robotics.org/pyfirmata/)
* [gRPC](http://www.athenian-robotics.org/grpc/)
* [OpenCV](http://www.athenian-robotics.org/opencv/)
* [Plot.ly](http://www.athenian-robotics.org/plotly/)


Instructions on how to display Raspi OpenCV camera images on a Mac are 
[here](http://www.athenian-robotics.org/opencv/)
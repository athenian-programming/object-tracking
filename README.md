# OpenCV Object Tracking and Pan/Tilt Servo Control

## Package Dependencies

Install the following Python packages: 

* [gRPC](http://www.grpc.io/docs/guides/index.html) 
as described [here](http://www.athenian-robotics.org/grpc/)

* [OpenCV](http://opencv.org) 
as described [here](http://www.athenian-robotics.org/opencv/)

* [imutils](https://github.com/jrosebr1/imutils)
as described [here](http://www.athenian-robotics.org/imutils/)

* [numpy](http://www.numpy.org)
as described [here](http://www.athenian-robotics.org/numpy/)

* [MQTT](http://mqtt.org) client 
as described [here](http://www.athenian-robotics.org/mqtt-client/)

* [pyfirmata](https://github.com/tino/pyFirmata) client 
as described [here]()

## Color Picker 

color_picker.py is used to choose a target BGR value.

### Usage 

```bash
$ ./color_picker.py 
```

### CLI Options

| Option         | Description                                        | Default |
|:---------------|----------------------------------------------------|---------|
| -w, --width    | Image width                                        | 400     |

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
| q          | Quit                                               |


## Object Tracker

The object_tracker.py script runs the LocationServer, which generates 
the location of the object having the target BGR value. It supplies data to 
clients like servo_controller.py via gRPC. The smaller the image width, the smaller 
the matching target area. Thus, decreasing the image width may require also 
decreasing the minimum target pixel area.

### Usage 

```bash
$ python object_tracker.py --bgr "[174, 56, 5]" --display 
```

### CLI Options

| Option         | Description                                        | Default |
|:---------------|----------------------------------------------------|---------|
| -b, --bgr      | BGR target value                                   |         |
| -w, --width    | Image width                                        | 400     |
| -e, --percent  | Middle percent                                     | 15      |
| -m, --min      | Minimum target pixel area                          | 100     |
| -r, --range    | HSV Range                                          | 20      |
| -d, --display  | Display image                                      | false   |
| -p, --port     | gRPC server port                                   | 50051   |
| -v, --verbose  | Include debugging info                             | false   |
| -h, --help     | Summary of options                                 |         |


### Sample Image

![alt text](https://github.com/pambrose/opencv_object_tracking/raw/master/docs/target_img.png "Object Tracking")


### Display Keystrokes

| Keystroke  | Action                                             |
|:----------:|----------------------------------------------------|
| -          | Decrease center area                               |
| +          | Increase center area                               |
| w          | Decrease image width                               |
| W          | Increase image width                               |
| r          | Reset center area and image width                  |
| p          | Save current image to disk                         |
| q          | Quit                                               |


## Servo Controller

The servo_controller.py script reads the location values provided by object_tracker.py
and adjusts the pan/tilt servos accordingly.

### Usage 

```bash
$ servo_controller.py --port ttyACM0 --grpc localhost
```

### CLI Options

| Option         | Description                                        | Default |
|:---------------|----------------------------------------------------|---------|
| -s, --serial   | Arduino serial port                                | ttyACM0 |
| -g, --grpc     | Object Tracker gRPC server hostname                |         |
| -x, --xservo   | X servo PWM pin                                    | 5       |
| -y, --xyservo  | Y servo PWM pin                                    | 6       |
| -c, --calib    | Calibration mode                                   | false   |
| -v, --verbose  | Include debugging info                             | false   |
| -h, --help     | Summary of options                                 |         |



## Relevant Links

### Hardware
* [Raspberry Pi Camera](https://www.adafruit.com/products/3099)
* [Pan/Tilt Kit](https://www.adafruit.com/product/1967)
* [Blinkt](https://www.adafruit.com/products/3195)

### Software
* [PyCharm IDE](https://www.jetbrains.com/pycharm/)
* [pyfirmata](https://github.com/tino/pyFirmata)
* [gRPC](http://www.grpc.io/docs/tutorials/basic/python.html)
* [OpenCV](https://github.com/opencv/opencv)
* [OpenCV Python Tutorial](http://docs.opencv.org/3.0-beta/doc/py_tutorials/py_tutorials.html)
* [Blinkt Docs](http://docs.pimoroni.com/blinkt/)


## Setup Details

### Displaying Raspi camera images on OSX

1) Set **DISPLAY** env var to use the OSX machine (in this case *my-mac*). 
On the Raspi type:
```bash
$ set DISPLAY my-mac:0
```

2) Start the *[X](https://en.wikipedia.org/wiki/X_Window_System) server* 
[XQuartz](https://www.xquartz.org) on the OSX machine.

3) Add the Raspi host name to enable connections to the X server (in this case *my-raspi*). 
On the OSX machine type:
```bash
$ xhost + my-raspi
my-raspi being added to access control list
```

### Plot.ly

Details on setting up plot.ly are 
[here](http://www.athenian-robotics.org/site/plotly/).

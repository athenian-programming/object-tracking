# OpenCV Object Tracking and Pan/Tilt Servo Control


## Color Picker 

color_picker.py is used to choose a target BGR value.

### Usage 

```bash
$ ./color_picker.py 
```

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

The object_tracker.py script generates the location of the object 
having the target BGR value. It can be run stand-alone or can supply data to 
servo_controller.py via gRPC or HTTP. The smaller the image width, the smaller 
the matching target area. Thus, decreasing the image width may require also 
decreasing the minimum target pixel area.

### Usage 

```bash
$ python object_tracker.py --bgr "[174, 56, 5]" --display --grpc localhost
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
| -g, --grpc     | Servo controller gRPC server hostname              |         |
| -o, --http     | Servo controller HTTP server hostname              |         |
| -t, --test     | Test mode                                          | false   |
| -v, --verbose  | Include debugging info                             | false   |
| -h, --help     | Summary of options                                 |         |


### Display Keystrokes

| Keystroke  | Action                                             |
|:----------:|----------------------------------------------------|
| -          | Decrease center area                               |
| +          | Increase center area                               |
| j          | Decrease image width                               |
| k          | Increase image width                               |
| r          | Reset center area and image width                  |
| s          | Print center area dimensions to conole             |
| p          | Save current frame to disk                         |
| q          | Quit                                               |


## Servo Controller

The servo_controller.py script reads the location values provided by object_tracker.py
and adjusts the pan/tilt servos accordingly.

### Usage 

```bash
$ python servo_controller.py --port ttyACM0 --grpc
```

### CLI Options

| Option         | Description                                        | Default |
|:---------------|----------------------------------------------------|---------|
| -g, --grpc     | Use gRPC server to read locations                  | false   |
| -o, --http     | Use HTTP server to read locations                  | false   |
| -t, --test     | Test mode                                          | false   |
| -c, --calib    | Calibration mode                                   | false   |
| -p, --port     | Arduino serial port                                | ttyACM0 |
| -x, --xservo   | X servo PWM pin                                    | 5       |
| -y, --xyservo  | Y servo PWM pin                                    | 6       |
| -v, --verbose  | Include debugging info                             | false   |
| -h, --help     | Summary of options                                 |         |


## Relevant Links

### Hardware
* [Raspberry Pi Camera](https://www.adafruit.com/products/3099)
* [Pan/Tilt Kit](https://www.adafruit.com/product/1967)
* [Blinkt](https://www.adafruit.com/products/3195)

### Software
* [PyCharm IDE](https://www.jetbrains.com/pycharm/)
* [Pyfirmata](https://github.com/tino/pyFirmata)
* [Blinkt docs](http://docs.pimoroni.com/blinkt/)
* [Flask](http://flask.pocoo.org)
* [gRPC](http://www.grpc.io/docs/tutorials/basic/python.html)
* [OpenCV Python Tutorial](http://docs.opencv.org/3.0-beta/doc/py_tutorials/py_tutorials.html)

### System
* [Installing OpenCV3 with Python 2.7 on Sierra](http://www.pyimagesearch.com/2016/11/28/macos-install-opencv-3-and-python-2-7/)
* [OpenCV](https://github.com/opencv/opencv)


## Setup Details

### Displaying Raspi camera images on OSX

1) Set **DISPLAY** env var on the Raspi to use the OSX machine (in this case *pleiku*).
```bash
$ set DISPLAY pleiku:0
```

2) Run the [X](https://en.wikipedia.org/wiki/X_Window_System) server [XQuartz](https://www.xquartz.org) 
on the OSX machine.

3) Add the Raspi host name (in this case *raspi11*) to enable connections to the X server on the OSX machine.
```bash
$ xhost + raspi11
```

# OpenCV Object Tracking 


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



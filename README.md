# OpenCV Object Tracking 


## Color Picker 

color_picker.py is used to choose a target BGR value.

```bash
$ ./color_picker.py 
```

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

object_tracker.py provides the location of the largest object having the 
target BGR value. It can be run stand-alone or can supply data to s
ervo_controller.py via gRPC or HTTP. The smaller the image width, the smaller 
the target area. Thus, decreasing the image width may require also decreasing 
the minimum taerget pixel area.

```bash
$ ./object_tracker.py 
```

| CLI Args       | Description                                        | Default |
|:---------------|----------------------------------------------------|---------|
| -b, --bgr      | BGR target value, e.g., -b "[174, 56, 5]"          |         |
| -w, --width    | Image width                                        | 400     |
| -p, --percent  | Middle percent                                     | 15      |
| -m, --min      | Minimum target pixel area                          | 100     |
| -r, --range    | HSV Range                                          | 20      |
| -d, --display  | Display image                                      | false   |
| -g, --grpc     | Run gRPC server                                    | false   |
| -h, --hostname | Servo controller hostname                          |         |
| -t, --test     | Test mode                                          | false   |
| -v, --verbose  | Include debugging info                             | false   |


## Servo Controller

```bash
$ ./servo_controller.py 
```


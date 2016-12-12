# OpenCV Object Tracking 


## Choose a target BGR value 

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

```bash
$ ./object_tracker.py 
```

| CLI Args       | Description                                        | Default |
|:---------------|----------------------------------------------------|---------|
| -b, --bgr      | BGR target value, e.g., -b "[174, 56, 5]"          |         |
| -w, --width    | Image width                                        | 400     |
| -r, --ranhge   | HSV Range                                          | 20      |
| -d, --display  | Display image                                      | false   |
| -g, --grpc     | Run gRPC server                                    | false   |
| -h, --hostname | Servo controller hostname                          | ""      |
| -t, --test     | Test mode                                          | false   |
| -v, --verbose  | Include debugging info                             | false   |

The object_tracker can be run stand-alone or can supply data to the servo_controller 
via gRPC or HTTP.

## Servo Controller

```bash
$ ./servo_controller.py 
```


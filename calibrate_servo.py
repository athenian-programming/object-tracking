def calibrate(locations, servo_x, servo_y):
    def center_servos():
        servo_x.write_pin(90)
        servo_y.write_pin(90)

    name = "x"
    servo = servo_x

    # This is a hack to get around python3 not having raw_input
    try:
        input = raw_input
    except NameError:
        pass

    while True:
        try:
            key = input("{0} {1} ({2}, {3})> ".format(name.upper(),
                                                      servo.read_pin(),
                                                      locations.get_loc("x"),
                                                      locations.get_loc("y")))
        except KeyboardInterrupt:
            return

        pause = 0.25

        if key == "?":
            print("Valid commands:")
            print("     x      : set current server to pan servo")
            print("     y      : set current server to tilt servo")
            print("     g      : advance current servo one location response")
            print("     s      : run scan on current servo")
            print("     c      : center current servo")
            print("     C      : center both servos")
            print("     +      : increase current servo position 1 degree")
            print("     -      : decrease current servo position 1 degree")
            print("     number : set current servo position number degree")
            print("     ?      : print summary of commands")
            print("     q      : quit")
        elif key == "c":
            servo.write_pin(90)
        elif key == "C":
            center_servos()
        elif key == "x":
            name = "x"
            servo = servo_x
        elif key == "y":
            name = "y"
            servo = servo_y
        elif key == "g":
            servo.ready_event.set()
        elif key == "l":
            servo.write_pin(90)
            servo_pos = 90
            img_start = locations.get_loc(name)
            img_last = -1
            for i in range(90, 0, -1):
                servo.write_pin(i, pause)
                img_pos = locations.get_loc(name)
                if img_pos == -1:
                    break
                img_last = img_pos
                servo_pos = i
            pixels = img_start - img_last
            degrees = 90 - servo_pos
            ppd = abs(float(pixels / degrees))
            print("{0} pixels {1} degrees from center to left edge at pos {2} {3} pix/deg".format(pixels,
                                                                                                  degrees,
                                                                                                  servo_pos,
                                                                                                  ppd))
        elif key == "r":
            servo.write_pin(90)
            servo_pos = 90
            img_start = locations.get_loc(name)
            img_last = -1
            for i in range(90, 180):
                servo.write_pin(i, pause)
                img_pos = locations.get_loc(name)
                if img_pos == -1:
                    break
                img_last = img_pos
                servo_pos = i
            pixels = img_last - img_start
            degrees = servo_pos - 90
            ppd = abs(float(pixels / degrees))
            print("{0} pixels {1} degrees from center to left edge at pos {2} {3} pix/deg"
                  .format(pixels, degrees, servo_pos, ppd))
        elif key == "s":
            center_servos()
            servo.write_pin(0)

            start_pos = -1
            end_pos = -1
            for i in range(0, 180, 1):
                servo.write_pin(i, pause)
                if locations.get_loc(name) != -1:
                    start_pos = i
                    print("Target starts at position {0}".format(start_pos))
                    break

            if start_pos == -1:
                print("No target found")
                continue

            for i in range(start_pos, 180, 1):
                servo.write_pin(i, pause)
                if locations.get_loc(name) == -1:
                    break
                end_pos = i

            print("Target ends at position {0}".format(end_pos))

            total_pixels = locations.get_size(name)
            total_pos = end_pos - start_pos
            if total_pos > 0:
                pix_per_deg = round(total_pixels / float(total_pos), 2)
                servo.write_pin(90)
                print("{0} degrees to cover {1} pixels [{2} pixels/degree]"
                      .format(total_pos, total_pixels, pix_per_deg))
            else:
                print("No target found")

        elif len(key) == 0:
            pass
        elif key == "-" or key == "_":
            servo.write_pin(servo.read_pin() - 1)
        elif key == "+" or key == "=":
            servo.write_pin(servo.read_pin() + 1)
        elif key.isdigit():
            servo.write_pin(int(key))
        elif key == "q":
            break
        else:
            print("Invalid input: {0}".format(key))

import argparse
import datetime
import logging
import sys
import time
from threading import Thread

import plotly.graph_objs as go
import plotly.plotly as py
import plotly.tools as tls

from defaults import FORMAT_DEFAULT
from grpc_support import TimeoutException
from position_client import PositionClient

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--grpc", required=True, help="gRPC location server hostname")
    args = vars(parser.parse_args())

    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format=FORMAT_DEFAULT)

    # Start position client
    positions = PositionClient(args["grpc"])
    Thread(target=positions.read_positions).start()

    stream_ids = tls.get_credentials_file()['stream_ids']
    stream_id = stream_ids[1]

    trace1 = go.Scatter(x=[],
                        y=[],
                        mode='lines+markers',
                        stream=dict(token=stream_id, maxpoints=80))
    data = go.Data([trace1])
    layout = go.Layout(title='Line Offsets',
                       yaxis=go.YAxis(range=[-400, 400]))
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='plot-positions')

    # Now write data
    s = py.Stream(stream_id)
    s.open()

    logging.info("Opening plot.ly tab")
    time.sleep(5)

    prev_pos = None

    try:
        while True:
            try:
                pos = positions.get_position(timeout=0.5)

                if not pos["in_focus"]:
                    prev_pos = None
                    continue

                y = pos["mid_offset"]
                prev_pos = y

            # No change in value
            except TimeoutException:
                y = prev_pos

            x = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

            s.write(dict(x=x, y=y))
            time.sleep(.10)

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        s.close()
        positions.stop()

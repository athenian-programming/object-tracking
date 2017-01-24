import argparse
import datetime
import logging
import time
from logging import info

import plotly.graph_objs as go
import plotly.plotly as py
import plotly.tools as tls

from common_constants import LOGGING_ARGS
from grpc_support import TimeoutException
from position_client import PositionClient

if __name__ == "__main__":
    # Parse CLI args
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--grpc", required=True, help="gRPC location server hostname")
    args = vars(parser.parse_args())

    # Setup logging
    logging.basicConfig(**LOGGING_ARGS)

    # Start position client
    positions = PositionClient(args["grpc"])
    positions.start()

    stream_ids = tls.get_credentials_file()['stream_ids']
    stream_id = stream_ids[1]

    # Declare graph
    graph = go.Scatter(x=[], y=[], mode='lines+markers', stream=dict(token=stream_id, maxpoints=80))
    data = go.Data([graph])
    layout = go.Layout(title='Line Offsets', yaxis=go.YAxis(range=[-400, 400]))
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='plot-positions')

    # Write data
    stream = py.Stream(stream_id)
    stream.open()

    info("Opening plot.ly tab")
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

            stream.write(dict(x=x, y=y))
            time.sleep(.10)

    except KeyboardInterrupt:
        pass
    finally:
        stream.close()
        positions.stop()

    print("Exiting...")

import argparse
import datetime
import logging
import sys
import time
from threading import Thread

import plotly.graph_objs as go
import plotly.plotly as py
import plotly.tools as tls

from position_client import PositionClient

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--grpc", required=True, help="gRPC location server hostname")
    args = vars(parser.parse_args())

    logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                        format="%(asctime)s %(name)-10s %(funcName)-10s():%(lineno)i: %(levelname)-6s %(message)s")

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

    logging.info("Opening plot.ly tab...")
    time.sleep(5)

    try:
        while True:
            pos = positions.get_position()

            if not pos["in_focus"]:
                continue

            x = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            y = pos["mid_offset"]

            s.write(dict(x=x, y=y))
            time.sleep(.10)


    except KeyboardInterrupt:
        s.close()
        positions.stop()
        print("Exiting...")

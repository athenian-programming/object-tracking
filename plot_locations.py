import argparse
import logging
import sys
import time
from threading import Thread

import plotly.graph_objs as go
import plotly.plotly as py
import plotly.tools as tls

from location_client import LocationClient

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--grpc", required=True, help="gRPC location server hostname")
    args = vars(parser.parse_args())

    logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                        format="%(asctime)s %(name)-10s %(funcName)-10s():%(lineno)i: %(levelname)-6s %(message)s")

    # Start location client
    locations = LocationClient(args["grpc"])
    Thread(target=locations.read_locations).start()

    stream_ids = tls.get_credentials_file()['stream_ids']
    stream_id = stream_ids[0]

    trace1 = go.Scatter(x=[],
                        y=[],
                        mode='lines+markers',
                        stream=dict(token=stream_id, maxpoints=80))
    data = go.Data([trace1])
    layout = go.Layout(title='Target Locations',
                       xaxis=go.XAxis(range=[0, 800]),
                       yaxis=go.YAxis(range=[0, 450]))
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='plot-locations')

    # Now write data
    s = py.Stream(stream_id)
    s.open()

    logging.info("Opening plot.ly tab...")
    time.sleep(5)

    try:
        while True:
            x_val, y_val = locations.get_xy()

            if x_val[0] == -1 or y_val[0] == -1:
                continue

            x = abs(x_val[1] - x_val[0])
            y = abs(y_val[1] - y_val[0])

            s.write(dict(x=x, y=y))
            time.sleep(.10)

    except KeyboardInterrupt:
        s.close()
        locations.stop()
        print("Exiting...")

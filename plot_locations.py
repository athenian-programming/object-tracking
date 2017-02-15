import logging
import time

import cli_args  as cli
import plotly.graph_objs as go
import plotly.plotly as py
import plotly.tools as tls
from cli_args import LOG_LEVEL, GRPC_HOST
from cli_args import setup_cli_args
from location_client import LocationClient
from utils import setup_logging

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Parse CLI args
    args = setup_cli_args(cli.grpc_host, cli.verbose)

    # Setup logging
    setup_logging(level=args[LOG_LEVEL])

    # Start location client
    locations = LocationClient(args[GRPC_HOST]).start()

    stream_ids = tls.get_credentials_file()['stream_ids']
    stream_id = stream_ids[0]

    # Declare graph
    graph = go.Scatter(x=[], y=[], mode='lines+markers', stream=dict(token=stream_id, maxpoints=80))
    data = go.Data([graph])
    layout = go.Layout(title='Target Locations', xaxis=go.XAxis(range=[0, 800]), yaxis=go.YAxis(range=[0, 450]))
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='plot-locations')

    # Write data
    stream = py.Stream(stream_id)
    stream.open()

    logger.info("Opening plot.ly tab")
    time.sleep(5)

    try:
        while True:
            x_val, y_val = locations.get_xy()

            if x_val[0] == -1 or y_val[0] == -1:
                continue

            x = x_val[1] - abs(x_val[1] - x_val[0])
            y = abs(y_val[1] - y_val[0])

            stream.write(dict(x=x, y=y))
            time.sleep(.10)

    except KeyboardInterrupt:
        pass
    finally:
        stream.close()
        locations.stop()

    logger.info("Exiting...")

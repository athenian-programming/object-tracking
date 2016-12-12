import grpc

import color_tracker_pb2 as color__tracker__pb2


class ObjectTrackerStub(object):
    def __init__(self, channel):
        """Constructor.

        Args:
          channel: A grpc.Channel.
        """
        self.ReportLocation = channel.unary_stream(
            '/object_tracking.ObjectTracker/ReportLocation',
            request_serializer=color__tracker__pb2.ClientInfo.SerializeToString,
            response_deserializer=color__tracker__pb2.Location.FromString,
        )


class ObjectTrackerServicer(object):
    def ReportLocation(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ObjectTrackerServicer_to_server(servicer, server):
    rpc_method_handlers = {
        'ReportLocation': grpc.unary_stream_rpc_method_handler(
            servicer.ReportLocation,
            request_deserializer=color__tracker__pb2.ClientInfo.FromString,
            response_serializer=color__tracker__pb2.Location.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        'object_tracking.ObjectTracker', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))

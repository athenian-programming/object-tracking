import grpc

import location_server_pb2 as location__server__pb2


class LocationServerStub(object):
    def __init__(self, channel):
        """Constructor.

        Args:
          channel: A grpc.Channel.
        """
        self.RegisterClient = channel.unary_unary(
            '/object_tracking.LocationServer/RegisterClient',
            request_serializer=location__server__pb2.ClientInfo.SerializeToString,
            response_deserializer=location__server__pb2.ServerInfo.FromString,
        )
        self.ReportLocation = channel.stream_unary(
            '/object_tracking.LocationServer/ReportLocation',
            request_serializer=location__server__pb2.Location.SerializeToString,
            response_deserializer=location__server__pb2.Empty.FromString,
        )


class LocationServerServicer(object):
    def RegisterClient(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ReportLocation(self, request_iterator, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_LocationServerServicer_to_server(servicer, server):
    rpc_method_handlers = {
        'RegisterClient': grpc.unary_unary_rpc_method_handler(
            servicer.RegisterClient,
            request_deserializer=location__server__pb2.ClientInfo.FromString,
            response_serializer=location__server__pb2.ServerInfo.SerializeToString,
        ),
        'ReportLocation': grpc.stream_unary_rpc_method_handler(
            servicer.ReportLocation,
            request_deserializer=location__server__pb2.Location.FromString,
            response_serializer=location__server__pb2.Empty.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        'object_tracking.LocationServer', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))

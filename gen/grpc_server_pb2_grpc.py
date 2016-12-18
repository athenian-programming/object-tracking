import grpc

import grpc_server_pb2 as grpc__server__pb2


class ObjectLocationServerStub(object):
    def __init__(self, channel):
        """Constructor.

        Args:
          channel: A grpc.Channel.
        """
        self.RegisterClient = channel.unary_unary(
            '/opencv_object_tracking.ObjectLocationServer/RegisterClient',
            request_serializer=grpc__server__pb2.ClientInfo.SerializeToString,
            response_deserializer=grpc__server__pb2.ServerInfo.FromString,
        )
        self.GetObjectLocations = channel.unary_stream(
            '/opencv_object_tracking.ObjectLocationServer/GetObjectLocations',
            request_serializer=grpc__server__pb2.ClientInfo.SerializeToString,
            response_deserializer=grpc__server__pb2.ObjectLocation.FromString,
        )


class ObjectLocationServerServicer(object):
    def RegisterClient(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetObjectLocations(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ObjectLocationServerServicer_to_server(servicer, server):
    rpc_method_handlers = {
        'RegisterClient': grpc.unary_unary_rpc_method_handler(
            servicer.RegisterClient,
            request_deserializer=grpc__server__pb2.ClientInfo.FromString,
            response_serializer=grpc__server__pb2.ServerInfo.SerializeToString,
        ),
        'GetObjectLocations': grpc.unary_stream_rpc_method_handler(
            servicer.GetObjectLocations,
            request_deserializer=grpc__server__pb2.ClientInfo.FromString,
            response_serializer=grpc__server__pb2.ObjectLocation.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        'opencv_object_tracking.ObjectLocationServer', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


class FocusLinePositionServerStub(object):
    def __init__(self, channel):
        """Constructor.

        Args:
          channel: A grpc.Channel.
        """
        self.RegisterClient = channel.unary_unary(
            '/opencv_object_tracking.FocusLinePositionServer/RegisterClient',
            request_serializer=grpc__server__pb2.ClientInfo.SerializeToString,
            response_deserializer=grpc__server__pb2.ServerInfo.FromString,
        )
        self.GetFocusLinePositions = channel.unary_stream(
            '/opencv_object_tracking.FocusLinePositionServer/GetFocusLinePositions',
            request_serializer=grpc__server__pb2.ClientInfo.SerializeToString,
            response_deserializer=grpc__server__pb2.FocusLinePosition.FromString,
        )


class FocusLinePositionServerServicer(object):
    def RegisterClient(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetFocusLinePositions(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_FocusLinePositionServerServicer_to_server(servicer, server):
    rpc_method_handlers = {
        'RegisterClient': grpc.unary_unary_rpc_method_handler(
            servicer.RegisterClient,
            request_deserializer=grpc__server__pb2.ClientInfo.FromString,
            response_serializer=grpc__server__pb2.ServerInfo.SerializeToString,
        ),
        'GetFocusLinePositions': grpc.unary_stream_rpc_method_handler(
            servicer.GetFocusLinePositions,
            request_deserializer=grpc__server__pb2.ClientInfo.FromString,
            response_serializer=grpc__server__pb2.FocusLinePosition.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        'opencv_object_tracking.FocusLinePositionServer', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))

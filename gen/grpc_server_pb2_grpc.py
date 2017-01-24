import grpc

import grpc_server_pb2 as grpc__server__pb2


class ObjectLocationServerStub(object):
    def __init__(self, channel):
        """Constructor.

        Args:
          channel: A grpc.Channel.
        """
        self.registerClient = channel.unary_unary(
            '/opencv_object_tracking.ObjectLocationServer/registerClient',
            request_serializer=grpc__server__pb2.ClientInfo.SerializeToString,
            response_deserializer=grpc__server__pb2.ServerInfo.FromString,
        )
        self.getObjectLocations = channel.unary_stream(
            '/opencv_object_tracking.ObjectLocationServer/getObjectLocations',
            request_serializer=grpc__server__pb2.ClientInfo.SerializeToString,
            response_deserializer=grpc__server__pb2.ObjectLocation.FromString,
        )


class ObjectLocationServerServicer(object):
    def registerClient(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def getObjectLocations(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ObjectLocationServerServicer_to_server(servicer, server):
    rpc_method_handlers = {
        'registerClient': grpc.unary_unary_rpc_method_handler(
            servicer.registerClient,
            request_deserializer=grpc__server__pb2.ClientInfo.FromString,
            response_serializer=grpc__server__pb2.ServerInfo.SerializeToString,
        ),
        'getObjectLocations': grpc.unary_stream_rpc_method_handler(
            servicer.getObjectLocations,
            request_deserializer=grpc__server__pb2.ClientInfo.FromString,
            response_serializer=grpc__server__pb2.ObjectLocation.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        'opencv_object_tracking.ObjectLocationServer', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))

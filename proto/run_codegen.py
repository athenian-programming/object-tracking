#!/usr/bin/env python2

from grpc.tools import protoc

protoc.main(
    (
        '',
        '-I.',
        '--python_out=../gen',
        '--grpc_python_out=../gen',
        './grpc_server.proto',
    )
)

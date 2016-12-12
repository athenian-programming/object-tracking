from grpc.tools import protoc

protoc.main(
    (
        '',
        '-I.',
        '--python_out=./gen',
        '--grpc_python_out=./gen',
        './color_tracker.proto',
    )
)

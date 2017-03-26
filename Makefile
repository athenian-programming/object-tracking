
py-stubs:
	python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. ./pb/location_server.proto

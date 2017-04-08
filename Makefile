
py-stubs:
	python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. ./proto/location_service.proto

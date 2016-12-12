import logging
import thread
import threading
import time

import grpc
from concurrent import futures

import gen.color_tracker_pb2


class LocationServer(gen.color_tracker_pb2.ObjectTrackerServicer):
    def __init__(self, hostname):
        self._hostname = hostname
        self._lock = threading.Lock()
        self._data_ready = threading.Event()
        self._currloc = None

    def ReportLocation(self, request, context):
        logging.info("Client connected: {0}".format(request.info))
        try:
            while True:
                yield self.read_location()
        finally:
            logging.info("Client disconnected: {0}".format(request.info))

    def hostname(self):
        return self._hostname

    def read_location(self):
        self._data_ready.wait()
        self._lock.acquire()
        try:
            return self._currloc
        finally:
            self._data_ready.clear()
            self._lock.release()

    def write_location(self, val):
        self._lock.acquire()
        try:
            self._currloc = val
            self._data_ready.set()
        finally:
            self._lock.release()

    @staticmethod
    def start(server):
        grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        gen.color_tracker_pb2.add_ObjectTrackerServicer_to_server(server, grpc_server)
        grpc_server.add_insecure_port(server.hostname())
        grpc_server.start()
        try:
            while True:
                time.sleep(60 * 60)
        except KeyboardInterrupt:
            grpc_server.stop(0)


if __name__ == '__main__':
    location_server = LocationServer('[::]:50051')
    try:
        thread.start_new_thread(LocationServer.start, (location_server,))
    except BaseException as e:
        logging.error("Unable to start grpc server [{0}]".format(e))

    time.sleep(2)
    for i in range(1, 100):
        print("Writing data for {0}".format(i))
        location_server.write_location(gen.color_tracker_pb2.Location(x=i, y=i + 1, width=i + 2, height=i + 3))
        time.sleep(2)

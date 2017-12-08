#!/usr/bin/python

import signal
from daemon_tree import DaemonTreeSvr
from wifireconnect import ReconnectWorker, WORKER_NAME
from dev_utils import configure_logging


def main():
    configure_logging()

    def handler(signum, frame):
        reconnect_worker.stop_reconnection()
        reconnect_svr.cancel()

    reconnect_worker = ReconnectWorker()
    reconnect_svr = DaemonTreeSvr(name=WORKER_NAME)

    reconnect_svr.register(reconnect_worker.start_reconnection)
    reconnect_svr.register(reconnect_worker.stop_reconnection)

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    reconnect_svr.run()
    reconnect_svr.shutdown()


if __name__ == '__main__':
    main()

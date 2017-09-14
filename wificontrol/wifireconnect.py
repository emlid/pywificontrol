# wificontrol code is placed under the GPL license.
# Written by Denis Chagin (denis.chagin@emlid.com)
# Copyright (c) 2016, Emlid Limited
# All rights reserved.

# If you are interested in using wificontrol code as a part of a
# closed source project, please contact Emlid Limited (info@emlid.com).

# This file is part of wificontrol.

# wificontrol is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# wificontrol is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with wificontrol.  If not, see <http://www.gnu.org/licenses/>.


import dbus
import signal
import threading
import logging
from daemon_tree import DaemonTreeSvr
from wificontrol import WiFiControl

logging.basicConfig()
logger = logging.getLogger(__name__)

WORKER_NAME = 'wifi_reconnect'


class ReconnectWorker(object):
    TIMEOUT = 10

    def __init__(self):
        self.manager = WiFiControl()
        self.interrupt = threading.Event()
        self.worker = None

    def start_reconnection(self, ssid):
        if self.worker is None:
            self.worker = threading.Thread(target=self._reconnect, args=(ssid,))
            self.worker.daemon = True
            self.worker.start()

    def _reconnect(self, ssid):
        self.interrupt.clear()
        self.interrupt.wait(self.TIMEOUT)

        while not self.interrupt.is_set():
            try:
                self.manager.scan()
                scan_results = self.manager.get_scan_results()

                scanned_ssids = [net['ssid'] for net in scan_results]

                if ssid in scanned_ssids:
                    network = {'ssid': ssid}
                    self.manager.start_connecting(network, callback=self._callback)
            except dbus.exceptions.DBusException as error:
                logger.error(error)

            self.interrupt.wait(self.TIMEOUT)

    def _callback(self, result=None):
        if result:
            self.interrupt.set()

    def stop_reconnection(self):
        self.interrupt.set()
        if self.worker:
            self.worker.join()
            self.worker = None


def main():
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

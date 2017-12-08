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
import threading
import logging
from wificontrol import WiFiControl


logger = logging.getLogger(__name__)

WORKER_NAME = 'wifi_reconnect'


class ReconnectWorker(object):
    TIMEOUT = 10

    def __init__(self):
        self.manager = WiFiControl()
        self.interrupt = threading.Event()
        self.worker = None

    def start_reconnection(self, ssid):
        logger.debug('start_reconnection, worker {}'.format(self.worker))
        if self.worker is None:
            self.worker = threading.Thread(target=self._reconnect, args=(ssid,))
            self.worker.daemon = True
            self.worker.start()

    def _reconnect(self, ssid):
        self.interrupt.clear()
        self.interrupt.wait(self.TIMEOUT)
        logger.debug('Test reconnect, ssid: {}'.format(ssid))
        while not self.interrupt.is_set():
            try:
                logger.debug('main loop, check ssid: {}'.format(ssid))
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
        logger.debug('start_connecting callback: {}'.format(result))
        if result:
            self.interrupt.set()

    def stop_reconnection(self):
        self.interrupt.set()
        if self.worker:
            logger.debug('stop_reconnection')
            self.worker.join()
            self.worker = None

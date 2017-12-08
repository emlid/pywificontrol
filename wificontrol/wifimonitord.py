#!/usr/bin/python


# Written by Ivan Sapozhkov and Denis Chagin <denis.chagin@emlid.com>
#
# Copyright (c) 2016, Emlid Limited
# All rights reserved.
#
# Redistribution and use in source and binary forms,
# with or without modification,
# are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software
# without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import signal
from reachstatus import StateClient
from wifimonitor import WiFiMonitor
from dev_utils import configure_logging


def main():
    configure_logging()

    def handler(signum, frame):
        wifi_monitor.shutdown()

    wifi_monitor = WiFiMonitor()

    wifi_monitor.register_callback(wifi_monitor.HOST_STATE, StateClient.set_network_host_state)
    wifi_monitor.register_callback(wifi_monitor.CLIENT_STATE, StateClient.set_network_client_state)
    wifi_monitor.register_callback(wifi_monitor.OFF_STATE, StateClient.set_network_disabled_state)
    wifi_monitor.register_callback(wifi_monitor.SCAN_STATE, StateClient.set_network_scan_state)
    wifi_monitor.register_callback(wifi_monitor.REVERT_EVENT,
                                   StateClient.send_revert_connect_notify)
    wifi_monitor.register_callback(wifi_monitor.SUCCESS_EVENT,
                                   StateClient.send_success_connect_notify)

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    wifi_monitor.run()


if __name__ == '__main__':
    main()

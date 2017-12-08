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


import pytest
import mock
import threading

# the new reconnect feature requires daemon tree
# skip if the dependency is not installed
daemon_tree = pytest.importorskip("daemon_tree")
from wificontrol.wifireconnect import ReconnectWorker


@pytest.fixture
def valid_network():
    network = {
        'ssid': 'TEST_SSID'
    }
    return network


class FakeReconnectWorker(ReconnectWorker):
    def __init__(self):
        self.manager = mock.MagicMock()
        self.interrupt = threading.Event()
        self.worker = None


class TestReconnectWorker:
    def setup_method(self):
        self.reconnect_worker = FakeReconnectWorker()
        self.reconnect_worker.TIMEOUT = 0.1

    def teardown_method(self):
        self.reconnect_worker.stop_reconnection()
        assert self.reconnect_worker.worker is None

    def test_reconnection_start_and_stop(self, valid_network):
        self.reconnect_worker.start_reconnection(valid_network['ssid'])

        self.reconnect_worker.interrupt.wait(0.5)

        self.reconnect_worker.manager.scan.assert_called()
        self.reconnect_worker.manager.get_scan_results.assert_called()

        self.reconnect_worker.stop_reconnection()

        assert self.reconnect_worker.interrupt.is_set()
        assert self.reconnect_worker.worker is None

    def test_reconnection_worker_success_connection(self, valid_network):
        def start_connecting(network, callback, *args, **kwargs):
            assert network == valid_network
            callback(True)

        self.reconnect_worker.manager.start_connecting.side_effect = start_connecting

        self.reconnect_worker.start_reconnection(valid_network['ssid'])
        self.reconnect_worker.interrupt.wait(0.5)

        self.reconnect_worker.manager.get_scan_results.return_value = [valid_network]

        self.reconnect_worker.interrupt.wait(2)
        assert self.reconnect_worker.interrupt.is_set()

        self.reconnect_worker.stop_reconnection()
        assert self.reconnect_worker.worker is None

    def test_second_worker_start(self, valid_network):
        self.reconnect_worker.start_reconnection(valid_network['ssid'])
        worker = self.reconnect_worker.worker
        self.reconnect_worker.start_reconnection(valid_network['ssid'])
        assert self.reconnect_worker.worker == worker

    def test_worker_restart(self, valid_network):
        self.reconnect_worker.start_reconnection(valid_network['ssid'])
        self.reconnect_worker.interrupt.wait(2)
        self.reconnect_worker.stop_reconnection()
        
        self.reconnect_worker.start_reconnection(valid_network['ssid'])
        self.reconnect_worker.interrupt.wait(2)
        self.reconnect_worker.manager.scan.assert_called()
        self.reconnect_worker.manager.get_scan_results.assert_called()

        assert self.reconnect_worker.worker



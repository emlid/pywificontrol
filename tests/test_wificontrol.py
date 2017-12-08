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

from wificontrol import WiFiControl


@pytest.fixture
def ssid():
    network = {
        'ssid': 'Test'
    }

    return network


class FakeWiFiControl(WiFiControl):
    def __init__(self):
        self.wifi = mock.MagicMock()
        self.wpasupplicant = mock.MagicMock()
        self.hotspot = mock.MagicMock()


class TestWiFiControl:
    def setup_method(self):
        self.manager = FakeWiFiControl()

    def test_host_mode(self):
        self.manager.hotspot.started = mock.Mock(return_value=False)

        self.manager.start_host_mode()

        assert self.manager.wpasupplicant.stop.call_count == 1
        assert self.manager.hotspot.started.call_count == 1
        assert self.manager.hotspot.start.call_count == 1

    def test_client_mode(self):
        self.manager.wpasupplicant.started = mock.Mock(return_value=False)

        self.manager.start_client_mode()

        assert self.manager.hotspot.stop.call_count == 1
        assert self.manager.wpasupplicant.started.call_count == 1
        assert self.manager.wpasupplicant.start.call_count == 1

    def test_wifi_turn_on(self):
        self.manager.wpasupplicant.started = mock.Mock(return_value=False)
        self.manager.hotspot.started = mock.Mock(return_value=False)

        self.manager.turn_on_wifi()

        assert self.manager.wifi.unblock.call_count == 1
        assert self.manager.wpasupplicant.started.call_count == 1
        assert self.manager.wpasupplicant.start.call_count == 1

        self.manager.wpasupplicant.started.return_value = True
        assert self.manager.get_wifi_turned_on() is True

    def test_wifi_turn_off(self):
        self.manager.wpasupplicant.started = mock.Mock(return_value=True)
        self.manager.hotspot.started = mock.Mock(return_value=False)

        self.manager.turn_off_wifi()

        assert self.manager.wifi.block.call_count == 1
        assert self.manager.hotspot.stop.call_count == 1
        assert self.manager.wpasupplicant.stop.call_count == 1

        self.manager.wpasupplicant.started.return_value = False
        assert self.manager.get_wifi_turned_on() is False

    def test_wifi_turn_on_if_wifi_is_on(self):
        self.manager.wpasupplicant.started = mock.Mock(return_value=False)
        self.manager.hotspot.started = mock.Mock(return_value=True)

        self.manager.turn_on_wifi()

        assert self.manager.wifi.unblock.call_count == 0
        assert self.manager.wpasupplicant.started.call_count == 1
        assert self.manager.hotspot.started.call_count == 1
        assert self.manager.wpasupplicant.start.call_count == 0
        assert self.manager.hotspot.start.call_count == 0

    def test_network_add(self, ssid):
        self.manager.add_network(ssid)
        assert self.manager.wpasupplicant.add_network.is_called_once_with(ssid)

    def test_network_remove(self, ssid):
        self.manager.remove_network(ssid)
        assert self.manager.wpasupplicant.remove_network.is_called_once_with(ssid)

    def test_status_get(self, ssid):
        self.manager.wpasupplicant.started = mock.Mock(return_value=False)
        self.manager.hotspot.started = mock.Mock(return_value=True)

        state, status = self.manager.get_status()

        assert state == self.manager.HOST_STATE
        assert status is None

        self.manager.wpasupplicant.started.return_value = True
        self.manager.hotspot.started.return_value = False

        self.manager.wpasupplicant.get_status = mock.Mock(return_value=ssid)

        state, status = self.manager.get_status()

        assert state == self.manager.WPA_STATE
        assert status == ssid

    def test_start_connection(self, ssid):
        def start_connecting(*args):
            self.manager.hotspot.started.return_value = False
            self.manager.revert_on_connect_failure(result=None)

        self.manager.wpasupplicant.started = mock.Mock(return_value=False)
        self.manager.wpasupplicant.start_connecting.side_effect = start_connecting

        self.manager.hotspot.started = mock.Mock(return_value=True)

        self.manager.start_connecting(ssid)

        assert self.manager.wpasupplicant.started.call_count == 1
        assert self.manager.hotspot.stop.call_count == 1
        assert self.manager.wpasupplicant.start.call_count == 1

        args = (ssid, self.manager.revert_on_connect_failure, None, 10)

        assert self.manager.wpasupplicant.start_connecting.is_called_once_with(args)

        assert self.manager.hotspot.started.call_count == 1
        assert self.manager.wpasupplicant.stop.call_count == 1
        assert self.manager.hotspot.start.call_count == 1

    def test_reconnection(self, ssid):
        def start_connecting(result, callback, args, timeout):
            self.manager.hotspot.started.return_value = False
            if args:
                callback({}, *args)
            else:
                callback(result)

        self.manager.wpasupplicant.started = mock.Mock(return_value=False)
        self.manager.wpasupplicant.start_connecting.side_effect = start_connecting

        self.manager.hotspot.started = mock.Mock(return_value=True)

        self.manager.start_connecting(ssid, callback=self.manager.reconnect,
                                      args=(ssid,))

        assert self.manager.wpasupplicant.start_connecting.call_count == 2

    def test_supplicant_functions(self):
        self.manager.scan()
        assert self.manager.wpasupplicant.scan.call_count == 1

        self.manager.get_scan_results()
        assert self.manager.wpasupplicant.get_scan_results.call_count == 1

        self.manager.get_added_networks()
        assert self.manager.wpasupplicant.get_added_networks.call_count == 1

        self.manager.get_ip()
        assert self.manager.wifi.get_device_ip.call_count == 1

        self.manager.stop_connecting()
        assert self.manager.wpasupplicant.stop_connecting.call_count == 1

        self.manager.disconnect()
        assert self.manager.wpasupplicant.disconnect.call_count == 1

        self.manager.get_device_name()
        assert self.manager.hotspot.get_host_name.call_count == 1

        self.manager.get_hostap_name()
        assert self.manager.hotspot.get_hostap_name.call_count == 1

        name = 'test'
        self.manager.set_device_names(name)
        assert self.manager.wpasupplicant.set_p2p_name.call_count == 1
        assert self.manager.wpasupplicant.set_p2p_name.is_called_once_with(name)

        assert self.manager.hotspot.set_hostap_name.call_count == 1
        assert self.manager.hotspot.set_hostap_name.is_called_once_with(name)

        assert self.manager.hotspot.set_host_name.call_count == 1
        assert self.manager.hotspot.set_host_name.is_called_once_with(name)

        assert self.manager.wifi.restart_dns.call_count == 1

        self.manager.set_hostap_password(name)
        assert self.manager.hotspot.set_hostap_password.is_called_once_with(name)

    def test_verify_names(self):
        name = 'test'
        mac_addr = '11:22:33:44:55:66'

        self.manager.hotspot.get_host_name.return_value = name
        self.manager.wpasupplicant.get_p2p_name.return_value = name
        self.manager.hotspot.get_hostap_name.return_value = "{}{}".format(name, mac_addr[-6:])
        self.manager.hotspot.get_device_mac.return_value = mac_addr[-6:]

        assert self.manager.verify_hostap_name(name)
        assert self.manager.verify_device_names(name)
        assert self.manager.hotspot.get_host_name.call_count == 1
        assert self.manager.wpasupplicant.get_p2p_name.call_count == 1

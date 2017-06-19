# wificontrol code is placed under the GPL license.
# Written by Ivan Sapozhkov (ivan.sapozhkov@emlid.com)
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

import os
import pytest
from threading import Event
from wificontrol import WiFiControl
from tests import edison


@pytest.fixture
def valid_network():
    network = {
        'ssid': "EML33T2",
        'password': "emrooftop",
        'security': "wpa2psk",
        'identity': ""
    }
    return network


@pytest.fixture
def invalid_network():
    network = {
        'ssid': "somenetwork",
        'password': "password",
        'security': "wpa2psk",
        'identity': "ivan@example.com"
    }
    return network


@edison
class TestWiFiControl:
    CALLBACK_TIMEOUT = 15

    @classmethod
    def setup_class(cls):
        cur_path = os.getcwd()
        cls.hostapd_path = cur_path + "/tests/test_files/hostapd.conf"
        cls.hostname_path = cur_path + "/tests/test_files/hostname"
        cls.wpas_config = cur_path + "/tests/test_files/wpa_supplicant.conf"
        cls.p2p_config = cur_path + "/tests/test_files/p2p_supplicant.conf"

    def setup_method(self):
        self.connection_result = 0
        self.callback_event = Event()
        self.manager = WiFiControl(wpas_config=self.wpas_config,
                                   p2p_config=self.p2p_config,
                                   hostapd_config=self.hostapd_path,
                                   hostname_config=self.hostname_path)

    def teardown_method(self):
        pass

    def hostapd_callback(self, result):
        if not result:
            self.manager.start_host_mode()
            self.connection_result = -1
        else:
            self.connection_result = 1

        self.callback_event.set()

    def wait_for_callback(self, result):
        self.callback_event.wait(self.CALLBACK_TIMEOUT)
        assert self.connection_result == result

    def test_start_hotspot(self):
        self.manager.start_host_mode()
        assert self.manager.get_state() == self.manager.HOST_STATE

    def test_start_client(self):
        self.manager.start_client_mode()
        assert self.manager.get_state() == self.manager.WPA_STATE

    def test_wifi_turn_off(self):
        self.manager.turn_off_wifi()
        assert self.manager.get_state() == self.manager.OFF_STATE
        assert self.manager.get_wifi_turned_on() is False

    def test_wifi_turn_on(self):
        self.manager.turn_off_wifi()
        self.manager.turn_on_wifi()

        assert self.manager.get_wifi_turned_on() is True

    def test_network_add(self, valid_network):
        self.manager.add_network(valid_network)
        added_networks = self.manager.get_added_networks()

        assert valid_network['ssid'] in [network['ssid'] for network in added_networks]

    def test_network_add_with_different_security(self, valid_network):
        securities = ['wpapsk', 'wpa2psk', 'wep', 'open', 'wpaeap']
        for security in securities:
            valid_network['security'] = security
            self.manager.add_network(valid_network)

    def test_network_remove(self, valid_network):
        self.test_network_add(valid_network)
        self.manager.remove_network(valid_network)

        added_networks = self.manager.get_added_networks()
        assert valid_network['ssid'] not in [network['ssid'] for network in added_networks]

    def test_hotspot_after_connect_failure(self, invalid_network):
        self.manager.add_network(invalid_network)
        self.manager.start_connecting(invalid_network, timeout=1, callback=self.hostapd_callback)

        self.wait_for_callback(-1)

        self.manager.remove_network(invalid_network)

    def test_connect_to_reachable_network_from_hostap(self, valid_network):
        self.manager.start_host_mode()

        self.manager.add_network(valid_network)
        self.manager.start_connecting(valid_network, callback=self.hostapd_callback)

        self.wait_for_callback(1)

        state, status = self.manager.get_status()

        assert state == self.manager.WPA_STATE
        assert status['ssid'] == valid_network['ssid']

    def test_change_names(self):
        old_name = self.manager.get_device_name()
        new_name = "TestCaseName"
        mac_end = self.manager.wifi.get_device_mac()[-6:]

        self.manager.set_device_names(new_name)
        assert self.manager.get_device_name() == new_name
        assert self.manager.get_hostap_name() == new_name + mac_end

        self.manager.set_device_names(old_name)
        assert self.manager.get_device_name() == old_name
        assert self.manager.get_hostap_name() == old_name + mac_end

    def test_connect_to_any_network(self):
        self.manager.start_client_mode()
        self.manager.start_connecting(None, callback=self.hostapd_callback)

        self.wait_for_callback(1)

        state, status = self.manager.get_status()

        assert state == self.manager.WPA_STATE
        assert status['ssid']

    def test_scan_function(self):
        self.manager.start_client_mode()
        self.manager.scan()
        scan_results = self.manager.get_scan_results()
        assert isinstance(scan_results, list)

    def test_disconnect_from_network(self, valid_network):
        self.test_connect_to_reachable_network_from_hostap(valid_network)
        self.manager.disconnect()

        state, status = self.manager.get_status()

        assert state == self.manager.WPA_STATE
        assert status is None

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
import unittest
import platform
import subprocess
from .fakewifi import fakeWiFiControl as WiFiControl

class WiFiControlTest(unittest.TestCase):

    not_edison = ("edison" not in platform.platform(), "Not suppoted in this platform")

    def hostapd_callback(self, result):
        if not result:
            print("Cant connect to network")
            print("Starting hostapd")
            self.manager.start_host_mode()
            self.connection_result = -1
        else:
            self.connection_result = 1

    def setUp(self):
        self.connection_result = 0
        self.manager = WiFiControl()

    def tearDown(self):
        pass

    @unittest.skipIf(*not_edison)
    def test_start_hotspot(self):
        self.manager.start_host_mode()

    @unittest.skipIf(*not_edison)
    def test_start_client(self):
        self.manager.start_client_mode()

    @unittest.skipIf(*not_edison)
    def test_hotspot_after_connect_failure(self):
        test_network = {
            'ssid': "somenetwork",
            'password': "password",
            'security': "wpa2psk",
            'identity': "ivan@example.com"
        }
        self.manager.add_network(test_network)
        self.manager.start_connecting(test_network, timeout=1, callback=self.hostapd_callback)
        while(self.connection_result == 0):
            pass
        self.assertEqual(self.connection_result, -1)
        self.manager.remove_network(test_network)

    @unittest.skipIf(*not_edison)
    def test_connect_to_reachable_network_from_hostap(self):
        self.manager.start_host_mode()
        test_network = {
            'ssid': "EML33T5",
            'password': "emrooftop",
            'security': "wpa2psk",
            'identity': ""
        }
        self.manager.add_network(test_network)
        self.manager.start_connecting(test_network, callback=self.hostapd_callback)
        while(self.connection_result == 0):
            pass
        self.assertEqual(self.connection_result, 1)

    @unittest.skipIf(*not_edison)
    def test_change_names(self):
        old_name = self.manager.get_device_name()
        new_name = "TestCaseName"
        mac_end = self.manager.wifi.get_device_mac()[-6:]

        self.manager.set_device_names(new_name)
        self.assertEqual(self.manager.get_device_name(), new_name)
        self.assertEqual(self.manager.get_hostap_name(), new_name+mac_end)

        self.manager.set_device_names(old_name)
        self.assertEqual(self.manager.get_device_name(), old_name)
        self.assertEqual(self.manager.get_hostap_name(), old_name+mac_end)

    @unittest.skipIf(*not_edison)
    def test_connect_to_any_network(self):
        self.manager.start_client_mode()
        self.manager.start_connecting(None, callback=self.hostapd_callback)
        while(self.connection_result == 0):
            pass
        self.assertEqual(self.connection_result, 1)


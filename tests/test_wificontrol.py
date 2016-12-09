import os
import unittest
import platform
import subprocess
from fakewifi import fakeWiFiControl as WiFiControl

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


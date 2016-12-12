import os
import unittest
import platform
import subprocess
from random import randint
from fakewifi import fakeWpaSupplicant as WpaSupplicant 

class ValidationError(Exception):
    pass

def execute_command(command):
   return subprocess.check_output(command, stderr=subprocess.PIPE, shell=True)

def check_number_of_networks(file, file_network_count, service_network_count):
    file_counter = int(execute_command("grep -c \"network={{\" {}".format(file)).strip())
    service_counter = int(execute_command("wpa_cli list_networks | grep -c \'^[0-9]\'".strip()))
    print("Number networks in REAL file: {}".format(file_counter))
    print("Number networks in REAL service: {}".format(service_counter))
    if (file_network_count != file_counter or
        service_network_count != service_counter):
        raise ValidationError()

class WpaSupplicantTest(unittest.TestCase):

    not_edison = ("edison" not in platform.platform(), "Not suppoted in this platform")

    def assert_networks_number(self):
        file_network_count = len(self.wifi.get_added_networks())
        service_network_count = len(self.wifi.wpa_supplicant_interface.getNetworks())
        print("Number networks in Config file: {}".format(file_network_count))
        print("Number networks in wpa_supplicant service: {}".format(service_network_count))
        # with self.assertRaises(ValidationError):
        check_number_of_networks(self.wifi.wpa_supplicant_path, 
            file_network_count, service_network_count)

    def print_callback(self, result):
        if not result:
            print("Cant connect to network!")
            self.connection_result = -1
        else:
            print("Connected to network")
            self.connection_result = 1

    def setUp(self):
        self.connection_result = 0
        if "Ubuntu" in platform.platform():
            cur_path = os.getcwd()
            wpas_config = cur_path + "/tests/test_files/wpa_supplicant.conf"
            p2p_config = cur_path + "/tests/test_files/p2p_supplicant.conf"
            self.wifi = WpaSupplicant('wlp6s0', wpas_config, p2p_config)
        else:
            self.wifi = WpaSupplicant('wlan0')

    def tearDown(self):
        pass

    def test_add_networks(self):
        test_network = {'ssid': "ssid", 'password': "password", 'security': "wpa2psk", 'identity': "ivan@example.com"}
        for index in range(0, 10):
            print(index)
            test_network['ssid'] = "ssid{}".format(index)
            print("network to add: {}".format(test_network))
            self.wifi.add_network(test_network)
        self.assert_networks_number()

    def test_remove_networks(self):
        test_network = {'ssid': "ssid", 'password': "password", 'security': "wpa2psk", 'identity': "ivan@example.com"}
        for index in range(0, 10):
            print(index)
            test_network['ssid'] = "ssid{}".format(index)
            print("network to remove: {}".format(test_network))
            self.wifi.remove_network(test_network)
        self.assert_networks_number()

    def test_connect_to_unreachable_network(self):
        test_network = {
            'ssid': "somenetwork",
            'password': "password",
            'security': "wpa2psk",
        }
        self.wifi.add_network(test_network)
        self.wifi.start_connecting(test_network, timeout=1, callback=self.print_callback)
        while(self.connection_result == 0):
            pass
        self.assertEqual(self.connection_result, -1)
        self.wifi.remove_network(test_network)

    @unittest.skipIf(*not_edison)
    def test_connect_to_reachable_network(self):
        test_network = {
            'ssid': "EML33T5",
            'password': "emrooftop",
            'security': "wpa2psk",
            'identity': ""
        }
        self.wifi.add_network(test_network)
        self.wifi.start_connecting(test_network, callback=self.print_callback)
        while(self.connection_result == 0):
            pass
        self.assertEqual(self.connection_result, 1)

    def test_p2p_name_changing(self):
        new_name = "testname_{}".format(randint(0,1000))
        self.wifi.set_p2p_name(new_name)
        self.assertEqual(self.wifi.get_p2p_name(), new_name)

    def test_start_wpas(self):
        self.wifi.start()
        self.assertTrue(self.wifi.started())

    def test_stop_wpas(self):
        self.wifi.stop()
        self.assertFalse(self.wifi.started())

if __name__ == '__main__':
    unittest.main()
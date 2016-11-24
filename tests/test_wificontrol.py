import os
import unittest
import platform
import subprocess
import wificontrol

def execute_command(command):
    try:
       return subprocess.check_output(command, stderr=subprocess.PIPE, shell=True)

    except subprocess.CalledProcessError as error:
        pass

def check_number_of_networks(file, file_network_count, service_network_count):
    file_counter = int(execute_command("grep -c \"network={{\" {}".format(file)).strip())
    service_counter = int(execute_command("wpa_cli list_networks | grep -c \'^[0-9]\'".strip()))
    print("Number networks in REAL file: {}".format(file_counter))
    print("Number networks in REAL service: {}".format(service_counter))
    if (file_network_count != file_counter or
        service_network_count != service_counter):
        return False
    return True


class WiFiControlTest(unittest.TestCase):

    def assert_networks_number(self):
        file_network_count = len(self.wifi.get_added_networks())
        service_network_count = len(self.wifi._wpa_supplicant_interface.getNetworks())
        print("Number networks in WiFiControl file: {}".format(file_network_count))
        print("Number networks in WiFiControl service: {}".format(service_network_count))
        self.assertTrue(check_number_of_networks(self.wifi.wpa_supplicant_path, 
            file_network_count, service_network_count))

    def print_callback(self, result):
        if not result:
            print("Cant connect to network!")
            self.connection_result = -1
        else:
            print("Connected to network")
            self.connection_result = 1

    def hostapd_callback(self, result):
        if not result:
            print("Cant connect to network")
            print("Starting hostapd")
            self.connection_result = -1
            self.wifi.start_host_mode()

    def setUp(self):
        self.connection_result = 0
        if "Ubuntu" in platform.platform():
            self.wifi = wificontrol.WiFiControl('wlp6s0')
            cur_path = os.getcwd()
            self.wifi.hostapd_path = cur_path + "/tests/test_files/hostapd.conf"
            self.wifi.wpa_supplicant_path = cur_path + "/tests/test_files/wpa_supplicant.conf"
            self.wifi.p2p_supplicant_path = cur_path + "/tests/test_files/wpa_p2p_supplicant.conf"
            self.wifi.hostname_path = cur_path + "/tests/test_files/hostname"
            self.wifi._config_updater = wificontrol.utils.ConfigurationFileUpdater(self.wifi.wpa_supplicant_path)
        else:
            self.wifi = wificontrol.WiFiControl()

    def tearDown(self):
        pass

    @unittest.skipIf("edison" not in platform.platform(), 
        "Not suppoted in this platform")
    def test_01_start_hotspot(self):
        self.wifi.start_host_mode()
        self.assertFalse(self.wifi._wpa_supplicant_start())
        self.assertTrue(self.wifi._hostapd_start())

    @unittest.skipIf("edison" not in platform.platform(), 
        "Not suppoted in this platform")
    def test_02_start_client(self):
        self.wifi.start_client_mode()
        self.assertFalse(self.wifi._hostapd_start())
        self.assertTrue(self.wifi._wpa_supplicant_start())

    def test_03_add_networks(self):
        self.assert_networks_number()
        
        test_network = {'ssid': "ssid", 'password': "password", 'security': "wpa2psk", 'identity': "ivan@example.com"}
        for index in range(0, 100):
            print(index)
            test_network['ssid'] = "ssid{}".format(index)
            print("network to add: {}".format(test_network))
            self.wifi.add_network(test_network)
        
        self.assert_networks_number()

    def test_04_remove_networks(self):
        self.assert_networks_number()
        
        test_network = {'ssid': "ssid", 'password': "password", 'security': "wpa2psk", 'identity': "ivan@example.com"}
        for index in range(0, 100):
            print(index)
            test_network['ssid'] = "ssid{}".format(index)
            print("network to remove: {}".format(test_network))
            self.wifi.remove_network(test_network)
        self.assert_networks_number()

    def test_05_connect_to_unreachable_network(self):
        test_network = {
            'ssid': "somenetwork",
            'password': "password",
            'security': "wpa2psk",
            'identity': "ivan@example.com"
        }
        self.wifi.add_network(test_network)
        self.wifi.start_connecting(test_network, callback=self.print_callback)
        while(self.connection_result == 0):
            pass
        self.assertTrue(self.connection_result == -1)
        self.connection_result = 0
        self.wifi.remove_network(test_network)

    @unittest.skipIf("edison" not in platform.platform(), 
        "Not suppoted in this platform")
    def test_06_connect_to_reachable_network(self):
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
        self.assertTrue(self.connection_result == 1)
        self.connection_result = 0
        self.assertTrue(self.get_status()[1]['ssid']==test_network['ssid'])
    
    @unittest.skipIf("edison" not in platform.platform(), 
        "Not suppoted in this platform")
    def test_07_hostap_create_after_unseccess_connection(self):
        test_network = {
            'ssid': "somenetwork",
            'password': "password",
            'security': "wpa2psk",
            'identity': "ivan@example.com"
        }
        self.wifi.add_network(test_network)
        self.wifi.start_connecting(test_network, callback=self.print_callback)
        while(self.connection_result == 0):
            pass
        self.assertTrue(self.connection_result == -1)
        self.connection_result = 0
        self.wifi.remove_network(test_network)
        self.assertTrue(self._hostapd_start())

    @unittest.skipIf("edison" not in platform.platform(), 
        "Not suppoted in this platform")
    def test_08_connect_to_reachable_network_from_hostap(self):
        self.assertTrue(self._hostapd_start())
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
        self.assertTrue(self.connection_result == 1)
        self.connection_result = 0
        self.assertTrue(self.get_status()[1]['ssid']==test_network['ssid'])

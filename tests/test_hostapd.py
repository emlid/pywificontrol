import os
import unittest
import platform
import subprocess
from random import randint
from fakewifi import fakeHostAP as HostAP

class HostAPTest(unittest.TestCase):

    def setUp(self):
        if "Ubuntu" in platform.platform():
            cur_path = os.getcwd()
            hostapd_path = cur_path + "/tests/test_files/hostapd.conf"
            hostname_path = cur_path + "/tests/test_files/hostname"
            self.hotspot = HostAP('wlp6s0', hostapd_path, hostname_path)
        else:
            self.hotspot = HostAP('wlan0')

    def tearDown(self):
        pass

    def test_set_hostap_name(self):
        new_name = "testname_{}".format(randint(0,1000))
        self.hotspot.set_hostap_name(new_name)
        mac_end = self.hotspot.get_device_mac()[-6:]
        self.assertEqual(self.hotspot.get_hostap_name(), "{}{}".format(new_name, mac_end))

    def test_set_host_name(self):
        new_name = "testname_{}".format(randint(0,1000))
        self.hotspot.set_host_name(new_name)
        self.assertEqual(self.hotspot.get_host_name(), new_name)

    def test_start_hotspot(self):
        self.hotspot.start()
        self.assertTrue(self.hotspot.started())

    def test_stop_hotspot(self):
        self.hotspot.stop()
        self.assertFalse(self.hotspot.started())

if __name__ == '__main__':
    unittest.main()
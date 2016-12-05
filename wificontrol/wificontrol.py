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

from hostapd import HostAP
from wificommon import WiFi
from wpas import WpaSupplicant

class WiFiControl(object):

    def __init__(self, interface='wlan0'):
        
        self.wifi = WiFi()
        self.wpas = WpaSupplicant(interface)
        self.hotspot = HostAP()

        self.wifi_on = lambda: (self.wpas.started() or self.hotspot.started())

    def start_host_mode(self):
        if not self.hotspot.started():
            self.wpas.stop()
            self.hotspot.start()

    def start_client_mode(self):
        if not self.wpas.started():
            self.wpas.start()
            self.hotspot.stop()

    def turn_on_wifi(self):
        self.wifi.unblock() 
        self.wpas.start()

    def turn_off_wifi(self):
        self.hotspot.stop()
        self.wpas.start()
        self.wifi.block()

    def get_wifi_turned_on(self):
        return self.wifi_on()

    def set_hostap_password(self, password):
        self.hotspot.set_hostap_password(password)

    def get_device_name(self):
        return self.hotspot.get_host_name()

    def get_hostap_name(self):
        return self.hotspot.get_hostap_name()

    def set_device_names(self, name):
        self.wpas.set_p2p_name(name)
        self.hotspot.set_hostap_name(name)
        self.hotspot.set_host_name(name)
        self.wifi.restart_mdns()

    def get_status(self):
        return (self.get_state(), self.wpas.get_status())

    def get_added_networks(self):
        return self.wpas.get_added_networks()

    def add_network(self, network_parameters):
        self.wpas.add_network(network)

    def remove_network(self, network):
        self.wpas.remove_network(network)

    def start_connecting(self, network, callback=None, args=None, timeout=10):
        if callback is None:
            callback = self.revert_on_connect_failure
            args = None
        self.wpas.start_connecting(network, callback, args, timeout)

    def stop_connecting(self):
        self.wpas.stop_connecting()

    def disconnect(self):
        self.wpas.disconnect()

    def get_state(self):
        if self.wpas.started():
            return "wpa_supplicant"
        if self.hotspot.started():
            return "hostapd"
        return "wifi_off"

    def revert_on_connect_failure(self, result):
        if not result:
            self.start_host_mode()

if __name__ == '__main__':
    wificontrol = WiFiControl('wlp6s0')
    print(wificontrol.get_status())

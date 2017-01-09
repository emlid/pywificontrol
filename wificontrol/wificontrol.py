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


from .hostapd import HostAP
from .wificommon import WiFi
from .wpasupplicant import WpaSupplicant


class WiFiControl(object):

    def __init__(self, interface='wlan0',
        wpas_config="/etc/wpa_supplicant/wpa_supplicant.conf",
        p2p_config="/etc/wpa_supplicant/p2p_supplicant.conf",
        hostapd_config="/etc/hostapd/hostapd.conf",
        hostname_config='/etc/hostname'):

        self.wifi = WiFi(interface)
        self.wpasupplicant = WpaSupplicant(interface, wpas_config, p2p_config)
        self.hotspot = HostAP(interface, hostapd_config, hostname_config)

    def start_host_mode(self):
        if not self.hotspot.started():
            self.wpasupplicant.stop()
            self.hotspot.start()

    def start_client_mode(self):
        if not self.wpasupplicant.started():
            self.hotspot.stop()
            self.wpasupplicant.start()

    def turn_on_wifi(self):
        self.wifi.unblock()
        self.wpasupplicant.start()

    def turn_off_wifi(self):
        self.hotspot.stop()
        self.wpasupplicant.start()
        self.wifi.block()

    def is_wifi_on(self):
        return (self.wpasupplicant.started() or self.hotspot.started())

    def set_hostap_password(self, password):
        self.hotspot.set_hostap_password(password)

    def get_device_name(self):
        return self.hotspot.get_host_name()

    def get_hostap_name(self):
        return self.hotspot.get_hostap_name()

    def set_device_names(self, name):
        self.wpasupplicant.set_p2p_name(name)
        self.hotspot.set_hostap_name(name)
        self.hotspot.set_host_name(name)
        self.wifi.restart_dns()

    def get_status(self):
        return (self.get_state(), self.wpasupplicant.get_status())

    def get_added_networks(self):
        return self.wpasupplicant.get_added_networks()

    def get_ip(self):
        return self.wifi.get_device_ip()

    def scan(self):
        self.wpasupplicant.scan()

    def get_scan_results(self):
        return self.wpasupplicant.get_scan_results()

    def add_network(self, network_parameters):
        self.wpasupplicant.add_network(network_parameters)

    def remove_network(self, network):
        self.wpasupplicant.remove_network(network)

    def start_connecting(self, network, callback=None, args=None, timeout=10):
        if callback is None:
            callback = self.revert_on_connect_failure
            args = None
        self.start_client_mode()
        self.wpasupplicant.start_connecting(network, callback, args, timeout)

    def stop_connecting(self):
        self.wpasupplicant.stop_connecting()

    def disconnect(self):
        self.wpasupplicant.disconnect()

    def get_state(self):
        if self.wpasupplicant.started():
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

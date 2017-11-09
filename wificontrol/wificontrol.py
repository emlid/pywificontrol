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


from hostapd import HostAP
from wificommon import WiFi
from wpasupplicant import WpaSupplicant
from utils import PropertyError


class WiFiControl(object):
    WPA_STATE = 'wpa_supplicant'
    HOST_STATE = 'hostapd'
    OFF_STATE = 'wifi_off'

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
        return True

    def start_client_mode(self):
        if not self.wpasupplicant.started():
            self.hotspot.stop()
            self.wpasupplicant.start()
        return True

    def turn_on_wifi(self):
        if self.get_state() == self.OFF_STATE:
            self.wifi.unblock()
            self.wpasupplicant.start()

    def turn_off_wifi(self):
        self.hotspot.stop()
        self.wpasupplicant.stop()
        self.wifi.block()

    def get_wifi_turned_on(self):
        return (self.wpasupplicant.started() or self.hotspot.started())

    def set_hostap_password(self, password):
        return self.hotspot.set_hostap_password(password)

    def get_device_name(self):
        return self.hotspot.get_host_name()

    def get_hostap_name(self):
        return self.hotspot.get_hostap_name()

    def set_device_names(self, name):
        self.wpasupplicant.set_p2p_name(name)
        self.hotspot.set_hostap_name(name)
        self.hotspot.set_host_name(name)
        self.wifi.restart_dns()
        return self.verify_device_names(name)

    def verify_hostap_name(self, name):
        mac_addr = self.hotspot.get_device_mac()[-6:]
        return "{}{}".format(name, mac_addr) == self.hotspot.get_hostap_name()

    def verify_device_names(self, name):
        verified = False
        if name == self.hotspot.get_host_name():
            if name == self.wpasupplicant.get_p2p_name():
                if self.verify_hostap_name(name):
                    verified = True
        return verified

    def get_status(self):
        state = self.get_state()
        wpa_status = None

        if state == self.WPA_STATE:
            try:
                wpa_status = self.wpasupplicant.get_status()
            except PropertyError:
                return state, wpa_status

        return state, wpa_status

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
        state = self.OFF_STATE

        if self.wpasupplicant.started():
            state = self.WPA_STATE
        elif self.hotspot.started():
            state = self.HOST_STATE

        return state

    def revert_on_connect_failure(self, result):
        if not result:
            self.start_host_mode()

    def reconnect(self, result, network):
        if not result:
            self.start_connecting(network)


if __name__ == '__main__':
    wificontrol = WiFiControl('wlp6s0')
    print(wificontrol.get_status())

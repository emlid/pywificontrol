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


from wificommon import WiFi
from utils import CfgFileUpdater
from utils import WpaSupplicantInterface, WpaSupplicantNetwork, WpaSupplicantBSS
from utils import convert_to_wpas_network, convert_to_wificontrol_network, \
    create_security
from utils import FileError
from utils import ServiceError, InterfaceError, PropertyError
from threading import Thread, Event, Timer
import time
import sys


class WpaSupplicant(WiFi):
    wpas_control = lambda self, action: "systemctl {} wpa_supplicant.service && sleep 2".format(
        action)

    def __init__(self, interface,
                 wpas_config="/etc/wpa_supplicant/wpa_supplicant.conf",
                 p2p_config="/etc/wpa_supplicant/p2p_supplicant.conf"):

        super(WpaSupplicant, self).__init__(interface)
        self.wpa_supplicant_path = wpas_config
        self.p2p_supplicant_path = p2p_config

        if (b'bin/wpa_supplicant' not in self.execute_command(
                "whereis wpa_supplicant")):
            raise OSError('No WPA_SUPPLICANT service')

        self.wpa_supplicant_interface = WpaSupplicantInterface(self.interface)
        self.wpa_bss_manager = WpaSupplicantBSS()
        self.wpa_network_manager = WpaSupplicantNetwork()
        self.config_updater = CfgFileUpdater(self.wpa_supplicant_path)

        self.connection_thread = None
        self.connection_event = Event()

        self.connection_timer = None
        self.break_event = Event()

    def started(self):
        wpa_supplicant_started = self.sysdmanager.is_active(
            "wpa_supplicant.service")

        if wpa_supplicant_started:
            self.wpa_supplicant_interface.initialize()

        return wpa_supplicant_started

    def start(self):
        self.execute_command(self.wpas_control("start"))
        self.wpa_supplicant_interface.initialize()

    def stop(self):
        self.execute_command(self.wpas_control("stop"))

    def get_status(self):
        network_params = None
        if self.started():
            network_params = dict()
            network_params['ssid'] = self.get_current_network_ssid()
            network_params['mac address'] = self.get_device_mac()
            network_params['IP address'] = self.get_device_ip()
        return network_params

    def scan(self):
        if self.started():
            self.wpa_supplicant_interface.scan()
            self.wait_scanning()

    def get_scan_results(self):
        if self.started():
            return [self.get_bss_network_info(bss) for bss in
                    self.wpa_supplicant_interface.get_BSSs()]
        else:
            return []

    def get_added_networks(self):
        current_network = None
        if self.started():
            current_network = self.get_status()
        return [convert_to_wificontrol_network(network, current_network) for
                network in self.config_updater.networks]

    def add_network(self, network_parameters):
        network = convert_to_wpas_network(network_parameters)
        try:
            self.config_updater.add_network(network)
        except AttributeError:
            pass
        else:
            if self.started():
                self.wpa_supplicant_interface.add_network(network)

    def remove_network(self, network):
        try:
            self.config_updater.remove_network(network)
        except AttributeError:
            pass
        else:
            if self.started():
                self.wpa_supplicant_interface.remove_network(
                    self.find_network_path(network))

    def start_connecting(self, network, callback=None,
                         args=None, timeout=10):
        self.break_connecting()
        self.connection_thread = Thread(target=self.connect,
                                        args=(network, callback, args))
        self.start_connecting_thread(timeout)

    def connect(self, network, callback, args):
        result = self.connect_to_network(network)
        self.teardown_connection()
        self.callback_response(result, callback, args)

    def callback_response(self, result, callback, args):
        if callback is not None:
            if args is not None:
                callback(result, *args)
            else:
                callback(result)

    def stop_connecting(self):
        self.connection_event.clear()
        self.connection_thread.join()

    def disconnect(self):
        self.wpa_supplicant_interface.disconnect()

    # Scan functions
    def wait_scanning(self):
        while self.wpa_supplicant_interface.get_scanning():
            pass

    def get_bss_network_info(self, bss):
        return {
            "ssid": self.wpa_bss_manager.get_SSID(bss),
            "mac address": self.wpa_bss_manager.get_BSSID(bss),
            "security": self.get_security(bss)
        }

    def get_security(self, bss_path):
        wpa_array = self.wpa_bss_manager.get_WPA(bss_path)
        rsn_array = self.wpa_bss_manager.get_RSN(bss_path)
        proto = self.get_protocol(wpa_array, rsn_array)
        key_mgmt, group = self.get_keymgmt_group(wpa_array, rsn_array, proto)
        return create_security(proto, key_mgmt, group)

    def get_protocol(self, wpa_dict, rsn_dict):
        if not self.is_dict_empty(wpa_dict):
            return "WPA"
        if not self.is_dict_empty(rsn_dict):
            return "RSN"
        return ""

    def get_keymgmt_group(self, wpa_dict, rsn_dict, proto):
        if proto == "WPA":
            return [str(key) for key in wpa_dict['KeyMgmt']], str(
                wpa_dict['Group'])
        if proto == "RSN":
            return [str(key) for key in rsn_dict['KeyMgmt']], str(
                rsn_dict['Group'])
        return [], ""

    def is_dict_empty(self, dict):
        for value in dict.values():
            if value:
                return False
        return True

    # Names changung actions
    def set_p2p_name(self, name='reach'):
        self.replace("^p2p_ssid_postfix=.*", "p2p_ssid_postfix={}".format(name),
                     self.p2p_supplicant_path)

    def get_p2p_name(self):
        return self.re_search("(?<=^p2p_ssid_postfix=).*",
                              self.p2p_supplicant_path)

    # Network actions
    def find_network_path(self, aim_network):
        for network in self.wpa_supplicant_interface.get_networks():
            if self.wpa_network_manager.get_network_SSID(network) == \
                    aim_network['ssid']:
                return network

    def get_current_network_ssid(self):
        self.wpa_supplicant_interface.initialize()
        network = self.wpa_supplicant_interface.get_current_network()
        return self.wpa_network_manager.get_network_SSID(network)

    # Connection actions
    def start_network_connection(self, network):
        if network is not None:
            self.wpa_supplicant_interface.select_network(
                self.find_network_path(network))
        else:
            self.wpa_supplicant_interface.reassociate()

    def wait_untill_connection_complete(self):
        while self.wpa_supplicant_interface.get_state() != "completed":
            if not self.connection_event.is_set():
                raise RuntimeError("Can't connect to network")
            time.sleep(0.5)

    def check_correct_connection(self, aim_network):
        if aim_network is not None:
            if self.get_current_network_ssid() != aim_network['ssid']:
                raise RuntimeError("Network not available")

    def connect_to_network(self, network):
        try:
            self.start_network_connection(network)
            self.wait_untill_connection_complete()
            self.check_correct_connection(network)
        except RuntimeError:
            return False
        else:
            return True

    def start_connecting_thread(self, timeout):
        self.connection_timer = Timer(timeout, self.stop_connecting)
        self.connection_event.set()
        self.connection_thread.start()
        self.connection_timer.start()

    def teardown_connection(self):
        self.connection_thread = None
        self.stop_timer_thread()
        if self.break_event.is_set():
            callback = None
            self.break_event.clear()

    def stop_timer_thread(self):
        try:
            self.connection_timer.cancel()
        except AttributeError:
            pass

    def break_connecting(self):
        if self.connection_thread is not None:
            self.break_event.set()
            try:
                if self.connection_timer.isAlive():
                    self.connection_timer.cancel()
                self.connection_timer = None
                self.stop_connecting()
            except AttributeError:
                pass


if __name__ == '__main__':
    wifi = WpaSupplicant('wlp6s0')
    print(wifi.get_status())

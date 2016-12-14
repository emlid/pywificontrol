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

from wificommon import WiFi
from threading import Thread, Event, Timer
from utils import ConfigurationFileUpdater, NullFileUpdater
from utils import WpaSupplicantInterface, WpaSupplicantNetwork
from utils import convert_to_wpas_network, convert_to_wificontrol_network
from utils import FileError
from utils import ServiceError, InterfaceError, PropertyError

class WpaSupplicant(WiFi):
    wpas_control = lambda self, action: "systemctl {} wpa_supplicant.service && sleep 2".format(action)

    def __init__(self, interface, 
        wpas_config="/etc/wpa_supplicant/wpa_supplicant.conf",
        p2p_config="/etc/wpa_supplicant/p2p_supplicant.conf"):
        
        super(WpaSupplicant, self).__init__(interface)
        self.wpa_supplicant_path = wpas_config
        self.p2p_supplicant_path = p2p_config

        if ("bin/wpa_supplicant" not in self.execute_command("whereis wpa_supplicant")):
            raise OSError('No WPA_SUPPLICANT servise')

        self.wpa_supplicant_interface = WpaSupplicantInterface(self.interface)
        self.wpa_network_manager = WpaSupplicantNetwork()
        try:
            self.config_updater = ConfigurationFileUpdater(self.wpa_supplicant_path)
        except FileError:
            self.config_updater = NullFileUpdater()

        self.connection_thread = None
        self.connection_event = Event()
        
        self.connection_timer = None
        self.break_event = Event()
        
        self.started = lambda: self.sysdmanager.is_active("wpa_supplicant.service")
        
        if self.started():
            self.wpa_supplicant_interface.initialize()

    def start(self):
        self.execute_command(self.wpas_control("start"))
        self.wpa_supplicant_interface.initialize()

    def stop(self):
        self.execute_command(self.wpas_control("stop"))

    def get_status(self):
        network_params = dict()
        try:
            network_params['ssid'] = self.get_current_network_ssid()
        except PropertyError:
            network_params = None
        else:
            network_params['mac address'] = self.get_device_mac()
            network_params['IP address'] = self.get_device_ip()
        finally:
            return network_params

    def get_added_networks(self):
        current_network = self.get_status()
        return [convert_to_wificontrol_network(network, current_network) for network in self.config_updater.networks]

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
                self.wpa_supplicant_interface.remove_network(self.find_network_path(network))

    def start_connecting(self, network, callback=None,
                         args=None, timeout=10):
        self.break_connecting()
        self.connection_thread = Thread(target=self.connect, args=(network, callback, args))
        self.start_connecting_thread(timeout)

    def connect(self, network, callback, args):
        result = self.connect_to_network(network)
        self.teardown_connection()
        self.callback_response(result, callback, args)

    def callback_response(self, result, callback, args):
        if callback is not None:
            if args is not None:
                callback(result, args)
            else:
                callback(result)

    def stop_connecting(self):
        self.connection_event.clear()
        self.connection_thread.join()

    def disconnect(self):
        self.wpa_supplicant_interface.disconnect()

    # Names changung actions
    def set_p2p_name(self, name='reach'):
        self.replace("^p2p_ssid_postfix=.*", "p2p_ssid_postfix={}".format(name), self.p2p_supplicant_path)

    def get_p2p_name(self):
        return self.re_search("(?<=^p2p_ssid_postfix=).*", self.p2p_supplicant_path)
    
    # Network actions
    def find_network_path(self, aim_network):
        for network in self.wpa_supplicant_interface.get_networks():
            if self.wpa_network_manager.get_network_SSID(network) == aim_network['ssid']:
                return network

    def get_current_network_ssid(self):
        network = self.wpa_supplicant_interface.get_current_network()
        return self.wpa_network_manager.get_network_SSID(network)

    # Connection actions
    def start_network_connection(self, network):
        if network is not None:
            self.wpa_supplicant_interface.select_network(self.find_network_path(network))
        else:
            self.wpa_supplicant_interface.reassociate()

    def wait_untill_connection_complete(self):
        while self.wpa_supplicant_interface.get_state() != "completed":
            if not self.connection_event.is_set():
                raise RuntimeError("Can't connect to network")
    
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

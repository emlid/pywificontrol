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

import subprocess
import shlex
import threading

class LaunchException(Exception):
    pass

class ModeChangeException(Exception):
    pass

class ExecutionError(Exception):
    pass

class ReachWiFi(object):
    default_path = {
        'hostapd_path' : "/etc/hostapd/hostapd.conf",
        'wpa_supplicant_path' : "/etc/wpa_supplicant/wpa_supplicant.conf",
        'p2p_supplicant_path' : "/etc/wpa_supplicant/p2p_supplicant.conf"
    }
    launch_start_wpa_service = "systemctl start wpa_supplicant.service"
    launch_stop_wpa_service = "systemctl stop wpa_supplicant.service"
    launch_start_hostapd_service = "systemctl start hostapd.service"
    launch_stop_hostapd_service = "systemctl stop hostapd.service"

    def __init__(self):
        self.hostapd_path = self.default_path['hostapd_path']
        self.wpa_supplicant_path = self.default_path['wpa_supplicant_path']
        self.p2p_supplicant_path = self.default_path['p2p_supplicant_path']

        try:
            self.launch("wpa_supplicant")
            self.launch("hostapd")
        except OSError:
            raise OSError
        except LaunchException:
            pass
        
        self.connection_thread = None
        self.connection_timer = None
        self.connection_event = threading.Event()
        try: 
            self.launch("wpa_cli status")
        except LaunchException:
            self.wpa_supplicant_start = False
            self.hostapd_start = True
            self.network_list = None
        else:
            self.wpa_supplicant_start = True
            self.hostapd_start = False
            self.network_list = self.parse_network_list()

    #Change mode part
    def run_host_mode(self):
        try:
            if not self.wpa_supplicant_start:
                raise ModeChangeException("Already in host mode")
            self.disconnect()
            self.launch(self.launch_stop_wpa_service)
            self.wpa_supplicant_start = False
            self.launch(self.launch_start_hostapd_service)
            self.hostapd_start = True
            return True
        except (LaunchException, ModeChangeException):
            return False

    def run_client_mode(self):
        try:
            if not self.hostapd_start:
                raise ModeChangeException("Already in client mode")
            self.launch(self.launch_stop_hostapd_service)
            self.hostapd_start = False
            self.launch(self.launch_start_wpa_service)
            self.wpa_supplicant_start = True
            self.network_list = self.parse_network_list()
            return True
        except (LaunchException, ModeChangeException):
            return False

    def set_hostap_name(self, name = 'reach'):
        try:
            self.launch("sed -i s/^ssid=.*/ssid={}/ {}".format(name, self.hostapd_path))
            return True
        except LaunchException:
            return False

    def get_hostap_name(self):
        try:
            return self.launch("grep \'^ssid=\' {}".format(a.hostapd_path))[5:-1]
        except LaunchException:
            return None

    def set_p2p_name(self, name = 'reach'):
        try:
            self.launch("sed -i s/^p2p_ssid_postfix=.*/p2p_ssid_postfix={}/ {}".format(name, self.p2p_supplicant_path))
            return True
        except LaunchException:
            return False

    def get_p2p_name(self):
        try:
            return self.launch("grep \'^p2p_ssid_postfix=\' {}".format(a.p2p_supplicant_path))[17:-1]
        except LaunchException:
            return None

    #Client mode part
    def start_scanning(self):
        try:
            self.launch("wpa_cli scan")
            return True
        except LaunchException:
            return False

    def get_scan_results(self):
        try:
            scan_result = self.launch("wpa_cli scan_result").split("\n")[2:-1]
            result = list()
            for network in scan_result:
                result.append((network.split('\t')[0], network.split('\t')[4].decode('string_escape')))
            return result
        except LaunchException:
            return None

    def get_list_added_networks(self):
        return self.network_list

    def get_scan_results_without_added_networks(self):
        #TODO: optimisation...
        curent_scan_results = self.get_scan_results()
        if self.network_list:
            for network in self.network_list:   
                for tuple_network in curent_scan_results:
                    if network[1].strip('\"') == tuple_network[1]:
                        curent_scan_results.pop(curent_scan_results.index(tuple_network))
                        break
        return curent_scan_results

    def add_network(self, mac_ssid_psk):
        try:
            if self.network_list:
                for network in self.network_list:
                    if (mac_ssid_psk[0].encode('utf-8') == network[0]) & (mac_ssid_psk[1].encode('utf-8') == network[1]):
                        raise ExecutionError("Already added")
            r = self.launch("wpa_cli add_network").split("\n")[1]
            self.launch("wpa_cli set_network {} bssid {}".format(r, mac_ssid_psk[0]))
            self.launch(["wpa_cli", "set_network", r, "ssid", "\"" + mac_ssid_psk[1] + "\""])
            self.launch(["wpa_cli", "set_network", r, "psk", "\"" + mac_ssid_psk[2] + "\""])
            self.launch("wpa_cli save_config")
            self.network_list = self.parse_network_list()
            return True
        except (LaunchException, ExecutionError):
            return False

    def remove_network(self, mac_ssid):
        try:
            remove_network_id = self.try_find_network_id_from_ssid(mac_ssid[1].encode('utf-8'))
            if remove_network_id is None:
                raise ExecutionError("No such network")
            self.launch("wpa_cli remove_network {}".format(remove_network_id))
            self.launch("wpa_cli save_config")
            self.launch("wpa_cli reconfigure")
            self.network_list = self.parse_network_list()
            return True
        except (LaunchException, ExecutionError):
            return False

    def start_connecting(self, mac_ssid, callback = None, args = [], timeout = 30):
        if self.connection_thread is not None:
            try:
                if self.connection_timer.isAlive():
                    self.connection_timer.cancel()
                self.connection_timer = None
                self.stop_connecting()
            except AttributeError:
                pass
        self.connection_thread = threading.Thread(target = self.connect, args = (mac_ssid, callback, args))
        self.connection_timer = threading.Timer(timeout, self.stop_connecting)
        self.connection_event.set()
        self.connection_thread.start()
        self.connection_timer.start()

    def connect(self, mac_ssid, callback = None, args = []):
        result = False
        try:
            self.disconnect()

            index_network_for_connect = self.try_find_network_id_from_ssid(mac_ssid[1].encode('utf-8'))
            if index_network_for_connect is None:
                raise ValueError("No such network... Desconnect")

            self.launch("wpa_cli enable_network {}".format(index_network_for_connect))
            while self.network_parameter("wpa_state") != "COMPLETED":
                if not self.connection_event.is_set():
                    raise ExecutionError("Time is out. Disconnect...")

            if (self.network_parameter("ssid") != mac_ssid[1].encode('utf-8')):
                raise ExecutionError("Unable to connect {}. Disconnect...".format(mac_ssid[1].encode('utf-8')))

            result = True
            self.connection_timer.cancel()
        
        except (ValueError, ExecutionError, LaunchException), e:
            self.disconnect()
            print e

        if callback is not None:
            callback(result, args)
        self.connection_thread = None

    def stop_connecting(self):
        self.connection_event.clear()
        self.connection_thread.join()

    def disconnect(self):
        try:
            state = self.network_parameter("wpa_state")
            if state is None:
                raise ExecutionError
            if state != "DISCONNECTED":
                current_network_id = self.try_find_current_network()
                if current_network_id is not None:
                    self.launch("wpa_cli disable_network {}".format(current_network_id))
            self.launch("wpa_cli disconnect")    
            return True
        except (LaunchException, ExecutionError):
            return False

    #Additional functional
    def launch(self, args):
        try:
            result = shlex.split(args)
            args = result
        except AttributeError:
            pass            
        ps = subprocess.Popen(args, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
        ps.wait()
        (out_return, err_return) = ps.communicate()
        if err_return:
            raise LaunchException(err_return)
        else:
            return out_return

    def parse_network_list(self):
        if self.wpa_supplicant_start:
            result = list()
            while True:
                try:
                    list_of_networks = self.launch("wpa_cli list_network").split("\n")[2:-1]
                    break
                except LaunchException:
                    pass        
            for network in list_of_networks: 
                result.append((network.split("\t")[2],network.split("\t")[1]))
            return result
        else:
            return None

    def network_parameter(self, parameter):
        try:
            network_status = self.launch("wpa_cli status").split("\n")[1:-1]
            for network_params in network_status:
                try:
                    network_params.split('=').index(parameter)
                    return network_params.split('=')[1]
                except ValueError:
                    pass
            print "No such value in status list"
            return None
        except LaunchException:
            return None

    def try_find_current_network(self):
        try: 
            network_list = self.launch("wpa_cli list_network").split("\n")[2:-1]
            for network in network_list:
                if network.split('\t')[-1].find('CURRENT') != -1:
                    return network.split('\t')[0]
        except LaunchException:
            return None

    def try_find_network_id_from_ssid(self, ssid):
        if self.network_list is not None:
            for network in self.network_list:
                if network[1].strip('\"') == ssid:
                    return self.network_list.index(network)
        return None

if __name__ == '__main__':
    a = ReachWiFi()
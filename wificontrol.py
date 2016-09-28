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
from threading import Thread, Event, Timer

wpa_template = '''
network={{
\tbssid={}
\tssid=\"{}\"
\tpsk=\"{}\"
}}
'''


class ModeChangeException(Exception):
    pass


class ExecutionError(Exception):
    pass


class ReachWiFi(object):
    default_path = {
        'hostapd_path': "/etc/hostapd/hostapd.conf",
        'wpa_supplicant_path': "/etc/wpa_supplicant/wpa_supplicant.conf",
        'p2p_supplicant_path': "/etc/wpa_supplicant/p2p_supplicant.conf"
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
        except subprocess.CalledProcessError:
            pass

        self.connection_thread = None
        self.connection_timer = None
        self.break_event = Event()
        self.connection_event = Event()
        try:
            self.launch("wpa_cli status")
        except subprocess.CalledProcessError:
            self.wpa_supplicant_start = False
            self.hostapd_start = True
            self.network_list = list()
        else:
            self.wpa_supplicant_start = True
            self.hostapd_start = False
            self.network_list = self.parse_network_list()

    # Change mode part
    def start_host_mode(self):
        try:
            if not self.wpa_supplicant_start:
                raise ModeChangeException("Already in host mode")
            self.disconnect()
            self.launch(self.launch_stop_wpa_service)
            self.launch(self.launch_start_hostapd_service)
        except (subprocess.CalledProcessError, ModeChangeException):
            return False
        else:
            self.wpa_supplicant_start = False
            self.hostapd_start = True
            return True

    def start_client_mode(self):
        try:
            if not self.hostapd_start:
                raise ModeChangeException("Already in client mode")
            self.launch(self.launch_stop_hostapd_service)
            self.launch(self.launch_start_wpa_service)
        except (subprocess.CalledProcessError, ModeChangeException):
            return False
        else:
            self.hostapd_start = False
            self.wpa_supplicant_start = True
            self.network_list = self.parse_network_list()
            return True

    def set_hostap_name(self, name='reach'):
        try:
            self.launch(
                "sed -i s/^ssid=.*/ssid={}/ {}".format(name, 
                                                       self.hostapd_path))
        except subprocess.CalledProcessError:
            return False

    def get_hostap_name(self):
        try:
            return self.launch(
                "grep \'^ssid=\' {}".format(
                    self.hostapd_path))[5:-1]
        except subprocess.CalledProcessError:
            return None

    def set_p2p_name(self, name='reach'):
        try:
            self.launch(
                "sed -i s/^p2p_ssid_postfix=.*/p2p_ssid_postfix={}/ {}".format(
                    name, self.p2p_supplicant_path))
            return True
        except subprocess.CalledProcessError:
            return False

    def get_p2p_name(self):
        try:
            return self.launch(
                "grep \'^p2p_ssid_postfix=\' {}".format(
                    self.p2p_supplicant_path))[17:-1]
        except subprocess.CalledProcessError:
            return None

    def get_status(self):
        if self.wpa_supplicant_start:
            id_current_network = int(self.find_current_network_id())
            if id_current_network != -1:
                network_params = self.network_list[id_current_network]
                network_IP = self.get_network_parameter('ip_address')
                network_params['IP address'] =  network_IP
                network_state = ("wpa_supplicant", network_params)
            else:
                network_state = ("wpa_supplicant", None)
        else:
            network_state = ("hostapd", None)
        return network_state

    # Client mode part
    def start_scanning(self):
        try:
            self.launch("wpa_cli scan")
            return True
        except subprocess.CalledProcessError:
            return False

    def get_scan_results(self):
        result = list()
        try:
            scan_result = self.launch("wpa_cli scan_result").split("\n")[2:-1]
        except subprocess.CalledProcessError:
            return None
        else:
            for network in scan_result:
                result.append({"mac address": network.split('\t')[0],
                               "ssid": network.split('\t')[4].decode('string_escape')})
            return result

    def get_added_networks(self):
        return self.network_list

    def get_unknown_networks(self):
        result = list()
        current_scan_results = self.get_scan_results()
        for network in self.get_added_networks():
            result = [scan_network for scan_network in current_scan_results \
            if network["ssid"] != scan_network["ssid"]]
        return result

    def add_network(self, mac_ssid_psk):
        if (self.network_not_added(mac_ssid_psk) and
            self.add_network_to_wpa_supplicant_file(mac_ssid_psk) and
                self.reconfigure()):
            self.network_list.append(
                {"mac address": mac_ssid_psk["mac address"].encode('utf-8'),
                 "ssid": mac_ssid_psk["ssid"].encode('utf-8')})
            return True
        return False

    def remove_network(self, mac_ssid):
        if not self.network_not_added(mac_ssid):
            remove_network_id = self.find_network_id_from_ssid(mac_ssid["ssid"].encode('utf-8'))
            if (self.remove_network_from_wpa_supplicant_file(
                    remove_network_id) and self.reconfigure()):
                self.network_list = self.parse_network_list()
                return True
        return False

    def start_connecting(self, mac_ssid, callback=None,
                         args=tuple(), timeout=30):
        self.break_connecting()
        network_state = self.get_network_state()
        self.start_client_mode()
        if callback is not None:
            self.connection_thread = Thread(
                target=self.connect,
                args=(mac_ssid, callback, args))
        else:
            self.connection_thread = Thread(
                target=self.connect,
                args=(mac_ssid,
                      self.revert_on_connect_failure,
                      network_state))
        self.connection_timer = Timer(timeout, self.stop_connecting)
        self.connection_event.set()
        self.connection_thread.start()
        self.connection_timer.start()

    def connect(self, mac_ssid, callback=None, args=None):
        result = False
        self.disconnect()
        if (not self.network_not_added(mac_ssid) and
            self.try_to_connect(mac_ssid) and
            self.check_correct_connection(mac_ssid)):
            result = True
        else:
            self.disconnect()

        self.connection_thread = None
        self.stop_timer_thread()
        if self.break_event.is_set():
            callback = None
            self.break_event.clear()

        if callback is not None:
            if args is not None:
                callback(result, args)
            else:
                callback(result)

    def stop_connecting(self):
        self.connection_event.clear()
        self.connection_thread.join()

    def disconnect(self):
        state = self.get_network_parameter("wpa_state")
        if (state is not None and
            state != "DISCONNECTED" and
                self.disable_current_network()):
            try:
                self.launch("wpa_cli disconnect")
            except subprocess.CalledProcessError:
                pass
            else:
                return True
        return False

    # Additional functional
    # ADD NETWORK
    def network_not_added(self, mac_ssid):
        for network in self.network_list:
            if (mac_ssid["mac address"].encode('utf-8') == network["mac address"] and
                mac_ssid["ssid"].encode('utf-8') == network["ssid"]):
                return False
        return True

    def add_network_to_wpa_supplicant_file(self, mac_ssid_psk):
        if self.hostapd_start:
            return self.write_to_wpa_supplicant_file(mac_ssid_psk)
        else:
            return self.use_wpa_cli_add_network(mac_ssid_psk)


    def write_to_wpa_supplicant_file(self, mac_ssid_psk):
        try:
            wpa_supplicant_file = open(self.wpa_supplicant_path, 'a')
            wpa_supplicant_file.write(wpa_template.format(
                mac_ssid_psk["mac address"].encode('utf-8'),
                mac_ssid_psk["ssid"].encode('utf-8'),
                mac_ssid_psk["password"].encode('utf-8')))
            wpa_supplicant_file.close()
            return True
        except IOError as ValueError:
            return False

    def use_wpa_cli_add_network(self, mac_ssid_psk):
        try:
            number = subprocess.check_output(['wpa_cli', 'add_network'],
                    stderr=subprocess.PIPE).strip().split("\n")[-1]
            subprocess.check_output(['wpa_cli', 'set_network', number, 'ssid', 
                                     '\"{}\"'.format(mac_ssid_psk['ssid'].encode('utf-8'))],
                                    stderr=subprocess.PIPE)
            subprocess.check_output(['wpa_cli', 'set_network', number, 'bssid', 
                                     mac_ssid_psk['mac address'].encode('utf-8')],
                                    stderr=subprocess.PIPE)
            subprocess.check_output(['wpa_cli', 'set_network', number, 'psk', 
                                     '\"{}\"'.format(mac_ssid_psk['password'].encode('utf-8'))],
                                    stderr=subprocess.PIPE)
            subprocess.check_output(['wpa_cli', 'save_config'],
                                    stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError:
            return False

    # REMOVE NETWORK
    def remove_network_from_wpa_supplicant_file(self, network_id):
        try:
            self.launch("wpa_cli remove_network {}".format(network_id))
            self.launch("wpa_cli save_config")
            return True
        except subprocess.CalledProcessError:
            return False

    def reconfigure(self):
        try:
            if self.wpa_supplicant_start:
                self.launch("wpa_cli reconfigure")
            return True
        except subprocess.CalledProcessError:
            return False

    # START CONNECTING
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

    def get_network_state(self):
        if self.wpa_supplicant_start:
            id_current_network = int(self.find_current_network_id())
            if id_current_network != -1:
                network_state = ("wpa_supplicant", self.network_list[
                                 id_current_network])
            else:
                network_state = ("wpa_supplicant", None)
        else:
            network_state = ("hostapd", None)
        return network_state

    # CONNECT
    # ONLY FOR THREAD!!!
    def try_to_connect(self, mac_ssid):
        index_network_for_connect = self.find_network_id_from_ssid(mac_ssid["ssid"].encode('utf-8'))
        if (self.reconnect() and
            self.enable_network(index_network_for_connect)):
            if self.wait_untill_connection_complete():
                return True
        return False

    def enable_network(self, network_id):
        try:
            self.launch("wpa_cli enable_network {}".format(
                network_id))
            return True
        except subprocess.CalledProcessError:
            return False

    def wait_untill_connection_complete(self):
        while self.get_network_parameter("wpa_state") != "COMPLETED":
            if not self.connection_event.is_set():
                return False
        return True

    def check_correct_connection(self, mac_ssid):
        if ((self.get_network_parameter("ssid") != mac_ssid["ssid"].encode('utf-8'))):
            return False
        return True

    def reconnect(self):
        try:
            self.launch("wpa_cli reconnect")
            return True
        except (subprocess.CalledProcessError):
            return False

    def stop_timer_thread(self):
        try:
            self.connection_timer.cancel()
        except AttributeError:
            pass

    # CONNECT SAFETY CALLBACK
    def revert_on_connect_failure(self, result, network_state):
        if not result:
            self.return_to_state(network_state)

    def return_to_state(self, network_state):
        if network_state[0] == "hostapd":
            self.start_host_mode()
        elif network_state[0] == "wpa_supplicant":
            if network_state[1] is not None:
                self.start_connecting(network_state[1])
            else:
                self.start_host_mode()

    # DISCONNETCT
    def disable_current_network(self):
        try:
            current_network_id = self.find_current_network_id()
            if current_network_id != -1:
                self.launch("wpa_cli disable_network {}".format(
                    current_network_id))
            return True
        except subprocess.CalledProcessError:
            return False

    # COMMON
    def launch(self, args):
        out_return = subprocess.check_output(
            args, stderr=subprocess.PIPE, shell=True)
        return out_return

    def parse_network_list(self):
        result = list()
        if self.wpa_supplicant_start:
            while True:
                try:
                    list_of_networks = self.launch(
                        "wpa_cli list_network").split("\n")[2:-1]
                    break
                except subprocess.CalledProcessError:
                    pass
            for network in list_of_networks:
                result.append({"mac address": network.split("\t")[2],
                               "ssid": network.split("\t")[1]})
        return result

    def get_network_parameter(self, parameter):
        try:
            network_status = self.launch("wpa_cli status").split("\n")[1:-1]
            for network_params in network_status:
                try:
                    network_params.split('=').index(parameter)
                    return network_params.split('=')[1]
                except ValueError:
                    pass
            return None
        except subprocess.CalledProcessError:
            return None

    def find_current_network_id(self):
        try:
            network_list = self.launch(
                "wpa_cli list_network").split("\n")[2:-1]
            for network in network_list:
                if network.split('\t')[-1].find('CURRENT') != -1:
                    return network.split('\t')[0]
            return -1       
        except subprocess.CalledProcessError:
            return -1

    def find_network_id_from_ssid(self, ssid):
        if self.network_list is not None:
            for network in self.network_list:
                if network["ssid"] == ssid:
                    return self.network_list.index(network)
        return -1

if __name__ == '__main__':
    rwc = ReachWiFi()
    print rwc.network_list
    print rwc.get_status()

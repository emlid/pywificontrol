2# wificontrol code is placed under the GPL license.
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

class wpa_templates(object):
    BASE = '''
network={{
\tssid=\"{}\"
\tkey=\"{}\"
}}
'''

    OPEN = '''
network={{
\tssid=\"{}\"
\tkey_mgmt=NONE
}}
'''

    WEP = '''
network={{
\tssid=\"{}\"
\tkey_mgmt=NONE
\tgroup=WEP104 WEP40
\twep_key0=\"{}\"
}}
'''
    WPAPSK = '''
network={{
\tssid=\"{}\"
\tkey_mgmt=WPA-PSK
\tpairwise=CCMP TKIP
\tgroup=CCMP TKIP WEP104 WP40
\teap=TTLS PEAP TLS
\tpsk=\"{}\"
}}
'''

    WPAEAP = '''
network={{
\tssid=\"{}\"
\tkey_mgmt=WPA-EAP
\tpairwise=CCMP TKIP
\tgroup=CCMP TKIP WEP104 WP40
\teap=TTLS PEAP TLS
\tidentity=\"{}\"
\tpassword=\"{}\"
\tphase1=\"peaplable=0\"
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
        self.network_list = None
        self.wifi_on = True
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

    def turn_on_wifi(self):
        if self.wifi_on:
            return True
        try:
                self.launch(self.launch_start_wpa_service)
        except subprocess.CalledProcessError:
            return False
        else:
            self.wpa_supplicant_start = True
            self.hostapd_start = False
            self.wifi_on = True
            return True

    def turn_off_wifi(self):
        if not self.wifi_on:
            return True
        try:
            if self.wpa_supplicant_start:
                self.launch(self.launch_stop_wpa_service)
            elif self.hostapd_start:
                self.launch(self.launch_stop_hostapd_service)
        except subprocess.CalledProcessError:
            return False
        else:
            self.wpa_supplicant_start = False
            self.hostapd_start = False
            self.wifi_on = False
            return True

    def get_wifi_turned_on(self):
        return self.wifi_on

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
        if self.wifi_on:
            if self.wpa_supplicant_start:
                id_current_network = int(self.find_current_network_id())
                if id_current_network != -1: #TODO
                    network_params = dict()
                    network_params['mac address'] = self.get_network_parameter('bssid')
                    network_params['ssid'] = self.get_network_parameter('ssid')
                    network_params['IP address'] = self.get_network_parameter('ip_address')
                    network_state = ("wpa_supplicant", network_params)
                else:
                    network_state = ("wpa_supplicant", None)
            else:
                network_state = ("hostapd", None)
        else:
            network_state = ("wifi off", None)
        return network_state

    # Client mode part
    def get_added_networks(self):
        self.network_list = self.parse_network_list()
        return self.network_list

    def add_network(self, ssid_psk_security):
        if (self.network_not_added(ssid_psk_security) and
            self.add_network_to_wpa_supplicant_file(ssid_psk_security)):
            self.get_added_networks()
            return True
        return False

    def remove_network(self, ssid):
        if not self.network_not_added(ssid):
            result = self.remove_network_from_wpa_supplicant_file(ssid)
            if (result):
                self.get_added_networks()
                return result
        return False

    def change_priority(self, ssid_list):
        info = self.read_wpa_supplicant_file()
        if info is not None:
            new_file = self.create_new_networks_priority_file(info, ssid_list)
            if new_file is not None:
                return self.write_new_wpa_supplicant_file(new_file)
        return False

    # TODO: reconfigure... and think about list
    def start_connecting(self, ssid, callback=None,
                         args=tuple(), timeout=30):
        self.break_connecting()
        network_state = self.get_network_state()
        self.reconfigure()
        self.start_client_mode()
        if callback is not None:
            self.connection_thread = Thread(
                target=self.connect,
                args=(ssid, callback, args))
        else:
            self.connection_thread = Thread(
                target=self.connect,
                args=(ssid,
                      self.revert_on_connect_failure,
                      network_state))
        self.connection_timer = Timer(timeout, self.stop_connecting)
        self.connection_event.set()
        self.connection_thread.start()
        self.connection_timer.start()

    def connect(self, ssid, callback=None, args=None):
        result = False
        self.disconnect()
        if (not self.network_not_added(ssid) and
            self.try_to_connect(ssid) and
            self.check_correct_connection(ssid)):
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
    def network_not_added(self, ssid):
        for network in self.network_list:
            if (ssid["ssid"].encode('utf-8').decode('string_escape') == network["ssid"].decode('string_escape')):
                return False
        return True

    def add_network_to_wpa_supplicant_file(self, ssid_psk_security):
        return self.write_to_wpa_supplicant_file(ssid_psk_security)

    def write_to_wpa_supplicant_file(self, ssid_psk_security):
        try:
            wpa_supplicant_file = open(self.wpa_supplicant_path, 'a')
            try:
                security = ssid_psk_security['security'].encode('utf-8')
            except KeyError:
                return False
            else:
                network_to_add = self.create_wifi_network(security)
                wpa_supplicant_file.write(network_to_add)
                wpa_supplicant_file.close()
            return True
        except (IOError, ValueError):
            return False

    def create_wifi_network(self, security):
        network = ''
        try:
            if (ssid_psk_security['security'] == 'open'):
                network = wpa_templates.OPEN.format(
                    ssid_psk_security["ssid"].encode('utf-8').decode('string_escape'))
            elif (ssid_psk_security['security'] == 'wep'):
                network = wpa_templates.WEP.format(
                    ssid_psk_security["ssid"].encode('utf-8').decode('string_escape'),
                    ssid_psk_security["password"].encode('utf-8'))
            elif (ssid_psk_security['security'] == 'wpapsk'):
                network = wpa_templates.WPAPSK.format(
                    ssid_psk_security["ssid"].encode('utf-8').decode('string_escape'),
                    ssid_psk_security["password"].encode('utf-8'))
            elif (ssid_psk_security['security'] == 'wpaeap'):
                network = wpa_templates.WPAEAP.format(
                    ssid_psk_security["ssid"].encode('utf-8').decode('string_escape'),
                    ssid_psk_security["identity"].encode('utf-8').decode('string_escape'),
                    ssid_psk_security["password"].encode('utf-8')) 
            else:
                network = wpa_templates.BASE.format(
                    ssid_psk_security["ssid"].encode('utf-8').decode('string_escape'),
                    ssid_psk_security["password"].encode('utf-8'))
            except KeyError:
                pass
        return network

    # REMOVE NETWORK
    def remove_network_from_wpa_supplicant_file(self, ssid):
        return self.remove_under_hostapd_mode(ssid)

    def remove_under_hostapd_mode(self, ssid):
        try:
            wpa_supplicant_file = open(self.wpa_supplicant_path, 'r')
            info = wpa_supplicant_file.read()
            ssid_symbol_num = info.find('{}'.format(ssid['ssid'].encode('utf-8').decode('string_escape')))
            last = info.find('}', ssid_symbol_num) + 2
            first = info.rfind('network', 0, ssid_symbol_num) - 1
            info = info.replace(info[first:last], '')
            wpa_supplicant_file.close()
            
            wpa_supplicant_file = open(self.wpa_supplicant_path, 'w')
            wpa_supplicant_file.write(info)
            wpa_supplicant_file.close()
            return True
        except (IOError, ValueError):
            return False

    def reconfigure(self):
        try:
            if self.wpa_supplicant_start:
                self.launch("wpa_cli reconfigure")
            return True
        except subprocess.CalledProcessError:
            return False


    #CHANGE PRIORITY
    def create_new_networks_priority_file(self, old_file, ssid_list):
        file_header = self.create_wpa_supplicant_header(old_file)
        file_new_networks = self.create_new_file_part_with_network_list(old_file, ssid_list)
        new_file = file_header + file_new_networks
        return new_file

    def create_wpa_supplicant_header(self, wpa_file):
        try:
            head_last = wpa_file.index('\nnetwork={')
        except ValueError:
            return None
        else:
            return wpa_file[0:head_last]

    def create_wpa_supplicant_network_list(self, wpa_file):
        try:
            first = wpa_file.index('\nnetwork={')
        except ValueError:
            return None
        else:
            file_networks = list()
            for network in wpa_file[first:].strip().split('\n\n'):
                file_networks.append('\n' + network + '\n')
            return file_networks

    def create_new_file_part_with_network_list(self, old_file, ssid_list):
        file_network_list_part = ''
        list_network = self.create_wpa_supplicant_network_list(old_file)
        if (list_network is None or
            ssid_list is None):
            return None
        for new_network in ssid_list:
            for old_network in list_network:
                if old_network.find(new_network['ssid'].encode('utf-8').decode('string_escape')) != -1:
                    file_network_list_part += old_network
                    break
        return file_network_list_part

    def read_wpa_supplicant_file(self):
        try:
            wpa_supplicant_file = open(self.wpa_supplicant_path, 'r')
            info = wpa_supplicant_file.read()
            wpa_supplicant_file.close()
        except (IOError, ValueError):
            return None
        else:
            return info

    def write_new_wpa_supplicant_file(self, new_file):
        try:
            wpa_supplicant_file = open(self.wpa_supplicant_path, 'w')
            wpa_supplicant_file.write(new_file)
            wpa_supplicant_file.close()
        except (IOError, ValueError):
            return False
        else:
            return True

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
                network_params = dict()
                network_params['ssid'] = self.get_network_parameter('ssid').decode('string_escape')
                network_state = ("wpa_supplicant", network_params)
            else:
                network_state = ("wpa_supplicant", None)
        else:
            network_state = ("hostapd", None)
        return network_state

    # CONNECT
    # ONLY FOR THREAD!!!
    def try_to_connect(self, ssid):
        index_network_for_connect = self.find_network_id_from_ssid(ssid["ssid"].encode('utf-8').decode('string_escape'))
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

    def check_correct_connection(self, ssid):
        if ((self.get_network_parameter("ssid").decode('string_escape') != ssid["ssid"].encode('utf-8').decode('string_escape'))):
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
        return self.parse_under_hostapd()

    def parse_under_hostapd(self):
        result = list()
        try:
            wpa_supplicant_file = open(self.wpa_supplicant_path, 'r')
            info = wpa_supplicant_file.read()
        except (IOError, ValueError):
            return []
        else:
            first = info.find('network')
            info = info[first:].strip()
            list_of_networks = info.split('}\n')
            for network in list_of_networks:
                network_to_add = dict()
                ssid = network.find('ssid')
                if ssid != -1:
                    ssid_last = network.find('\n', ssid)
                    network_to_add['ssid'] = network[ssid + 5:ssid_last].strip('\"')
                else:
                    network_to_add['ssid'] = 'Unknown'
                result.append(network_to_add)
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
        try:
            network_list = self.launch(
                "wpa_cli list_network").split('\n')[2:-1]
        except subprocess.CalledProcessError:
            return -1
        else:
            for network in network_list:
                if network.decode('string_escape').find(ssid) != -1:
                    return int(network.split('\t')[0])
            return -1

if __name__ == '__main__':
    rwc = ReachWiFi()
    print rwc.get_added_networks()
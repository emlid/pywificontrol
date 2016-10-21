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
\tgroup=CCMP TKIP
\teap=TTLS PEAP TLS
\tpsk=\"{}\"
}}
'''
    WPA2PSK = '''
network={{
\tssid=\"{}\"
\tproto=RSN
\tkey_mgmt=WPA-PSK
\tpairwise=CCMP TKIP
\tgroup=CCMP TKIP
\teap=TTLS PEAP TLS
\tpsk=\"{}\"
}}
'''

    WPAEAP = '''
network={{
\tssid=\"{}\"
\tkey_mgmt=WPA-EAP
\tpairwise=CCMP TKIP
\tgroup=CCMP TKIP
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

class wificontrol(object):
    _default_path = {
        'hostapd_path': "/etc/hostapd/hostapd.conf",
        'wpa_supplicant_path': "/etc/wpa_supplicant/wpa_supplicant.conf",
        'p2p_supplicant_path': "/etc/wpa_supplicant/p2p_supplicant.conf",
        'hostname_path': '/etc/hostname'
    }
    _launch_start_wpa_service = "systemctl start wpa_supplicant.service"
    _launch_stop_wpa_service = "systemctl stop wpa_supplicant.service"
    _launch_start_hostapd_service = "systemctl start hostapd.service"
    _launch_stop_hostapd_service = "systemctl stop hostapd.service"
    _launch_restart_mdns = "systemctl restart mdns && sleep 2"
    _launch_rfkill_block_wifi = "rfkill block wifi"
    _launch_rfkill_unblock_wifi = "rfkill unblock wifi"

    def __init__(self, interface='wlan0'):
        self.hostapd_path = self._default_path['hostapd_path']
        self.wpa_supplicant_path = self._default_path['wpa_supplicant_path']
        self.p2p_supplicant_path = self._default_path['p2p_supplicant_path']
        self.hostname_path = self._default_path['hostname_path']
        self.interface = interface
        try:
            self._launch("wpa_supplicant")
        except OSError:
            raise OSError('No WPA_SUPPLICANT servise')
        except subprocess.CalledProcessError:
            try:
                self._launch("hostapd")
            except OSError:
                raise OSError('No HOSTAPD servise')
            except subprocess.CalledProcessError:
                pass

        self._connection_thread = None
        self._connection_timer = None
        self._break_event = Event()
        self._connection_event = Event()
        self._network_list = None
        self._wifi_on = True
        try:
            self._launch("wpa_cli status")
        except subprocess.CalledProcessError:
            self._wpa_supplicant_start = False
            self._hostapd_start = True
            self._network_list = list()
        else:
            self._wpa_supplicant_start = True
            self._hostapd_start = False
            self._network_list = self._parse_network_list()

    # Change mode part
    def start_host_mode(self):
        try:
            if (self._hostapd_start and
                not self._wpa_supplicant_start):
                raise ModeChangeException("Already in host mode")
            self.disconnect()
            self._launch(self._launch_stop_wpa_service)
            self._launch(self._launch_start_hostapd_service)
        except subprocess.CalledProcessError:
            return False
        except ModeChangeException, error:
            print error
            return True
        else:
            self._wpa_supplicant_start = False
            self._hostapd_start = True
            return True

    def start_client_mode(self):
        try:
            if (self._wpa_supplicant_start and
                not self._hostapd_start):
                raise ModeChangeException("Already in client mode")
            self._launch(self._launch_stop_hostapd_service)
            self._launch(self._launch_start_wpa_service)
        except subprocess.CalledProcessError:
            return False
        except ModeChangeException, error:
            print error
            return True
        else:
            self._hostapd_start = False
            self._wpa_supplicant_start = True
            self._reconnect()
            self._network_list = self._parse_network_list()
            return True

    def turn_on_wifi(self):
        if self._wifi_on:
            return True
        try:
            self._launch(self._launch_rfkill_unblock_wifi)
            self._launch(self._launch_start_wpa_service)
        except subprocess.CalledProcessError:
            return False
        else:
            self._wpa_supplicant_start = True
            self._hostapd_start = False
            self._wifi_on = True
            return True

    def turn_off_wifi(self):
        if not self._wifi_on:
            return True
        try:
            if self._wpa_supplicant_start:
                self._launch(self._launch_stop_wpa_service)
            elif self._hostapd_start:
                self._launch(self._launch_stop_hostapd_service)
            self._launch(self._launch_rfkill_block_wifi)
        except subprocess.CalledProcessError:
            return False
        else:
            self._wpa_supplicant_start = False
            self._hostapd_start = False
            self._wifi_on = False
            return True

    def get_wifi_turned_on(self):
        return self._wifi_on

    def _set_hostap_name(self, name='reach'):
        try:
            config = self._launch("ifconfig {}".format(self.interface))
            first = config.find('HWaddr') + 18
            last = first + 6
            mac_addr = config[first:last]
            self._launch(
                "sed -i s/^ssid=.*/ssid={}{}/ {}".format(name, mac_addr,
                                                         self.hostapd_path))
        except subprocess.CalledProcessError:
            return False
        else:
            return True

    def get_hostap_name(self):
        try:
            return self._launch(
                "grep \'^ssid=\' {}".format(
                    self.hostapd_path))[5:-1]
        except subprocess.CalledProcessError:
            return None

    def _set_host_name(self, name='reach'):
        try:
            hostname_file = open(self.hostname_path, 'w')
        except IOError:
            return False
        else:
            hostname_file.write(name + '\n')
            hostname_file.close()
            try:
                self._launch('hostname -F {}'.format(self.hostname_path))
            except subprocess.CalledProcessError:
                return False
            else:
                return True

    def _get_host_name(self):
        try:
            return self._launch("cat {}".format(self.hostname_path)).strip()
        except subprocess.CalledProcessError:
            return None

    def set_p2p_name(self, name='reach'):
        try:
            self._launch(
                "sed -i s/^p2p_ssid_postfix=.*/p2p_ssid_postfix={}/ {}".format(
                    name, self.p2p_supplicant_path))
        except subprocess.CalledProcessError:
            return False
        else:
            return True

    def _get_p2p_name(self):
        try:
            return self._launch(
                "grep \'^p2p_ssid_postfix=\' {}".format(
                    self.p2p_supplicant_path))[17:-1]
        except subprocess.CalledProcessError:
            return None

    def set_hostap_password(self, password):
        try:
            self._launch(
                "sed -i s/^wpa_passphrase=.*/wpa_passphrase={}/ {}".format(
                    password, self.hostapd_path))
        except subprocess.CalledProcessError:
            return False
        else:
            return True

    def get_device_name(self):
        return self._get_host_name()

    def set_device_names(self, name):
        self._set_hostap_name(name)
        self.set_p2p_name(name)
        self._set_host_name(name)
        try:
            self._launch(self._launch_restart_mdns)
        except subprocess.CalledProcessError:
            return False
        else:
            return True

    def get_status(self):
        if self._wifi_on:
            if self._wpa_supplicant_start:
                id_current_network = int(self._find_current_network_id())
                if id_current_network != -1:
                    network_params = dict()
                    network_params['mac address'] = self._get_network_parameter(
                        'bssid')
                    network_params['ssid'] = self._get_network_parameter('ssid')
                    network_params['IP address'] = self._get_network_parameter(
                        'ip_address')
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
        self._network_list = self._parse_network_list()
        return self._network_list

    def add_network(self, ssid_psk_security):
        if (self._network_not_added(ssid_psk_security) and
                self._add_network_to_wpa_supplicant_file(ssid_psk_security)):
            self.get_added_networks()
            return True
        return False

    def remove_network(self, ssid):
        if not self._network_not_added(ssid):
            result = self._remove_network_from_wpa_supplicant_file(ssid)
            if (result):
                self.get_added_networks()
                return True
        return False

    def change_priority(self, ssid_list):
        info = self._read_wpa_supplicant_file()
        if info is not None:
            new_file = self._create_new_networks_priority_file(info, ssid_list)
            if new_file is not None:
                return self._write_new_wpa_supplicant_file(new_file)
        return False

    def start_connecting(self, ssid, callback=None,
                         args=None, timeout=10, any_network=False):
        self._break_connecting()
        network_state = self._get_network_state()
        self.start_client_mode()
        while (not self._reconfigure()):
            pass
        if callback is not None:
            self._connection_thread = Thread(
                target=self.connect,
                args=(ssid, callback, any_network, args))
        else:
            self._connection_thread = Thread(
                target=self.connect,
                args=(ssid,
                      self._revert_on_connect_failure,
                      any_network, network_state))
        self._connection_timer = Timer(timeout, self.stop_connecting)
        self._connection_event.set()
        self._connection_thread.start()
        self._connection_timer.start()

    def connect(self, ssid, callback=None, any_network=False, args=None):
        result = False
        if not any_network:
            self._disable_all_networks()
            if (not self._network_not_added(ssid) and
                self._try_to_connect(ssid) and
                    self._check_correct_connection(ssid)):
                result = True
            else:
                self.disconnect()
        else:
            if (self._reconnect() and
                self._wait_untill_connection_complete()):
                result = True

        self._connection_thread = None
        self._stop_timer_thread()
        if self._break_event.is_set():
            callback = None
            self._break_event.clear()

        if callback is not None:
            if args is not None:
                callback(result, args)
            else:
                callback(result)

    def stop_connecting(self):
        self._connection_event.clear()
        self._connection_thread.join()

    def disconnect(self):
        state = self._get_network_parameter("wpa_state")
        if (state is not None and
            state != "DISCONNECTED" and
                self._disable_current_network()):
            try:
                self._launch("wpa_cli disconnect")
            except subprocess.CalledProcessError:
                pass
            else:
                return True
        return False

    def _disable_all_networks(self):
        try:
            self._launch('wpa_cli disable_network all')
        except subprocess.CalledProcessError:
            return False
        else:
            return True

    # Additional functional
    # ADD NETWORK
    def _network_not_added(self, ssid):
        for network in self._network_list:
            if (ssid["ssid"].encode('utf-8').decode('string_escape') ==
                    network["ssid"].decode('string_escape')):
                return False
        return True

    def _add_network_to_wpa_supplicant_file(self, ssid_psk_security):
        try:
            security = ssid_psk_security['security'].encode('utf-8')
        except KeyError:
            return False
        else:
            network_to_add = self._create_wifi_network(ssid_psk_security,
                                                      security)
            if not network_to_add:
                return False
            try:
                wpa_supplicant_file = open(self.wpa_supplicant_path, 'a')
                wpa_supplicant_file.write(network_to_add)
                wpa_supplicant_file.close()
            except IOError:
                return False
            else:
                return True

    def _create_wifi_network(self, ssid_psk, security):
        network = ''
        try:
            if (security == 'open'):
                network = wpa_templates.OPEN.format(
                    ssid_psk["ssid"].encode('utf-8').decode('string_escape'))
            elif (security == 'wep'):
                network = wpa_templates.WEP.format(
                    ssid_psk["ssid"].encode('utf-8').decode('string_escape'),
                    ssid_psk["password"].encode('utf-8'))
            elif (security == 'wpapsk'):
                network = wpa_templates.WPAPSK.format(
                    ssid_psk["ssid"].encode('utf-8').decode('string_escape'),
                    ssid_psk["password"].encode('utf-8'))
            elif (security == 'wpa2psk'):
                network = wpa_templates.WPA2PSK.format(
                    ssid_psk["ssid"].encode('utf-8').decode('string_escape'),
                    ssid_psk["password"].encode('utf-8'))
            elif (security == 'wpaeap'):
                network = wpa_templates.WPAEAP.format(
                    ssid_psk["ssid"].encode('utf-8').decode('string_escape'),
                    ssid_psk["identity"].encode('utf-8').
                    decode('string_escape'),
                    ssid_psk["password"].encode('utf-8'))
            else:
                network = wpa_templates.BASE.format(
                    ssid_psk["ssid"].encode('utf-8').decode('string_escape'),
                    ssid_psk["password"].encode('utf-8'))
        except KeyError:
            pass
        return network

    # REMOVE NETWORK
    def _remove_network_from_wpa_supplicant_file(self, ssid):
        info = self._read_wpa_supplicant_file()
        if not info:
            return False
        ssid_symbol_num = info.find('{}'.format(
            ssid['ssid'].encode('utf-8').decode('string_escape')))
        last = info.find('}', ssid_symbol_num) + 2
        first = info.rfind('\nnetwork', 0, ssid_symbol_num)
        info = info.replace(info[first:last], '')
        if not self._write_new_wpa_supplicant_file(info):
            return False
        return True

    def _reconfigure(self):
        try:
            if self._wpa_supplicant_start:
                self._launch("wpa_cli _reconfigure")
            return True
        except subprocess.CalledProcessError:
            return False

    # CHANGE PRIORITY
    def _create_new_networks_priority_file(self, old_file, ssid_list):
        file_header = self._create_wpa_supplicant_header(old_file)
        file_new_networks = self._create_new_file_part_with_network_list(
            old_file, ssid_list)
        new_file = file_header + file_new_networks
        return new_file

    def _create_wpa_supplicant_header(self, wpa_file):
        try:
            head_last = wpa_file.index('\nnetwork={')
        except ValueError:
            return None
        else:
            return wpa_file[0:head_last]

    def _create_wpa_supplicant_network_list(self, wpa_file):
        try:
            first = wpa_file.index('\nnetwork={')
        except ValueError:
            return None
        else:
            file_networks = list()
            for network in wpa_file[first:].strip().split('\n\n'):
                file_networks.append('\n' + network + '\n')
            return file_networks

    def _create_new_file_part_with_network_list(self, old_file, ssid_list):
        file_network_list_part = ''
        list_network = self._create_wpa_supplicant_network_list(old_file)
        if (list_network is None or
                ssid_list is None):
            return None
        for new_network in ssid_list:
            for old_network in list_network:
                if old_network.find(new_network['ssid'].encode('utf-8').
                                    decode('string_escape')) != -1:
                    file_network_list_part += old_network
                    break
        return file_network_list_part

    def _read_wpa_supplicant_file(self):
        try:
            wpa_supplicant_file = open(self.wpa_supplicant_path, 'r')
            info = wpa_supplicant_file.read()
            wpa_supplicant_file.close()
        except (IOError, ValueError):
            return None
        else:
            return info

    def _write_new_wpa_supplicant_file(self, new_file):
        try:
            wpa_supplicant_file = open(self.wpa_supplicant_path, 'w')
            wpa_supplicant_file.write(new_file)
            wpa_supplicant_file.close()
        except (IOError, ValueError):
            return False
        else:
            return True

    # START CONNECTING
    def _break_connecting(self):
        if self._connection_thread is not None:
            self._break_event.set()
            try:
                if self._connection_timer.isAlive():
                    self._connection_timer.cancel()
                self._connection_timer = None
                self.stop_connecting()
            except AttributeError:
                pass

    def _get_network_state(self):
        if self._wpa_supplicant_start:
            id_current_network = int(self._find_current_network_id())
            if id_current_network != -1:
                network_params = dict()
                network_params['ssid'] = self._get_network_parameter(
                    'ssid').decode('string_escape')
                network_state = ("wpa_supplicant", network_params)
            else:
                network_state = ("wpa_supplicant", None)
        else:
            network_state = ("hostapd", None)
        return network_state

    # CONNECT
    # ONLY FOR THREAD!!!
    def _try_to_connect(self, ssid):
        index_network_for_connect = self._find_network_id_from_ssid(
            ssid["ssid"].encode('utf-8').decode('string_escape'))
        if (self._reconnect() and
                self._enable_network(index_network_for_connect)):
            if self._wait_untill_connection_complete():
                return True
        return False

    def _enable_network(self, network_id):
        try:
            self._launch("wpa_cli _enable_network {}".format(
                network_id))
            return True
        except subprocess.CalledProcessError:
            return False

    def _wait_untill_connection_complete(self):
        while self._get_network_parameter("wpa_state") != "COMPLETED":
            if not self._connection_event.is_set():
                return False
        return True

    def _check_correct_connection(self, ssid):
        if (self._get_network_parameter("ssid").decode('string_escape')
                != ssid["ssid"].encode('utf-8').decode('string_escape')):
            return False
        return True

    def _reconnect(self):
        try:
            self._launch("wpa_cli _reconnect")
            return True
        except (subprocess.CalledProcessError):
            return False

    def _stop_timer_thread(self):
        try:
            self._connection_timer.cancel()
        except AttributeError:
            pass

    # CONNECT SAFETY CALLBACK
    def _revert_on_connect_failure(self, result, network_state):
        if not result:
            self.start_host_mode()

    # DISCONNETCT
    def _disable_current_network(self):
        try:
            current_network_id = self._find_current_network_id()
            if current_network_id != -1:
                self._launch("wpa_cli disable_network {}".format(
                    current_network_id))
            return True
        except subprocess.CalledProcessError:
            return False

    # COMMON
    def _launch(self, args):
        out_return = subprocess.check_output(
            args, stderr=subprocess.PIPE, shell=True)
        return out_return

    def _parse_network_list(self):
        info = self._read_wpa_supplicant_file()
        if not info:
            return []
        try:
            result = list()
            first = info.index('network')
        except ValueError:
            return []
        else:
            info = info[first:].strip()
            list_of_networks = info.split('}\n')
            for network in list_of_networks:
                network_to_add = dict()
                ssid = network.find('ssid')
                if ssid != -1:
                    ssid_last = network.find('\n', ssid)
                    network_to_add['ssid'] = network[
                        ssid + 5:ssid_last].strip('\"')
                else:
                    network_to_add['ssid'] = 'Unknown'
                security = network.find('key_mgmt')
                if security != -1:
                    security_last = network.find('\n', security)
                    if (network[security +
                                9:security_last].strip('\"') == 'NONE'):
                        if (network.find('WEP') != -1):
                            network_to_add['security'] = 'WEP'
                        else:
                            network_to_add['security'] = 'OPEN'
                    elif (network.find('proto') != -1):
                        network_to_add['security'] = 'WPA2-PSK'
                    else:
                        network_to_add['security'] = network[
                            security + 9:security_last].strip('\"')
                else:
                    network_to_add['security'] = 'NONE'
                result.append(network_to_add)
            return result

    def _get_network_parameter(self, parameter):
        try:
            network_status = self._launch("wpa_cli status").split("\n")[1:-1]
            for network_params in network_status:
                try:
                    network_params.split('=').index(parameter)
                    return network_params.split('=')[1]
                except ValueError:
                    pass
            return None
        except subprocess.CalledProcessError:
            return None

    def _find_current_network_id(self):
        try:
            _network_list = self._launch(
                "wpa_cli list_network").split("\n")[2:-1]
            for network in _network_list:
                if network.split('\t')[-1].find('CURRENT') != -1:
                    return network.split('\t')[0]
            return -1
        except subprocess.CalledProcessError:
            return -1

    def _find_network_id_from_ssid(self, ssid):
        try:
            _network_list = self._launch(
                "wpa_cli list_network").split('\n')[2:-1]
        except subprocess.CalledProcessError:
            return -1
        else:
            for network in _network_list:
                if network.decode('string_escape').find(ssid) != -1:
                    return int(network.split('\t')[0])
            return -1

if __name__ == '__main__':
    rwc = wificontrol()
    print rwc.get_added_networks()

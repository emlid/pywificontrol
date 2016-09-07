import subprocess
import shlex
import time
import threading

class LaunchException(Exception):
    pass

class ModeChangeException(Exception):
    pass

class ExecutionError(Exception):
    pass

class ReachWiFi():
    default_path = {
        'hostapd_path' : "/etc/hostapd/hostapd.conf",
        'wpa_supplicant_path' : "/etc/wpa_supplicant/wpa_supplicant.conf",
    }
    launch_start_wpa_service = "systemctl start wpa_supplicant.service"
    launch_stop_wpa_service = "systemctl stop wpa_supplicant.service"
    launch_start_hostapd_service = "systemctl start hostapd.service"
    launch_stop_hostapd_service = "systemctl stop hostapd.service"

    def __init__(self):
        self.hostapd_path = self.default_path['hostapd_path']
        self.wpasupplicant_path = self.default_path['wpa_supplicant_path']

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
            self.wpa_sup_start = False
            self.hostapd_start = True
            self.network_list = None
        else:
            self.wpa_sup_start = True
            self.hostapd_start = False
            self.network_list = self.parse_wpa_conf_file()

    def launch(self, args): #todo other return value
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

    #Host part
    def start_host_mode(self):
        try:
            if not self.wpa_sup_start:
                raise ModeChangeException("Already in host mode")
            self.disconnect()
            self.launch(self.launch_stop_wpa_service)
            self.wpa_sup_start = False
            self.launch(self.launch_start_hostapd_service)
            self.hostapd_start = True
            return True
        except (LaunchException, ModeChangeException):
            return False

    def start_client_mode(self):
        try:
            if not self.hostapd_start:
                raise ModeChangeException("Already in client mode")
            self.launch(self.launch_stop_hostapd_service)
            self.hostapd_start = False
            self.launch(self.launch_start_wpa_service)
            self.wpa_sup_start = True
            self.network_list = self.parse_wpa_conf_file()
            return True
        except (LaunchException, ModeChangeException):
            return False


    #Client part
    def scan(self):
        try:
            self.launch("wpa_cli scan")
            return True
        except LaunchException:
            return False

    def scan_results(self):
        try:
            scan_result = self.launch("wpa_cli scan_result").split("\n")[2:-1]
            result = list()
            for network in scan_result:
                result.append((network.split('\t')[0], network.split('\t')[4].decode('string_escape')))
            return result
        except LaunchException:
            return False

    def list_network(self):
        return self.network_list

    def show_network_list(self):
        try:
            return self.launch("wpa_cli list_network").split("\n")[2:-1]
        except LaunchException:
            return None

    def parse_wpa_conf_file(self):
        result = list()
        while self.show_network_list() is None:
            pass
        list_of_networks = self.show_network_list()
        for network in list_of_networks: 
            result.append((network.split("\t")[2],network.split("\t")[1]))
        return result

    def delta_added_scan(self):
        cur_scan = self.scan_results()
        if self.network_list:
            for key in self.network_list:   
                for tuple_network in cur_scan:
                    if key[1].strip('\"') == tuple_network[1]:
                        cur_scan.pop(cur_scan.index(tuple_network))
                        break
        return cur_scan

    def add_network(self, args):
        try:
            if self.network_list:
                for key in self.network_list:
                    if (args[0].encode('utf-8') == key[0]) & (args[1].encode('utf-8') == key[1]):
                        raise ExecutionError("Already added")
            r = self.launch("wpa_cli add_network").split("\n")[1]
            self.launch(['wpa_cli', 'set_network', r, 'bssid', args[0]])
            self.launch(['wpa_cli', 'set_network', r, 'ssid', '\"'+args[1]+'\"'])
            self.launch(['wpa_cli', 'set_network', r, 'psk', '\"'+args[2]+'\"'])
            self.launch("wpa_cli save_config")
            self.network_list = self.parse_wpa_conf_file()
            return True
        except (LaunchException, ExecutionError):
            return False


    def disconnect(self):
        try:
            state = self.network_parameter("wpa_state")
            if state is None:
                raise ExecutionError
            if state != "DISCONNECTED":
                current_network_id = self.try_find_current_network()
                if current_network_id is not None:
                    self.launch("wpa_cli disable_network " + current_network_id)
            self.launch("wpa_cli disconnect")    
            return True
        except (LaunchException, ExecutionError):
            return False

    def connect(self, mac_ssid, callback = None, socketio = None, timeout = 50):
        if self.connection_thread is not None:
            try:
                if self.connection_timer.isAlive():
                    self.connection_timer.cancel()
                self.connection_timer = None
                self.stop_connection_thread()
            except AttributeError:
                pass
        self.connection_thread = threading.Thread(target = self.connection, args = [mac_ssid, callback, socketio])
        self.connection_timer = threading.Timer(timeout, self.stop_connection_thread)
        self.connection_event.set()
        self.connection_thread.start()
        self.connection_timer.start()


    def connection(self, mac_ssid, callback, socketio):
        try:
            if not self.disconnect():
                raise ExecutionError("No wpa_supplicant service")
            ind_conn = self.network_list.index(self.find_tuple_ssid(mac_ssid[1].encode('utf-8')))
            self.launch("wpa_cli enable_network %s" % ind_conn)
            while self.network_parameter("wpa_state") != "COMPLETED":
                if not self.connection_event.is_set():
                    raise ExecutionError("Time is out. Disconnect...")
            if (self.network_parameter("ssid") != mac_ssid[1].encode('utf-8')):
                raise ExecutionError("Unable to connect %s. Disconnect..." % mac_ssid[1].encode('utf-8'))
            if callback is not None:
                callback(socketio, True)
            self.connection_timer.cancel()
            return True
        
        except (ValueError, ExecutionError, LaunchException), e:
            self.disconnect()
            print e
            if callback is not None:
                callback(socketio, False)
            return False


    def stop_connection_thread(self):
        self.connection_event.clear()
        self.connection_thread.join()
        self.connection_thread = None

    def remove_network(self, mac_ssid):
        try:
            tuple_network = self.find_tuple_ssid(mac_ssid[1].encode('utf-8'))
            if tuple_network is None:
                raise ExecutionError("No such network")
            index = self.network_list.index(tuple_network)
            self.network_list.pop(index)
            self.launch("wpa_cli remove_network %s" % index)
            self.launch("wpa_cli save_config")
            self.launch("wpa_cli reconfigure")
            self.network_list = self.parse_wpa_conf_file()
        except (LaunchException, ExecutionError):
            return False

    def try_find_current_network(self):
        network_list = self.show_network_list()
        if network_list is not None:
            for network in network_list:
                if network.split('\t')[-1].find('CURRENT') != -1:
                    return network.split('\t')[0]
        return None

    def find_tuple_ssid(self, ssid):
        if self.network_list is not None:
            for network in self.network_list:
                if network[1].strip('\"') == ssid:
                    return network
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

if __name__ == '__main__':
    a = ReachWiFi()
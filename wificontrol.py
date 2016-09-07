import subprocess
import shlex
import time
import threading

class ReachWiFi():
    def __init__(self, hostapd_path = "/etc/hostapd/hostapd.conf", wpasupplicant_path = "/etc/wpa_supplicant/wpa_supplicant.conf"):
        self.hostapd_path = hostapd_path
        self.wpasupplicant_path = wpasupplicant_path
        
        self.connection_thread = None
        self.connection_timer = None
        self.connection_event = threading.Event() 
        status = self.write("wpa_cli status")
        if not status:
            self.wpa_sup_start = False
            self.hostapd_start = True
            self.network_list = None
        else:
            self.wpa_sup_start = True
            self.hostapd_start = False
            self.network_list = self.parse_wpa_conf_file()

    def __del__(self):
        pass

    def write(self, args): #todo other return value
        try:
            result = shlex.split(args)
            args = result
        except AttributeError:
            pass
            
        ps = subprocess.Popen(args, stdout=subprocess.PIPE)
        ps.wait()
        (ret, ret2) = ps.communicate()
        return ret

    #Host part
    def start_host_mode(self):
        if not self.wpa_sup_start:
            print "Already in host mode"
            return
        self.write("wpa_cli disconnect")
        self.write("systemctl stop wpa_supplicant.service")
        self.wpa_sup_start = False
        self.write("systemctl start hostapd.service")
        #self.write("hostapd -B " + self.hostapd_path)
        self.hostapd_start = True

    def start_client_mode(self):
        if not self.hostapd_start:
            print "Already in client mode"
            return
        self.write("systemctl stop hostapd.service")
        self.hostapd_start = False
        self.start_wpa_supplicant()
        self.wpa_sup_start = True
        self.network_list = self.parse_wpa_conf_file()


    #Client part
    def start_wpa_supplicant(self, interface = 'wlan0'):
        #self.write("wpa_supplicant -B -i " + interface + " -c " + self.wpasupplicant_path)
        self.write("systemctl start wpa_supplicant.service")

    def scan(self):
        self.write("wpa_cli scan")

    def scan_results(self):
        scan_result = self.write("wpa_cli scan_result").split("\n")[2:-1]
        result = list()
        for network in scan_result:
            result.append((network.split('\t')[0], network.split('\t')[4].decode('string_escape')))
            #print network.split('\t')[0] + " " + network.split('\t')[4].decode('string_escape')
        return result

    def show_network_list(self):
        return self.write("wpa_cli list_network").split("\n")[2:-1]

    def parse_wpa_conf_file(self):
        result = list()
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
        else:
            return cur_scan

    def add_network(self, args):
        if self.network_list:
            for key in self.network_list:
                if (args[0].encode('utf-8') == key[0]) & (args[1].encode('utf-8') == key[1]):
                    print "Already added"
                    return None
        r = self.write("wpa_cli add_network").split("\n")[1]
        self.write(['wpa_cli', 'set_network', r, 'bssid', args[0]])
        self.write(['wpa_cli', 'set_network', r, 'ssid', '\"'+args[1]+'\"'])
        self.write(['wpa_cli', 'set_network', r, 'psk', '\"'+args[2]+'\"'])
        #self.write("wpa_cli enable_network %s" % r)
        self.write("wpa_cli save_config")
        self.network_list = self.parse_wpa_conf_file()


    def disconnect(self):
        if self.network_parameter("wpa_state") != "DISCONNECTED":
            current_network_id = self.try_find_current_network()
            if current_network_id is not None:
                self.write("wpa_cli disable_network " + current_network_id)
        self.write("wpa_cli disconnect")    

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
        self.disconnect()
        try:
            ind_conn = self.network_list.index(self.find_tuple_ssid(mac_ssid[1].encode('utf-8')))
            self.write("wpa_cli enable_network %s" % ind_conn)
            #TODO TIMEOUT
            while self.network_parameter("wpa_state") != "COMPLETED":
                if not self.connection_event.is_set():
                    raise Exception("Time is out. Disconnect...")
            if (self.network_parameter("ssid") != mac_ssid[1].encode('utf-8')):
                raise Exception("Unable to connect %s. Disconnect..." % mac_ssid[1].encode('utf-8'))
            if callback is not None:
                callback(socketio, True)
            self.connection_timer.cancel()
            return True
        
        except (ValueError, Exception), e:
            self.disconnect()
            print e
            if callback is not None:
                callback(socketio, False)
            return False


    def stop_connection_thread(self):
        self.connection_event.clear()
        self.connection_thread.join()
        self.connection_thread = None

    def remove_network(self, ssid):
        tuple_network = self.find_tuple_ssid(ssid.encode('utf-8'))
        if tuple_network is not None:
            index = self.network_list.index(tuple_network)
            self.network_list.pop(index)
            self.write("wpa_cli remove_network %s" % index)
            self.write("wpa_cli save_config")
            self.write("wpa_cli reconfigure")
            self.network_list = self.parse_wpa_conf_file()
        else:
            print "No such network"

    def try_find_current_network(self):
        network_list = self.show_network_list()
        for network in network_list:
            if network.split('\t')[-1].find('CURRENT') != -1:
                return network.split('\t')[0]
        return None

    def find_tuple_ssid(self, ssid):
        for network in self.network_list:
            if network[1].strip('\"') == ssid:
                return network
        return None

    def network_parameter(self, parameter):
        network_status = self.write("wpa_cli status").split("\n")[1:-1]
        for network_params in network_status:
            try:
                network_params.split('=').index(parameter)
                return network_params.split('=')[1]
            except ValueError:
                pass
        print "No such value in status list"
        return None

if __name__ == '__main__':
    a = ReachWiFi()

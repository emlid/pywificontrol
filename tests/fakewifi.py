import os
from configs import wificontrol, wpas, hotspot, wifi
from sysdmanager import SystemdManager

restart_mdns_cmd = "systemctl restart mdns.service && sleep 2"
rfkill_block_cmd = "rfkill block wifi"
rfkill_unblock_cmd = "rfkill unblock wifi"
start_wpa_cmd = "systemctl start wpa_supplicant.service && sleep 2"
stop_wpa_cmd = "systemctl stop wpa_supplicant.service && sleep 2"
start_host_cmd = "systemctl start hostapd.service && sleep 2"
stop_host_cmd = "systemctl stop hostapd.service && sleep 2"

def verify_cmd(input_cmd, cmd):
    if (input_cmd != cmd):
        raise wificontrol.WiFiControllError("Wrong: {}\nRigth: {}",(input_cmd, cmd))

class fakeWiFi(wifi.WiFi):

    def __init__(self, interface):
        super(fakeWiFi, self).__init__(interface)

    def restart_dns(self):
        verify_cmd(self.restart_mdns, restart_mdns_cmd)

    def block():
        verify_cmd(self.rfkill_wifi_control("block"), rfkill_block_cmd)

    def unblock():
        verify_cmd(self.rfkill_wifi_control("unblock"), rfkill_unblock_cmd)

    def get_device_ip(self):
        if (self.interface):
            return "0.0.0.0"
        else:
            raise wificontrol.WiFiControllError()

    def get_device_mac(self):
        if (self.interface):
            return "00:00:00:00:00:00"
        else:
            raise wificontrol.WiFiControllError()

class fakeWpaSupplicant(fakeWiFi, wpas.WpaSupplicant):

    def __init__(self, interface, 
        wpas_config="/etc/wpa_supplicant/wpa_supplicant.conf",
        p2p_config="/etc/wpa_supplicant/p2p_supplicant.conf"):

        fakeWiFi.__init__(self, interface)
        wpas.WpaSupplicant.__init__(self, interface, wpas_config, p2p_config)
        self.p2p_name = "reach"
        self.fake_started = self.sysdmanager.is_active("wpa_supplicant.service")
        self.started = lambda: self.fake_started
        
    def start(self):
        verify_cmd(self.wpas_control("start"), start_wpa_cmd)
        self.fake_started = True
        
    def stop(self):
        verify_cmd(self.wpas_control("stop"), stop_wpa_cmd)
        self.fake_started = False

    def get_status(self):
        network_params = dict()
        network_params['ssid'] = "FakeWiFi"
        network_params['mac address'] = self.get_device_mac()
        network_params['IP address'] = self.get_device_ip()
        return network_params

    def start_connecting(self, network, callback=None,
                         args=None, timeout=10):
        result = False
        if (network is None or
            network['ssid'] in ('EML33T2','EML33T5')):
            result = True
        self.callback_response(result, callback, args)

    def callback_response(self, result, callback, args):
        if callback is not None:
            if args is not None:
                callback(result, args)
            else:
                callback(result)

    # Names changung actions
    def set_p2p_name(self, name='reach'):
        if (os.path.exists(self.p2p_supplicant_path)):
            self.p2p_name = name
        else:
            raise wificontrol.WiFiControllError("No p2p_supplicant file!")


    def get_p2p_name(self):
        if (os.path.exists(self.p2p_supplicant_path)):
            return self.p2p_name
        else:
            raise wificontrol.WiFiControllError("No p2p_supplicant file!")
    
    # Connection actions
    def connect(self, network, callback, args):
        pass

    def start_network_connection(self, network):
        pass

    def wait_untill_connection_complete(self):
        pass
    
    def check_correct_connection(self, aim_network):
        pass

class fakeHostAP(fakeWiFi, hotspot.HostAP):

    def __init__(self, interface,
        hostapd_config="/etc/hostapd/hostapd.conf", 
        hostname_config='/etc/hostname'):
        
        super(fakeHostAP, self).__init__(interface)
        self.hostapd_path = hostapd_config
        self.hostname_path = hostname_config
        self.hostap_name = "reach:00:00"
        self.hostname = "reach"
        self.fake_started = self.sysdmanager.is_active("hostapd.service")
        self.started = lambda: self.fake_started

    def start(self):
        verify_cmd(self.hostapd_control("start"), start_host_cmd)
        self.fake_started = True

    def stop(self):
        verify_cmd(self.hostapd_control("stop"), stop_host_cmd)
        self.fake_started = False

    def set_hostap_name(self, name='reach'):
        if (os.path.exists(self.hostapd_path)):
            mac_addr = self.get_device_mac()[-6:]
            self.hostap_name = "{}{}".format(name, mac_addr)
        else:
            raise wificontrol.WiFiControllError("No hostap file!")

    def get_hostap_name(self):
        if (os.path.exists(self.hostapd_path)):
            return self.hostap_name
        else:
            raise wificontrol.WiFiControllError("No hostap file!")

    def set_hostap_password(self, password):
        if (os.path.exists(self.hostapd_path)):
            pass
        else:
            raise wificontrol.WiFiControllError("No hostap file!")

    def set_host_name(self, name='reach'):
        if (os.path.exists(self.hostname_path)):
            self.hostname = name
        else:
            raise wificontrol.WiFiControllError("No hostname file!")

    def get_host_name(self):
        if (os.path.exists(self.hostname_path)):
            return self.hostname
        else:
            raise wificontrol.WiFiControllError("No hostname file!")

class fakeWiFiControl(object):

    def __init__(self, interface='wlan0'):
        
        self.wifi = fakeWiFi(interface)
        self.wpas = fakeWpaSupplicant(interface)
        self.hotspot = fakeHostAP(interface)

    def start_host_mode(self):
        if not self.hotspot.started():
            self.wpas.stop()
            self.hotspot.start()

    def start_client_mode(self):
        if not self.wpas.started():
            self.hotspot.stop()
            self.wpas.start()

    def turn_on_wifi(self):
        self.wifi.unblock() 
        self.wpas.start()

    def turn_off_wifi(self):
        self.hotspot.stop()
        self.wpas.start()
        self.wifi.block()

    def get_wifi_turned_on(self):
        return (self.wpas.started() or self.hotspot.started())

    def set_hostap_password(self, password):
        self.hotspot.set_hostap_password(password)

    def get_device_name(self):
        return self.hotspot.get_host_name()

    def get_hostap_name(self):
        return self.hotspot.get_hostap_name()

    def set_device_names(self, name):
        self.wpas.set_p2p_name(name)
        self.hotspot.set_hostap_name(name)
        self.hotspot.set_host_name(name)
        self.wifi.restart_dns()

    def get_status(self):
        return (self.get_state(), self.wpas.get_status())

    def get_added_networks(self):
        return self.wpas.get_added_networks()

    def add_network(self, network_parameters):
        self.wpas.add_network(network_parameters)

    def remove_network(self, network):
        self.wpas.remove_network(network)

    def start_connecting(self, network, callback=None, args=None, timeout=10):
        if callback is None:
            callback = self.revert_on_connect_failure
            args = None
        self.start_client_mode()
        self.wpas.start_connecting(network, callback, args, timeout)

    def stop_connecting(self):
        self.wpas.stop_connecting()

    def disconnect(self):
        self.wpas.disconnect()

    def get_state(self):
        if self.wpas.started():
            return "wpa_supplicant"
        if self.hotspot.started():
            return "hostapd"
        return "wifi_off"

    def revert_on_connect_failure(self, result):
        if not result:
            self.start_host_mode() 

if __name__ == '__main__':
    wf = fakeWpaSupplicant('wlp6s0')
    print(wf.get_status())

import dbus

class ServiceError(Exception):
    pass

class InterfaceError(Exception):
    pass

class PropertyError(Exception):
    pass

class WpaTemplates(object):
    def __init__(self, network_dict):

        self.security = network_dict.get('security')
        self.name = network_dict.get('ssid').encode('utf-8')
        self.password = network_dict.get('password').encode('utf-8')
        self.identity = network_dict.get('identity').encode('utf-8')

    def __iter__(self):
        if (self.security == 'open'):
            yield "ssid", "{}".format(self.name)
            yield "key_mgmt", "NONE"
        elif (self.security == 'wep'):
            yield "ssid", "{}".format(self.name)
            yield "key_mgmt", "NONE"
            yield "group", "WEP104 WEP40"
            yield "wep_key0", "{}".format(self.password)
        elif (self.security == 'wpapsk'):
            yield "ssid", "{}".format(self.name)
            yield "key_mgmt", "WPA-PSK"
            yield "pairwise", "CCMP TKIP"
            yield "group", "CCMP TKIP"
            yield "eap", "TTLS PEAP TLS"
            yield "psk", "{}".format(self.password)
        elif (self.security == 'wpa2psk'):
            yield "ssid", "{}".format(self.name)
            yield "proto", "RSN"
            yield "key_mgmt", "WPA-PSK"
            yield "pairwise", "CCMP TKIP"
            yield "group", "CCMP TKIP"
            yield "eap", "TTLS PEAP TLS"
            yield "psk", "{}".format(self.password)
        elif (self.security == 'wpaeap'):
            yield "ssid", "{}".format(self.name)
            yield "key_mgmt", "WPA-EAP"
            yield "pairwise", "CCMP TKIP"
            yield "group", "CCMP TKIP"
            yield "eap", "TTLS PEAP TLS"
            yield "identity", "{}".format(self.identity)
            yield "password", "{}".format(self.password)
            yield "phase1", "peaplable=0"
        else:
            yield "ssid", "{}".format(self.name)
            yield "psk", "{}".format(self.password)

class WpaSupplicantDBus(object):

    _BASE_NAME = "fi.w1.wpa_supplicant1"
    _BASE_PATH = "/fi/w1/wpa_supplicant1"

    def __init__(self):
        self._bus = dbus.SystemBus()

    def __get_interface(self):
        try:
            obj = self._bus.get_object(self._BASE_NAME, self._BASE_PATH)
            return dbus.Interface(obj, self._BASE_NAME)
        except dbus.exceptions.DBusException as error:
            raise ServiceError(error)

    def __get_properties(self):
        try:
            obj = self._bus.get_object(self._BASE_NAME, self._BASE_PATH)
            properties_interface = dbus.Interface(obj, dbus.PROPERTIES_IFACE)
            return properties_interface.GetAll(self._BASE_NAME)
        except dbus.exceptions.DBusException as error:
            raise ServiceError(error)

    def showWpaSupplicantProperties(self):
        return self.__get_properties()

    def getInterface(self, interface):
        wpa_interface = self.__get_interface()
        try:
            return wpa_interface.GetInterface(interface)
        except dbus.exceptions.DBusException as error:
            raise InterfaceError(error)

class WpaSupplicantInterface(WpaSupplicantDBus):

    _INTERFACE_NAME = "fi.w1.wpa_supplicant1.Interface"

    def __init__(self, interface):

        super(WpaSupplicantInterface, self).__init__()
        self.interface = interface

    def initialize(self):
        self._interface_path = self.getInterface(self.interface)

    def __get_interface(self):
        try:
            obj = self._bus.get_object(self._BASE_NAME, self._interface_path)
            return dbus.Interface(obj, self._INTERFACE_NAME)
        except dbus.exceptions.DBusException as error:
            raise InterfaceError(error)

    def __get_property(self, property_name):
        try:
            obj = self._bus.get_object(self._BASE_NAME, self._interface_path)
            properties_interface = dbus.Interface(obj, dbus.PROPERTIES_IFACE)
            return properties_interface.Get(self._INTERFACE_NAME, property_name)
        except dbus.exceptions.DBusException as error:
            raise PropertyError(error)

    def __set_property(self, property_name, property_value):
        try:
            obj = self._bus.get_object(self._BASE_NAME, self._interface_path)
            properties_interface = dbus.Interface(obj, dbus.PROPERTIES_IFACE)
            properties_interface.Set(self._INTERFACE_NAME, property_name, property_value)
        except dbus.exceptions.DBusException as error:
            raise PropertyError(error)

    def scan(self):
        interface = self.__get_interface()
        try:
            return interface.Scan(dbus.Dictionary({"Type": "passive"}, 'sv'))
        except dbus.exceptions.DBusException as error:
            raise ServiceError(error)

    def addNetwork(self, network):
        interface = self.__get_interface()
        try:
            return interface.AddNetwork(dbus.Dictionary(network, 'sv'))
        except dbus.exceptions.DBusException as error:
            raise ServiceError(error)

    def removeNetwork(self, network_path):
        interface = self.__get_interface()
        try:
            interface.RemoveNetwork(network_path)
        except dbus.exceptions.DBusException as error:
            raise ServiceError(error)

    def removeAllNetworks(self):
        interface = self.__get_interface()
        try:
            interface.RemoveAllNetworks()
        except dbus.exceptions.DBusException as error:
            raise ServiceError(error)

    def selectNetwork(self, network_path):
        interface = self.__get_interface()
        try:
            interface.SelectNetwork(network_path)
        except dbus.exceptions.DBusException as error:
            raise ServiceError(error)

    def networkReply(self, network_path, parameter, value):
        interface = self.__get_interface()
        try:
            interface.NetworkReply(network_path, parameter, value)
        except dbus.exceptions.DBusException as error:
            raise ServiceError(error)

    def signalPoll(self):
        interface = self.__get_interface()
        try:
            return interface.SignalPoll()
        except dbus.exceptions.DBusException as error:
            raise ServiceError(error)

    def reassociate(self):
        interface = self.__get_interface()
        try:
            interface.Reassociate()
        except dbus.exceptions.DBusException as error:
            if ("fi.w1.wpa_supplicant1.NotConnected" in str(error)):
                pass
            else:
                raise ServiceError(error)
        
    def reconnect(self):
        interface = self.__get_interface()
        try:
            interface.Reconnect()
        except dbus.exceptions.DBusException as error:
            raise ServiceError(error)

    def disconnect(self):
        interface = self.__get_interface()
        try:
            interface.Disconnect()
        except dbus.exceptions.DBusException as error:
            raise ServiceError(error)

    def getState(self):
        return self.__get_property("State")

    def getInterfaceName(self):
        return self.__get_property("Ifname")

    def getScanning(self):
        return self.__get_property("Scanning")

    def getApScan(self):
        return self.__get_property("ApScan")

    def setApScan(self, value):
        return self.__set_property("ApScan", dbus.UInt32(value))

    def getCurrentNetwork(self):
        return self.__get_property("CurrentNetwork")

    def getNetworks(self):
        return self.__get_property("Networks")

    def getDisconnectReason(self):
        return self.__get_property("DisconnectReason")

class WpaSupplicantNetwork(WpaSupplicantDBus):

    _NETWORK_NAME = "fi.w1.wpa_supplicant1.Network"

    def __init__(self):
        super(WpaSupplicantNetwork, self).__init__()

    def __get_properties(self, network_path):
        try:
            obj = self._bus.get_object(self._BASE_NAME, network_path)
            properties_interface = dbus.Interface(obj, dbus.PROPERTIES_IFACE)
            return properties_interface.GetAll(self._NETWORK_NAME)
        except dbus.exceptions.DBusException as error:
            raise PropertyError(error)

    def networkEnable(self, network_path):
        return self.__get_properties(network_path)['Enable']

    def networkProperties(self, network_path):
        return self.__get_properties(network_path)['Properties']

    def getNetworkSSID(self, network_path):
        ssid = self.networkProperties(network_path)['ssid']
        try:
            return str(ssid.decode('hex')).strip("\"")
        except TypeError:
            return str(ssid).strip("\"")

if __name__ == '__main__':
    wifi = WpaSupplicantInterface('wlp6s0')
    wifi.initialize()
    network_manager = WpaSupplicantNetwork()
    network_path = wifi.getCurrentNetwork()
    wifi.setApScan("0")
    new_network={"ssid": "myssid", "psk": "mypassword"}
    print(network_manager.networkProperties(network_path)['ssid'])

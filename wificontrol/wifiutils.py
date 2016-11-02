import dbus

class NoInterfaceException(Exception):
    pass

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
            print(error)
            return None

    def __get_properties(self):
        try:
            obj = self._bus.get_object(self._BASE_NAME, self._BASE_PATH)
            properties_interface = dbus.Interface(obj, dbus.PROPERTIES_IFACE)
            return properties_interface.GetAll(self._BASE_NAME)
        except dbus.exceptions.DBusException as error:
            print(error)
            return None

    def showWpaSupplicantProperties(self):
        return self.__get_properties()

    def getInterface(self, interface):
        wpa_interface = self.__get_interface()
        if wpa_interface is None:
            return False
        try:
            return wpa_interface.GetInterface(interface)
        except dbus.exceptions.DBusException as error:
            print(error)
            return None

class WpaSupplicantInterface(WpaSupplicantDBus):

    _INTERFACE_NAME = "fi.w1.wpa_supplicant1.Interface"
    _PROPERTIES = {
        "readable": ["State", "Scanning", "ApScan", "Ifname", 
                     "Driver", "CurrentNetwork", "Networks", 
                     "ScanInterval", "DisconnectReason"],
        "writable": ["ApScan", "ScanInterval", "DisconnectReason"]
    }

    def __init__(self, interface):

        super(WpaSupplicantInterface, self).__init__()
        self._interface_path = self.getInterface(interface)
        if self._interface_path is None:
            raise NoInterfaceException("No such interface")

    def __get_interface(self):
        try:
            obj = self._bus.get_object(self._BASE_NAME, self._interface_path)
            return dbus.Interface(obj, self._INTERFACE_NAME)
        except dbus.exceptions.DBusException as error:
            print(error)
            return None

    def __get_property(self, property_name):
        try:
            obj = self._bus.get_object(self._BASE_NAME, self._interface_path)
            properties_interface = dbus.Interface(obj, dbus.PROPERTIES_IFACE)
            return properties_interface.Get(self._INTERFACE_NAME, property_name)
        except dbus.exceptions.DBusException as error:
            print(error)
            return None

    def addNetwork(self, network):
        interface = self.__get_interface()

        if interface is None:
            return False
        try:
            return interface.AddNetwork(network)
        except dbus.exceptions.DBusException as error:
            print(error)
            return None

    def removeNetwork(self, network_path):
        interface = self.__get_interface()

        if interface is None:
            return False

        try:
            interface.RemoveNetwork(network_path)
            return True
        except dbus.exceptions.DBusException as error:
            print(error)
            return False

    def removeAllNetworks(self):
        interface = self.__get_interface()

        if interface is None:
            return False

        try:
            interface.RemoveAllNetworks()
            return True
        except dbus.exceptions.DBusException as error:
            print(error)
            return False

    def selectNetwork(self, network_path):
        interface = self.__get_interface()

        if interface is None:
            return False

        try:
            interface.SelectNetwork(network_path)
            return True
        except dbus.exceptions.DBusException as error:
            print(error)
            return False

    def networkReply(self, network_path, parameter, value):
        interface = self.__get_interface()

        if interface is None:
            return False

        try:
            interface.NetworkReply(network_path, parameter, value)
            return True
        except dbus.exceptions.DBusException as error:
            print(error)
            return False

    def signalPoll(self):
        interface = self.__get_interface()

        if interface is None:
            return False

        try:
            return interface.SignalPoll()
        except dbus.exceptions.DBusException as error:
            print(error)
            return None

    def reconnect(self):
        interface = self.__get_interface()

        if interface is None:
            return False

        try:
            interface.Reconnect()
            return True
        except dbus.exceptions.DBusException as error:
            print(error)
            return False

    def disconnect(self):
        interface = self.__get_interface()

        if interface is None:
            return False

        try:
            interface.Disconnect()
            return True
        except dbus.exceptions.DBusException as error:
            print(error)
            return False
    def getAvailableProperties(self):
        return self._PROPERTIES

    def getProperty(self, proterty):
        return self.__get_property(proterty)

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
            print(error)
            return None

    def networkEnable(self, network_path):
        return self.__get_properties(network_path)['Enable']

    def networkProperties(self, network_path):
        return self.__get_properties(network_path)['Properties']

# class WifiManager(WpaSupplicantInterface, WpaSupplicantNetwork):

#     def __init__(self, interface):
#         super(WifiManager, self).__init__(interface)
    
if __name__ == '__main__':

    wifi = WpaSupplicantInterface('wlp6s0')
    network_manager = WpaSupplicantNetwork()
    network_path = wifi.getProperty("CurrentNetwork")
    # print network_manager.networkProperties(network_path)['ssid']
    # wifi.removeAllNetworks()
    # nw = wifi.addNetwork({'ssid': 'EML33T5', 'psk': 'emrooftop'})
    # for k, w in network_manager.networkProperties(nw).items():
    #     print k, ':', w
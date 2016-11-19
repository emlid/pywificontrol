import dbus

class ServiceError(Exception):
    pass

class InterfaceError(Exception):
    pass

class PropertyError(Exception):
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

    def getNetworks(self):
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

if __name__ == '__main__':
    wifi = WpaSupplicantInterface('wlp6s0')
    wifi.initialize()
    network_manager = WpaSupplicantNetwork()
    network_path = wifi.getCurrentNetwork()
    wifi.setApScan("0")
    new_network={"ssid": "myssid", "psk": "mypassword"}
    print(network_manager.networkProperties(network_path)['ssid'])

import dbus

class NoInterfaceException(Exception):
    pass

class WpaSupplicantDBus(object):
    BASE_NAME = "fi.w1.wpa_supplicant1"
    BASE_PATH = "/fi/w1/wpa_supplicant1"
    def __init__(self, interface):
        self.__bus = dbus.SystemBus()

    def _get_interface(self):
        try:
            obj = self.__bus.get_object("fi.w1.wpa_supplicant1",
                "/fi/w1/wpa_supplicant1")
            return dbus.Interface(obj, "fi.w1.wpa_supplicant1")
        except dbus.exceptions.DBusException as error:
            print(error)
            return None

    def get_interface_path(self, interface):
        wpa_interface = self._get_interface()
        if wpa_interface is None:
            return False
        try:
            return wpa_interface.GetInterface(interface)
        except dbus.exceptions.DBusException as error:
            print(error)
            return None

class WpaSupplicantInterface(object):
    def __init__(self, interface):
        self.__bus = dbus.SystemBus()
        self._interface_path = WpaSupplicantDBus.get_interface_path(interface)
        if self._interface_path is None:
            raise NoInterfaceException("No such interface")

    def _get_interface(self):
        try:
            obj = self.__bus.get_object("fi.w1.wpa_supplicant1",
                                        self._interface_path)

            return dbus.Interface(obj,
                "fi.w1.wpa_supplicant1.Interface")
        except dbus.exceptions.DBusException as error:
            print(error)
            return None

    def _get_property(self, property_name):
        try:
            obj = self.__bus.get_object("fi.w1.wpa_supplicant1",
                                        self._interface_path)

            properties_interface = dbus.Interface(
                obj, dbus.PROPERTIES_IFACE)

            return properties_interface.Get(
                "fi.w1.wpa_supplicant1.Interface", property_name)

        except dbus.exceptions.DBusException as error:
            print(error)
            return None

class WpaSupplicantNetwork(object):
    def __init__(self):
        pass

class WifiManager(object):

    def __init__(self, interface):
        self.__bus = dbus.SystemBus()
        self._interface_path = self._get_interface_path(interface)
        if self._interface_path is None:
            raise NoInterfaceException("No such interface")

    def _get_interface_path(self, interface):
        try:
            obj = self.__bus.get_object("fi.w1.wpa_supplicant1",
                "/fi/w1/wpa_supplicant1")
            wpa_interface = dbus.Interface(obj, "fi.w1.wpa_supplicant1")
            return wpa_interface.GetInterface(interface)
        except dbus.exceptions.DBusException as error:
            print(error)
            return None
    
    def _get_interface(self):
        try:
            obj = self.__bus.get_object("fi.w1.wpa_supplicant1",
                                        self._interface_path)

            return dbus.Interface(obj,
                "fi.w1.wpa_supplicant1.Interface")
        except dbus.exceptions.DBusException as error:
            print(error)
            return None

    def _get_property(self):
        try:
            obj = self.__bus.get_object("fi.w1.wpa_supplicant1",
                                        "/fi/w1/wpa_supplicant1/Interfaces/1")

            properties_interface = dbus.Interface(
                obj, dbus.PROPERTIES_IFACE)

            return properties_interface.Get(
                "fi.w1.wpa_supplicant1.Interface", "Ifname")

        except dbus.exceptions.DBusException as error:
            print(error)
            return None

    def scan(self):
        interface = self._get_interface()

        if interface is None:
            return False

        try:
            interface.Scan({"Type": "active"})
            return True
        except dbus.exceptions.DBusException as error:
            print(error)
            return False

    def smth(self):

        prop = self._get_property()

        if prop is None:
            return False

        try:
            print prop # .encode('utf-8')
            return True
        except dbus.exceptions.DBusException as error:
            print(error)
            return False   

    def add_network(self, network):
        interface = self._get_interface()

        if interface is None:
            return False

        try:
            return interface.AddNetwork(network)
        except dbus.exceptions.DBusException as error:
            print(error)
            return None

    def remove_network(self, network):
        interface = self._get_interface()

        if interface is None:
            return False

        try:
            interface.RemoveNetwork(network)
            return True
        except dbus.exceptions.DBusException as error:
            print(error)
            return False

if __name__ == '__main__':
    wifi = WifiManager('wlp6s0')
    # wifi.scan()
    wifi.smth()
    # wifi.scan()
    # nw_path = wifi.add_network({'ssid': 'EML33T5', 'psk': 'emrooftop'})
    # wifi.remove_network(nw_path)

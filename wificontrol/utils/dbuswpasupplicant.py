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

    def show_wpa_supplicant_properties(self):
        return self.__get_properties()

    def get_interface(self, interface):
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
        self._interface_path = self.get_interface(self.interface)

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

    def add_network(self, network):
        interface = self.__get_interface()
        try:
            return interface.AddNetwork(dbus.Dictionary(network, 'sv'))
        except dbus.exceptions.DBusException as error:
            raise ServiceError(error)

    def remove_network(self, network_path):
        interface = self.__get_interface()
        try:
            interface.RemoveNetwork(network_path)
        except dbus.exceptions.DBusException as error:
            raise ServiceError(error)

    def remove_all_networks(self):
        interface = self.__get_interface()
        try:
            interface.RemoveAllNetworks()
        except dbus.exceptions.DBusException as error:
            raise ServiceError(error)

    def select_network(self, network_path):
        interface = self.__get_interface()
        try:
            interface.SelectNetwork(network_path)
        except dbus.exceptions.DBusException as error:
            raise ServiceError(error)

    def network_reply(self, network_path, parameter, value):
        interface = self.__get_interface()
        try:
            interface.NetworkReply(network_path, parameter, value)
        except dbus.exceptions.DBusException as error:
            raise ServiceError(error)

    def signal_poll(self):
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

    def get_state(self):
        return self.__get_property("State")

    def get_interface_name(self):
        return self.__get_property("Ifname")

    def get_scanning(self):
        return self.__get_property("Scanning")

    def get_ap_scan(self):
        return self.__get_property("ApScan")

    def set_ap_scan(self, value):
        return self.__set_property("ApScan", dbus.UInt32(value))

    def get_current_network(self):
        return self.__get_property("CurrentNetwork")

    def get_networks(self):
        return self.__get_property("Networks")

    def get_disconnect_reason(self):
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

    def network_enable(self, network_path):
        return self.__get_properties(network_path)['Enable']

    def network_properties(self, network_path):
        return self.__get_properties(network_path)['Properties']

    def get_network_SSID(self, network_path):
        ssid = self.network_properties(network_path)['ssid']
        try:
            return str(ssid.decode('hex')).strip("\"")
        except TypeError:
            return str(ssid).strip("\"")

if __name__ == '__main__':
    wifi = WpaSupplicantInterface('wlp6s0')
    wifi.initialize()
    network_manager = WpaSupplicantNetwork()
    # network_path = wifi.get_current_network()
    # wifi.set_ap_scan("0")
    # new_network={"ssid": "myssid", "psk": "mypassword"}
    print(network_manager.network_properties(network_path)['ssid'])

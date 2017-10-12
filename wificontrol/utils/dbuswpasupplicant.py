# Written by Ivan Sapozhkov and Denis Chagin <denis.chagin@emlid.com>
#
# Copyright (c) 2016, Emlid Limited
# All rights reserved.
#
# Redistribution and use in source and binary forms,
# with or without modification,
# are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software
# without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


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

    def __get_property(self, property_name):
        try:
            obj = self._bus.get_object(self._BASE_NAME, self._BASE_PATH)
            properties_interface = dbus.Interface(obj, dbus.PROPERTIES_IFACE)
            return properties_interface.Get(self._BASE_NAME, property_name)
        except dbus.exceptions.DBusException as error:
            raise PropertyError(error)

    def __set_property(self, property_name, property_value):
        try:
            obj = self._bus.get_object(self._BASE_NAME, self._BASE_PATH)
            properties_interface = dbus.Interface(obj, dbus.PROPERTIES_IFACE)
            properties_interface.Set(self._BASE_NAME, property_name, property_value)
        except dbus.exceptions.DBusException as error:
            raise PropertyError(error)

    def get_interface(self, interface):
        wpa_interface = self.__get_interface()
        try:
            return wpa_interface.GetInterface(interface)
        except dbus.exceptions.DBusException as error:
            raise InterfaceError(error)

    def create_interface(self, interface, bridge_interface=None,
                         driver=None, config_file=None):
        try:
            wpa_interface = self.__get_interface()
        except dbus.exceptions.DBusException as error:
            raise ServiceError(error)
        else:
            args = {"Ifname": interface}
            if bridge_interface is not None:
                args["BridgeIfname"] = bridge_interface
            if driver is not None:
                args["Driver"] = driver
            if config_file is not None:
                args["ConfigFile"] = config_file
            try:
                return wpa_interface.CreateInterface(dbus.Dictionary(args, 'sv'))
            except dbus.exceptions.DBusException as error:
                raise InterfaceError(error)

    def remove_interface(self, iface_path):
        try:
            wpa_interface = self.__get_interface()
        except dbus.exceptions.DBusException as error:
            raise ServiceError(error)
        else:
            try:
                return wpa_interface.RemoveInterface(iface_path)
            except dbus.exceptions.DBusException as error:
                raise InterfaceError(error)

    def get_debug_level(self):
        return self.__get_property(dbus.String("DebugLevel"))

    def set_debug_level(self, parameter):
        self.__set_property(dbus.String("DebugLevel"), dbus.String(parameter))

    def get_debug_timestamp(self):
        return self.__get_property(dbus.String("DebugTimestamp"))

    def set_debug_level(self, parameter):
        self.__set_property(dbus.String("DebugTimestamp"), dbus.Boolean(parameter))

    def get_debug_show_keys(self):
        return self.__get_property(dbus.String("DebugShowKeys"))

    def set_debug_show_keys(self, parameter):
        self.__set_property(dbus.String("DebugShowKeys"), dbus.Boolean(parameter))

    def get_interfaces(self):
        return self.__get_property(dbus.String("Interfaces"))

    def get_EAP_methods(self):
        return self.__get_property(dbus.String("EapMethods"))

    def get_capabilities(self):
        return self.__get_property(dbus.String("Capabilities"))

    def get_WFDIEs(self):
        return self.__get_property(dbus.String("WFDIEs"))

    def set_WFDIEs(self, parameter):
        self.__set_property(dbus.String("WFDIEs"), dbus.Array(parameter, "y"))

    def show_wpa_supplicant_properties(self):
        return self.__get_properties()


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

    def get_current_BSS(self):
        return self.__get_property("CurrentBSS")

    def get_BSSs(self):
        return self.__get_property("BSSs")

    def get_interface_name(self):
        return self.__get_property("Ifname")

    def get_scanning(self):
        return self.__get_property("Scanning")

    def get_ap_scan(self):
        return self.__get_property("ApScan")

    def set_ap_scan(self, value):
        return self.__set_property("ApScan", dbus.UInt32(value))

    def get_scan_interval(self):
        return self.__get_property("ScanInterval")

    def set_scan_interval(self, value):
        return self.__set_property("ScanInterval", dbus.Int32(value))

    def get_current_network(self):
        return self.__get_property("CurrentNetwork")

    def get_networks(self):
        return self.__get_property("Networks")

    def get_disconnect_reason(self):
        return self.__get_property("DisconnectReason")


class WpaSupplicantBSS(WpaSupplicantDBus):
    _BSS_NAME = "fi.w1.wpa_supplicant1.BSS"

    def __init__(self):
        super(WpaSupplicantBSS, self).__init__()

    def __get_property(self, bss_path, property_name):
        try:
            obj = self._bus.get_object(self._BASE_NAME, bss_path)
            properties_interface = dbus.Interface(obj, dbus.PROPERTIES_IFACE)
            return properties_interface.Get(self._BSS_NAME, property_name)
        except dbus.exceptions.DBusException as error:
            raise PropertyError(error)

    def __set_property(self, bss_path, property_name, property_value):
        try:
            obj = self._bus.get_object(self._BASE_NAME, bss_path)
            properties_interface = dbus.Interface(obj, dbus.PROPERTIES_IFACE)
            properties_interface.Set(self._BSS_NAME, property_name, property_value)
        except dbus.exceptions.DBusException as error:
            raise PropertyError(error)

    def get_SSID(self, bss_path):
        name_array = self.__get_property(bss_path, "SSID")
        try:
            ssid = "".join([str(letter) for letter in name_array])
        except UnicodeDecodeError:
            ssid = "".join([hex(letter)[2:].zfill(2) for letter in name_array])
            ssid = str(ssid.decode('hex'))
        return ssid

    def get_BSSID(self, bss_path):
        mac_array = self.__get_property(bss_path, "BSSID")
        bssid = ":".join([hex(byte)[2:].zfill(2) for byte in mac_array])
        return bssid

    def get_WPA(self, bss_path):
        return self.__get_property(bss_path, "WPA")

    def get_RSN(self, bss_path):
        return self.__get_property(bss_path, "RSN")

    def get_WPS(self, bss_path):
        return self.__get_property(bss_path, "WPS")

    def get_mode(self, bss_path):
        return str(self.__get_property(bss_path, "Mode"))

    def get_frequency(self, bss_path):
        return int(self.__get_property(bss_path, "Frequency"))

    def get_signal(self, bss_path):
        return int(self.__get_property(bss_path, "Signal"))


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
    bss_manager = WpaSupplicantBSS()
    network_manager = WpaSupplicantNetwork()

    cur_net = wifi.get_current_network()
    print(network_manager.get_network_SSID(cur_net))

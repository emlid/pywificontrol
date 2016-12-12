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

class WpasNetworkConverter(object):
    def __init__(self, network_dict):

        self.security = network_dict.get('security')
        self.name = network_dict.get('ssid', '').encode('utf-8')
        self.password = network_dict.get('password', '').encode('utf-8')
        self.identity = network_dict.get('identity', '').encode('utf-8')

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

class WifiControlNetworkConverter(object):
    def __init__(self, network_dict):

        self.name = network_dict.get('ssid')
        self.key_mgmt = network_dict.get('key_mgmt')
        self.proto = network_dict.get('proto')
        self.group = network_dict.get('group')

    def __iter__(self):
        if (self.key_mgmt == 'NONE'):
            if not self.group:
                yield "ssid", self.name
                yield "security", "Open"
            else:
                yield "ssid", self.name
                yield "security", "WEP"

        elif (self.key_mgmt == 'WPA-PSK'):
            if not self.proto:
                yield "ssid", self.name
                yield "security", "WPA-PSK"
            else:
                yield "ssid", self.name
                yield "security", "WPA2-PSK"

        elif (self.key_mgmt == 'WPA-EAP'):
            yield "ssid", self.name
            yield "security", "WPA-EAP"

        else:
            yield "ssid", self.name
            yield "security", "NONE"
        yield "connected", False

def ConvertToWpasNetwork(network):
    return dict(WpasNetworkConverter(network))

def ConvertToWifiControlNetwork(network, current_network):
    wifinetwork = dict(WifiControlNetworkConverter(network))
    try:
        if wifinetwork['ssid'] == current_network['ssid']:
            wifinetwork.update(current_network)
            wifinetwork["connected"] = True
    except TypeError:
        pass
    finally:
        return wifinetwork

if __name__ == '__main__':
    network = {'ssid': "MySSID", 'password': "NewPassword", 'security': "wpaeap", 'identity': "alex@example.com"}
    conv = ConvertToWpasNetwork(network)
    reconv = ConvertToWifiControlNetwork(conv)
    print(conv, reconv)

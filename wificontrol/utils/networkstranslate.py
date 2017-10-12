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


def create_security(proto, key_mgmt, group):
    if not proto:
        return 'open'
    if not key_mgmt:
        if "wep" in group:
            return 'wep'
        else:
            return None
    else:
        if "wpa-psk" in key_mgmt:
            if proto == "WPA":
                return "wpapsk"
            elif proto == "RSN":
                return "wpa2psk"
            else:
                return None
        elif "wpa-eap" in key_mgmt:
            return 'wpaeap'
        else:
            return None


def convert_to_wpas_network(network):
    return dict(WpasNetworkConverter(network))


def convert_to_wificontrol_network(network, current_network):
    wifinetwork = dict(WifiControlNetworkConverter(network))
    try:
        if wifinetwork['ssid'] == current_network['ssid']:
            wifinetwork.update(current_network)
            wifinetwork["connected"] = True
    except TypeError:
        pass
    finally:
        return wifinetwork


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


if __name__ == '__main__':
    network = {'ssid': "MySSID", 'password': "NewPassword", 'security': "wpaeap", 'identity': "alex@example.com"}
    conv = convert_to_wpas_network(network)
    reconv = convert_to_wificontrol_network(conv)
    print(conv, reconv)

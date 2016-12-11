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

def ConvertToWpasNetwork(network):
    return dict(WpasNetworkConverter(network))

def ConvertToWifiControlNetwork(network):
    return dict(WifiControlNetworkConverter(network))

if __name__ == '__main__':
    network = {'ssid': "MySSID", 'password': "NewPassword", 'security': "wpaeap", 'identity': "alex@example.com"}
    conv = ConvertToWpasNetwork(network)
    reconv = ConvertToWifiControlNetwork(conv)
    print(conv, reconv)

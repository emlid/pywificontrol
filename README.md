# WiFiControl

Wificontrol is a module for management wireless networks.
That module provide two modes of wireless interface:

	1. Like AccessPoint in host mode.

	2. Like Client in client mode.

This module works only in root mode

# WiFiControl API
 - ReachWiFi() - constructor
 - start_host_mode() - run WiFi interface as wireless AP mode
 - start_client_mode() - run WiFi interface as client mode
 - scan() - start scan available networks
 - scan_result() - return scan results. Return value: list[(bssid, ssid)]
 - add_network(tuple(bssid, ssid, passkey)) - add network to the network_list
 - remove_network(tuple(bssid, ssid)) - remove network
 - connect(tuple(bssid, ssid), socketio, callback, timeout) - connect to network in network_list
 - disconnect() - disconnect from currend network
 - delta_added_scan() - return list of available networks without already added
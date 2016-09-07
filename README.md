# WiFiControl

Wificontrol is a module for management of wireless networks.
That module provide two modes of wireless interface:
1. Like AccessPoint in host mode.
2. Like Client on client mode.

# WiFiControl API
 - ReachWiFi() - constructor
 - start_host_mode() - run WiFi interface as wireless AP mode
 - start_client_mode() - run WiFi interface as client mode
 - scan() - start scan available networks
 - scan_result() - return scan results
 - add_network(args) - add network to the network_list. Args - tuple(bssid, ssid, passkey)
 - remove_network(args) - remove network. Args - tuple(bssid, ssid)
 - connect(args, socketio, callback, timeout) - connect to network in network_list. Args - tuple(bssid, ssid)
 - disconnect() - disconnect from currend network
 - delta_added_scan() - return list of available networks without already added. 
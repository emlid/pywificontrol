# WiFiControl

**Wificontrol** is a module for management wireless networks.
That module provide two modes of wireless interface:

 1. Like AccessPoint in host mode.

 2. Like Client in client mode.

Functions of module based on two packages: *hostapd* (AP-mode) and *wpa_supplicant* (Client-mode).  
For successful using intall it:
```bash
sudo apt-get update
sudo apt-get install hostapd
sudo apt-get install wpa_supplicant
```
This module works only in root mode

# Install

`make install`

# WiFiControl API

 - `ReachWiFi()` - constructor.

 
 - `start_host_mode()` - run WiFi interface as wireless AP mode
 - `start_client_mode()` - run WiFi interface as client mode
 - `set_hostap_name(newName)` - change name of your Access Point in AP mode
 - `get_hostap_name()` - return name of your Access Point in AP mode
 - `set_p2p_name(newName)` - change name of your devise for local access in Client mode
 - `get_p2p_name` - retirn name of your devise for local access in Client mode

 
 - `start_scanning()` - start scan available networks.
 - `get_scan_results()` - return scan results. Return value: `list[{'mac address':bssid,'ssid':ssid}]`
 - `get_added_networks()` - return list of added networks. Return value: `list[{'mac address':bssid, 'ssid':ssid}]`
 - `get_unknown_networks()` - return list of available networks without already added. Return value: `list[{'mac address':bssid, 'ssid':ssid}]`


 - `add_network(dict{'mac address':bssid, 'ssid':ssid, 'password':psk})` - add network to the network_list
 - `remove_network(dict{'mac address':bssid, 'ssid':ssid})` - remove network
 
 - `start_connecting(dict{'mac address':bssid, 'ssid':ssid}, callback = None, args = [], timeout = const)` - connect to network in network_list.  
  Connetion to network continue for a several seconds into a background Thread.  
  To notify user about connection ending uses callback functions.  
  Prototype of callback function is `foo(result, args)`.  
  There are some reasones for ending connection:
    * Successful connection
	* Timeout error
	* Retry of connection
	* User request of end connection
 - `stop_connecting()` - stop connection thread
 - `disconnect()` - disconnect from current network
 
#Exceptions

If you don't have hostapd or wpa_supplicant package, `__init__` function raise `OSError` exception. 


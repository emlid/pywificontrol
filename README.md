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
This package works only in root mode   
Wificontrol was tested on Intel Edison with Yocto image

# Install

`make install`

# WiFiControl API

 - `wificontrol()` - constructor.

 
 - `start_host_mode()` - run WiFi interface as wireless AP mode
 - `start_client_mode()` - run WiFi interface as client mode
 - `set_device_name(newName)` - change all names of your device
 - `get_device_name()` - return name of your device
 - `get_hostap_name()` - return name of your Access Point in AP mode
 - `get_status()` -  return tuple(mode, network_info). Network info is a dict('IP address', 'ssid', 'mac address') 

 
 - `get_added_networks()` - return list of added networks. Return value: `list[{'security': security, 'ssid': ssid}]`

 - `add_network(dict{'security': security, 'ssid': ssid, 'password': psk, 'identity': identity})` - add network to wpa_supplicant.conf file. Return value: `bool`   
**List of possible security protocols**:
    - 'open'
    - 'wep'
    - 'wpapsk'
    - 'wpa2psk'
    - 'wpaeap'   
For network with Open security protocol field 'password' has no effect.   
Network with WPA Enterprise security protocol has additional field 'identity'

 - `remove_network(dict{'ssid': ssid})` - remove network from wpa_supplicant.conf file. Return value: `bool`
 - `change_priority(list[dict{'ssid': ssid}) - change autoconnection priority of networks in wpa_supplicant.conf file
 
 - `start_connecting(dict{'ssid': ssid}, callback=None, args=None, timeout=const, any_network=False)` - connect to network from network_list in thread.  
  Connecting to network continue for a several seconds into a background Thread.  
  To notify user about ending of connection use callback functions.  
  Prototype of callback function is `foo(result, args)`.  
  If program can't connect to your network and you don't set any callback then you will be switched to host mode.  
  There are some reasons for ending of connection:
    * Successful connection
	* Timeout error
	* Retry of connection
	* User request of end connection
 - `stop_connecting()` - stop connection thread
 - `disconnect()` - disconnect from current network
 
#Exceptions

If you don't have hostapd or wpa_supplicant package, `__init__` function raise `OSError` exception. 


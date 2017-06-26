# WiFiControl

**Wificontrol** is a module for management wireless networks.
That module provide two modes of wireless interface:

 1. Like AccessPoint in host mode.
 2. Like Client in client mode.

Functions of module based on two packages: *hostapd* (AP-mode) and *wpa_supplicant* (Client-mode).  
WPA Supplicant operations use DBus w1.fi.wpa_supplicant1

For successful using intall it:
```bash
sudo apt-get update
sudo apt-get install hostapd
sudo apt-get install wpa_supplicant
```
This package works only in root mode   
Wificontrol was tested on Intel Edison with Yocto image

### Dependencies

`sysdmanager`
`netifaces`

The package was tested with **Python 2.7** and **Python 3.5**

### Install

`make install`

### Tests

`sudo make test`

### Usage

 - `WiFiControl(arguments)` - constructor. Arguments:
   - interface: WiFi interface. Default value: 'wlan0'
   - wpas_config: path to wpa_supplicant.conf file. Default value: '/etc/wpa_supplicant/wpa_supplicant.conf'
   - p2p_config: path to p2p_supplicant.conf file. Default value: '/etc/wpa_supplicant/p2p_supplicant.conf'
   - hostapd_config: path to hostapd.conf file. Default value: '/etc/hostapd/hostapd.conf'
   - hostname_config: path to hostname file. Default value: '/etc/hostname'
 
 - `start_host_mode()` - run WiFi interface as wireless AP mode
 - `start_client_mode()` - run WiFi interface as client mode
 - `set_device_names(newName)` - change your device name
 - `get_device_name()` - return name of your device
 - `get_hostap_name()` - return name of your Access Point in AP mode
 - `get_status()` - get WiFi status. return value: `tuple(mode, network_info)`. Network info is a `dict('IP address', 'ssid', 'mac address')`
 - `turn_on_wifi()` - turned on wifi through `rfkill block` command
 - `turn_off_wifi()` - turned on wifi through `rfkill unblock` command
 - `is_wifi_on()` - return value: `bool`

 - `scan()` - scan networks. Only for client mode
 - `get_scan_results()` - return list of available networks. Return value: `list[{'security': security, 'ssid': ssid, 'mac address': bssid}]`
 - `get_added_networks()` - return list of added networks. Return value: `list[{'security': security, 'ssid': ssid, 'connected': bool}]`
 - `add_network(dict{'security': security, 'ssid': ssid, 'password': psk, 'identity': identity})` - add new network.   
**List of possible security protocols**:
    - 'open'
    - 'wep'
    - 'wpapsk'
    - 'wpa2psk'
    - 'wpaeap'   
For network with Open security protocol field 'password' has no effect.   
Network with WPA Enterprise security protocol has additional field 'identity'

 - `remove_network(dict{'ssid': ssid})` - remove network from wpa_supplicant.conf file. Return value: `bool`
  
 - `start_connecting(network, callback=None, args=None, timeout=const)` - connect to network from network_list in thread.  
  Connecting to network continue for a several seconds into a background Thread.  
  To notify user about ending of connection use callback functions.  
  Prototype of callback function is `foo(result, args)`.  
  If program can't connect to your network and you don't set any callback then you will be switched to host mode.  
  For try connection to any known network set network=None
  There are some reasons for ending of connection:
    * Successful connection
  	* Timeout error
    * Retry of connection
    * User request of end connection
 - `stop_connecting()` - stop connection thread
 - `disconnect()` - disconnect from current network
 
### Exceptions

If you don't have hostapd or wpa_supplicant package, `__init__` function raise `OSError` exception.  
WiFiControl raise `WiFiControlError` exception on failure.


### WiFiMonitor 

Monitor module which processing WPA Supplicant and HostAPD D-Bus signals

#### Usage Example

```python
import signal
from reachstatus import StateClient
from wificontrol import WiFiMonitor


def main():
    def handler(signum, frame):
        wifi_monitor.shutdown()

    wifi_monitor = WiFiMonitor()

    wifi_monitor.register_callback(wifi_monitor.HOST_STATE, StateClient.set_network_host_state)
    wifi_monitor.register_callback(wifi_monitor.CLIENT_STATE, StateClient.set_network_client_state)
    wifi_monitor.register_callback(wifi_monitor.OFF_STATE, StateClient.set_network_disabled_state)
    wifi_monitor.register_callback(wifi_monitor.SCAN_STATE, StateClient.set_network_scan_state)
    wifi_monitor.register_callback(wifi_monitor.REVERT_EVENT, StateClient.send_revert_connect_notify)
    wifi_monitor.register_callback(wifi_monitor.SUCCESS_EVENT, StateClient.send_success_connect_notify)

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    wifi_monitor.run()


if __name__ == '__main__':
    main()

```
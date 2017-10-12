#### Python API to control Wi-Fi connectivity

Simple, human Python API to control your device's wireless connectivity. Allows you to:

* Switch between client and hotspot modes
* Scan for networks in client mode
* Add and remove networks in the wpa_supplicant
* Connect to a certain or any network
* Add handlers to certain network-related events, like switching modes or a successful connection

The project was originally started as a part of ReachView, the software powering [Emlid Reach](https://emlid.com/reachrs/) receivers. However, it was written with any modern Linux distro in mind. As long as you comply with the dependencies listed below, it will work.

##### Prerequisites

This package uses D-Bus to control systemd and wpa_supplicant. You need to have D-Bus itself and its python bindings in order to use this library. For example, on Ubuntu you need to install the following packages:

`sudo apt install dbus libdbus-glib-1-dev libdbus-1-dev python-dbus`

The D-Bus is used to control wpa_supplicant and hostapd systemd services. Stopping one of them and starting the other should be sufficient to actually turn on hotspot or get back to client mode on your system.

The project also relies on the following python packages:

* [netifaces](https://pypi.python.org/pypi/netifaces)
* [systemd-manager](https://github.com/emlid/systemd-manager)

The setup.py **does not contain** the python dependencies and you have to install them manually.

The wificontrol package has been tested and used with **Python 2.7**.
**Python 3.5** should also work with minor modifications, if any.

Practically everything wificontrol does, requires **root access**.

##### WiFiControl Examples

###### Checking connection status

```
>>> import wificontrol
>>> wifi = wificontrol.WiFiControl()
>>> wifi.get_status()
('wpa_supplicant', {'IP address': '192.168.1.17', 'ssid': 'MYNETWORK', 'mac address': '9f:b6:86:0f:19:93'})
```

###### Switching modes

```
>>> wifi.start_host_mode()
True
>>> wifi.start_client_mode()
True
```

###### Scanning and connecting

```
>>> wifi.scan()
>>> wifi.get_scan_results()
[{'security': 'WPA2-PSK', 'connected': False, 'ssid': 'reach:db:76'}, ...]
>>> wifi.add_network({'security': 'wpa2psk', 'ssid': 'reach:db:76', 'password': 'emlidreach', 'identity': ''})
>>> # the following method is non-blocking, but offers a callback option
...
>>> wifi.start_connecting({'ssid': 'reach:db:76'})
>>> wifi.get_status()
('wpa_supplicant', {'IP address': u'192.168.42.21', 'ssid': 'reach:db:76', 'mac address': u'90:b6:86:0f:19:93'})
```

##### WiFiControl API

All methods might raise the `wificontrol.WiFiControlError` if something does not go according to plan.
If you don't have hostapd or wpa_supplicant package, WiFiControl will raise an `OSError` exception.

All methods are blocking unless specified otherwise. Some, like `scan()`, might take a while to complete.

* `WiFiControl()` constructor arguments:
    * `interface`: network interface name. Defaults to `wlan0`
    * `wpas_config`: path to wpa_supplicant.conf file. Defaults to: `/etc/wpa_supplicant/wpa_supplicant.conf`
    * `p2p_config`: path to p2p_supplicant.conf file. Defaults to: `/etc/wpa_supplicant/p2p_supplicant.conf`
    * `hostapd_config`: path to hostapd.conf file. Defaults to: `/etc/hostapd/hostapd.conf`
    * `hostname_config`: path to hostname file. Defaults to: `/etc/hostname`

###### Hardware control

* `WiFiControl().turn_on_wifi()` - turn the wi-fi on using `rfkill`
* `WiFiControl().turn_off_wifi()` - turn the wi-fi off using `rfkill`
* `WiFiControl().is_wifi_on()` - return bool of whether the wi-fi is on

###### Mode switching

* `WiFiControl().start_host_mode()` - stop wpa_supplicant and start hostapd
* `WiFiControl().start_client_mode()` - stop hostapd and start wpa_supplicant

###### Status and naming

* `WiFiControl().get_status()` - get wireless connection status. Returns `(mode, network_info)`. Mode is on of `wpa_supplicant` or `hostapd`. `network_info` is a dict with fields `'IP address', 'ssid', 'mac address'`
* `WiFiControl().set_device_names(new_name)` - change hostname, p2p_name and Host AP SSID. Host AP SSID gets last 4 mac address digits appended in form of `reach:db:76` for uniqueness
* `WiFiControl().get_device_name()` - returns device name string
* `WiFiControl().get_hostap_name()` - returns Host AP SSID name

###### Scanning and working with networks

* `WiFiControl().scan()` - scan for visible networks. Only works in client mode
* `WiFiControl().get_scan_results()` - return a list of visible networks. Each network is represented with a dict with fields `'security', 'ssid', 'mac address'`
* `WiFiControl().get_added_networks()` - return a list of added networks. Each network is represented with a dict with fields `'security', 'ssid', 'security'`
* `WiFiControl().add_network({'security': security, 'ssid': ssid, 'password': psk, 'identity': identity})` - add a new network to the system and wpa_supplicant.conf. Security field is one of `'open', 'wep', 'wpapsk', 'wpa2psk', 'wpaeap'`. Identity is only used for WPA2 Enterprise, but is always required to be in the dict.
* `WiFiControl().remove_network({'ssid': ssid})` - remove network from the system and wpa_supplicant.conf
* `WiFiControl().start_connecting({'ssid': ssid}, callback=None, args=None, timeout=None)` - connect to one of the added networks. Add an optional callback function to execute after the connection process ended. The function's first argument will be a bool, representing connection success. Prototype looks like this: `def foo(result, args):`
* `WiFiControl().stop_connecting()` - stop the connection thread
* `WiFiControl().disconnect()` - disconnect from the current network


##### WiFiMonitor daemon

Add handlers to wpa_supplicant and hostapd D-Bus events. **Must be** run in a separate process. D-Bus does not work with Python threads. Tools directory has a script and service files used to watch for network status on Reach.

#### Usage Example

```
import signal
from wificontrol import WiFiMonitor, WiFiControl


def main():

    def handler(signum, frame):
        wifi_monitor.shutdown()

    def print_wifi_state():
        print(WiFiControl().get_status())
        wifi_monitor = WiFiMonitor()

    wifi_monitor.register_callback(wifi_monitor.HOST_STATE, print_wifi_state)
    wifi_monitor.register_callback(wifi_monitor.CLIENT_STATE, print_wifi_statete)
    wifi_monitor.register_callback(wifi_monitor.OFF_STATE, print_wifi_statetate)
    wifi_monitor.register_callback(wifi_monitor.SCAN_STATE, print_wifi_state)
    wifi_monitor.register_callback(wifi_monitor.REVERT_EVENT, print_wifi_statetify)
    wifi_monitor.register_callback(wifi_monitor.SUCCESS_EVENT, print_wifi_stateotify)

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    wifi_monitor.run()


if __name__ == '__main__':
    main()

```

##### Credits

This package was written by [Ivan Sapozhkov](https://github.com/isapozhkov) and [Denis Chagin](https://github.com/merindorium). It is used in [Emlid](https://emlid.com)'s products, such as Reach and Reach RS.

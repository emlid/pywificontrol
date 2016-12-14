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

import subprocess
from sysdmanager import SystemdManager
from netifaces import ifaddresses, AF_INET, AF_LINK

class WiFiControlError(Exception):
    pass

class WiFi(object):

    restart_mdns = "systemctl restart mdns.service && sleep 2"
    rfkill_wifi_control = lambda self, action: "rfkill {} wifi".format(action)

    def __init__(self, interface):
        self.interface = interface
        self.sysdmanager = SystemdManager()

    def restart_dns(self):
        self.execute_command(self.restart_mdns)

    def block():
        self.execute_command(self.rfkill_wifi_control("block"))

    def unblock():
        self.execute_command(self.rfkill_wifi_control("unblock"))

    def get_device_ip(self):
        try:
            return ifaddresses(self.interface)[AF_INET][0]['addr']
        except KeyError:
            return "127.0.0.1"

    def get_device_mac(self):
        try:
            return ifaddresses(self.interface)[AF_LINK][0]['addr']
        except KeyError:
            return "00:00:00:00:00:00"

    def execute_command(self, args):
        try:
            return subprocess.check_output(args, stderr=subprocess.PIPE, shell=True)
        except subprocess.CalledProcessError as error:
            error_message = "WiFiControl: subprocess call error\n"
            error_message += "Return code: {}\n".format(error.returncode)
            error_message += "Command: {}".format(args)
            raise WiFiControlError(error_message)

if __name__ == '__main__':
    wifi = WiFi('wlp6s0')
    print(wifi.get_device_ip())
    print(wifi.get_device_mac())
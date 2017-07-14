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


import os
from wificommon import WiFi


class HostAP(WiFi):
    hostapd_control = lambda self, action: "systemctl {} hostapd.service && sleep 2".format(action)

    def __init__(self, interface,
                 hostapd_config="/etc/hostapd/hostapd.conf",
                 hostname_config='/etc/hostname'):

        super(HostAP, self).__init__(interface)
        self.hostapd_path = hostapd_config
        self.hostname_path = hostname_config

        if (b'bin/hostapd' not in self.execute_command("whereis hostapd")):
            raise OSError('No HOSTAPD servise')

        self.started = lambda: self.sysdmanager.is_active("hostapd.service")

    def start(self):
        self.execute_command(self.hostapd_control("start"))

    def stop(self):
        self.execute_command(self.hostapd_control("stop"))

    def set_hostap_name(self, name='reach'):
        mac_addr = self.get_device_mac()[-6:]
        self.replace("^ssid=.*", "ssid={}{}".format(name, mac_addr), self.hostapd_path)

    def get_hostap_name(self):
        return self.re_search("(?<=^ssid=).*", self.hostapd_path)

    def set_hostap_password(self, password):
        self.replace("^wpa_passphrase=.*", "wpa_passphrase={}".format(password), self.hostapd_path)

    def set_host_name(self, name='reach'):
        try:
            with open(self.hostname_path, 'w', 0) as hostname_file:
                hostname_file.write(name + '\n')
                hostname_file.flush()
                os.fsync(hostname_file)
        except IOError:
            pass
        else:
            self.execute_command('hostname -F {}'.format(self.hostname_path))

    def get_host_name(self):
        return self.re_search("^.*", self.hostname_path)


if __name__ == '__main__':
    hotspot = HostAP('wlp6s0')

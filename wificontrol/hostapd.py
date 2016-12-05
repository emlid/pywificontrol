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

from wificommon import WiFi

class HostAP(WiFi):
    hostapd_control = lambda self, action: "systemctl {} hostapd.service && sleep 2".format(action)

    def __init__(self):
        super(HostAP, self).__init__()
        self.hostapd_path = "/etc/hostapd/hostapd.conf",
        self.hostname_path = '/etc/hostname'

        if ("bin/hostapd" not in self.execute_command("whereis hostapd")):
            raise OSError('No HOSTAPD servise')

        self.started = lambda: self.sysdmanager.is_active("hostapd.service")

    def start(self):
        self.execute_command(self._hostapd_control("start"))

    def stop(self):
        self.execute_command(self._hostapd_control("stop"))

    def get_hostap_name(self):
        return self.execute_command("grep \'^ssid=\' {}".format(self.hostapd_path))[5:-1]

    def set_hostap_password(self, password):
        self.execute_command("sed -i s/^wpa_passphrase=.*/wpa_passphrase={}/ {}".format(password, self.hostapd_path))

    def set_hostap_name(self, name='reach'):
        mac_addr = self.get_device_mac()[-6:]
        self.execute_command("sed -i s/^ssid=.*/ssid={}{}/ {}".format(name, mac_addr, self.hostapd_path))

    def set_host_name(self, name='reach'):
        try:
            hostname_file = open(self.hostname_path, 'w')
        except IOError:
            pass
        else:
            hostname_file.write(name + '\n')
            hostname_file.close()
            self.execute_command('hostname -F {}'.format(self.hostname_path))

    def get_host_name(self):
        return self.execute_command("cat {}".format(self.hostname_path)).strip()

    def get_device_mac(self):
        mac_pattern = "..:..:..:..:..:.."
        data = self.execute_command("ifconfig {}".format(self.interface))
        try:
            return re.search(mac_pattern, data).group(0)
        except TypeError:
            return None

if __name__ == '__main__':
    hotspot = HostAP()
    
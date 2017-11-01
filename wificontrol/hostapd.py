# Written by Ivan Sapozhkov and Denis Chagin <denis.chagin@emlid.com>
#
# Copyright (c) 2016, Emlid Limited
# All rights reserved.
#
# Redistribution and use in source and binary forms,
# with or without modification,
# are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software
# without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


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

    def get_hostap_name(self):
        return self.re_search("(?<=^ssid=).*", self.hostapd_path)

    def set_hostap_name(self, name='reach'):
        mac_addr = self.get_device_mac()[-6:]
        self.replace("^ssid=.*", "ssid={}{}".format(name, mac_addr), self.hostapd_path)

    def set_hostap_password(self, password):
        self.replace("^wpa_passphrase=.*",
                     "wpa_passphrase={}".format(password), self.hostapd_path)
        return self.verify_hostap_password(password)

    def verify_hostap_password(self, value):
        return self.re_search("(?<=^wpa_passphrase=).*", self.hostapd_path) == value

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

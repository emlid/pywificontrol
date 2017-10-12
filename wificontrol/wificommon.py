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
import re
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

    def block(self):
        self.execute_command(self.rfkill_wifi_control("block"))

    def unblock(self):
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

    def re_search(self, pattern, file):
        with open(file, 'r', 0) as data_file:
            data = data_file.read()
        return re.search(pattern, data, re.MULTILINE).group(0)

    def replace(self, pattern, text, file):
        with open(file, 'r', 0) as data_file:
            data = data_file.read()
        old = re.search(pattern, data, re.MULTILINE).group(0)
        with open(file, 'w', 0) as data_file:
            data_file.write(data.replace(old, text))
            data_file.flush()
            os.fsync(data_file)

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

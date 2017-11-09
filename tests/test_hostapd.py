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
from wificontrol.hostapd import HostAP
import pytest
import netifaces


@pytest.fixture
def get_interface():
    interface = None
    for iface in netifaces.interfaces():
        if 'wl' in iface:
            interface = iface
            return interface
    return interface


@pytest.mark.skipif(not get_interface(), reason="Hostapd is not installed")
class TestHostAP:
    @classmethod
    def setup_class(cls):
        cur_path = os.getcwd()
        hostapd_path = cur_path + "/tests/test_files/hostapd.conf"
        hostname_path = cur_path + "/tests/test_files/hostname"

        cls.hotspot = HostAP(get_interface(), hostapd_path, hostname_path)

    @classmethod
    def teardown_class(cls):
        pass

    def test_set_hostap_name(self):
        new_name = "testname"
        self.hotspot.set_hostap_name(new_name)
        mac_end = self.hotspot.get_device_mac()[-6:]
        assert self.hotspot.get_hostap_name() == "{}{}".format(new_name, mac_end)

    def test_set_host_name(self):
        new_name = "testname"
        self.hotspot.set_host_name(new_name)
        assert self.hotspot.get_host_name() == new_name

    def test_start_hotspot(self):
        self.hotspot.start()
        assert self.hotspot.started() is True

    def test_stop_hotspot(self):
        self.hotspot.stop()
        assert self.hotspot.started() is False

    def test_verify_hostap_password(self):
        wpa_pass = 'somepassword'
        assert self.hotspot.verify_hostap_password(wpa_pass)

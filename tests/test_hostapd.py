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
import platform
import pytest
from random import randint
from wificontrol.hostapd import HostAP
from tests import edison


@edison
class TestHostAP:
    @classmethod
    def setup_class(cls):
        if "Ubuntu" in platform.platform():
            cur_path = os.getcwd()
            hostapd_path = cur_path + "/tests/test_files/hostapd.conf"
            hostname_path = cur_path + "/tests/test_files/hostname"
            cls.hotspot = HostAP('wlp6s0', hostapd_path, hostname_path)
        else:
            cls.hotspot = HostAP('wlan0')

    @classmethod
    def teardown_class(cls):
        pass

    def test_set_hostap_name(self):
        new_name = "testname_{}".format(randint(0, 1000))
        self.hotspot.set_hostap_name(new_name)
        mac_end = self.hotspot.get_device_mac()[-6:]
        assert self.hotspot.get_hostap_name() == "{}{}".format(new_name, mac_end)

    def test_set_host_name(self):
        new_name = "testname_{}".format(randint(0, 1000))
        self.hotspot.set_host_name(new_name)
        assert self.hotspot.get_host_name() == new_name

    def test_start_hotspot(self):
        self.hotspot.start()
        assert self.hotspot.started() is True

    def test_stop_hotspot(self):
        self.hotspot.stop()
        assert self.hotspot.started() is False

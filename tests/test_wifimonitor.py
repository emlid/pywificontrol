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


import pytest
import pytest_mock
import mock
from wificontrol import WiFiMonitor, WiFiControl


class FakeWiFiControl(WiFiControl):
    def __init__(self):
        self.state = self.HOST_STATE
        self.status = {}

    def get_state(self):
        return self.state

    def get_status(self):
        return self.state, self.status

    def set_ssid(self, ssid):
        self.status['ssid'] = ssid


@pytest.fixture
def scanning_state():
    state = {
        'State': 'scanning'
    }
    return state


@pytest.fixture
def wpa_client_state():
    state = {
        'State': 'completed'
    }
    return state


@pytest.fixture
def wpa_disconnect_state():
    state = {
        'DisconnectReason': 3
    }
    return state


@pytest.fixture
def host_mode_state():
    state = {
        'ActiveState': 'active',
        'SubState': 'running'
    }
    return '', state, ''


@pytest.fixture
def disconnect_state_on_station_del():
    state = {
        'DisconnectReason': 0
    }
    return state


class FakeWifiMonitor(WiFiMonitor):
    def __init__(self):
        self.bus = mock.MagicMock()
        self._mainloop = mock.MagicMock()

        self.wifi_manager = FakeWiFiControl()

        self.callbacks = {}

        self.current_state = None
        self.current_ssid = None

        self._initialize()


class TestWiFiMonitor:
    @classmethod
    def setup_method(cls):
        cls.monitor = FakeWifiMonitor()
        cls.monitor.run()
        cls.ssid = 'TEST_SSID'

    @classmethod
    def teardown_method(cls):
        cls.monitor.shutdown()

    def test_initial_start(self):
        assert self.monitor.current_state == self.monitor.HOST_STATE

    def test_wpa_scan_state(self, scanning_state):
        self.monitor._wpa_props_changed(scanning_state)
        assert self.monitor.current_state == self.monitor.SCAN_STATE

    def test_wpa_client_state(self, wpa_client_state):
        self.monitor._wpa_props_changed(wpa_client_state)
        assert self.monitor.current_state == self.monitor.CLIENT_STATE

    def test_wpa_disconnect_state(self, wpa_disconnect_state):
        self.monitor._wpa_props_changed(wpa_disconnect_state)
        assert self.monitor.current_state == self.monitor.OFF_STATE

    def test_host_mode_state(self, wpa_client_state, host_mode_state):
        self.monitor.wifi_manager.set_ssid(self.ssid)
        self.monitor._wpa_props_changed(wpa_client_state)

        assert self.monitor.current_state == self.monitor.CLIENT_STATE
        assert self.monitor.current_ssid == self.ssid

        self.monitor._host_props_changed(*host_mode_state)

        assert self.monitor.current_state == self.monitor.HOST_STATE
        assert self.monitor.current_ssid is None

    def test_callback_execution(self, wpa_client_state, mocker):
        stub_func = mocker.stub(name='stub_func')

        self.monitor.register_callback(self.monitor.CLIENT_STATE, stub_func, args=('test',))

        self.monitor._wpa_props_changed(wpa_client_state)
        assert self.monitor.current_state == self.monitor.CLIENT_STATE
        stub_func.assert_called_with('test')

    def test_success_connection_event(self, wpa_client_state, host_mode_state, mocker):
        stub_func = mocker.stub(name='stub_func')

        self.monitor.register_callback(self.monitor.SUCCESS_EVENT, stub_func, args=('success',))

        self.monitor._host_props_changed(*host_mode_state)

        self.monitor.wifi_manager.set_ssid(self.ssid)
        self.monitor._wpa_props_changed(wpa_client_state)

        assert self.monitor.current_state == self.monitor.CLIENT_STATE
        assert self.monitor.current_ssid == self.ssid
        stub_func.assert_called_with('success')

    def test_revert_connection_event(self, wpa_client_state, scanning_state, mocker):
        stub_func = mocker.stub(name='stub_func')

        self.monitor.wifi_manager.set_ssid(self.ssid)

        self.monitor.register_callback(self.monitor.REVERT_EVENT, stub_func, args=('revert',))

        self.monitor._wpa_props_changed(wpa_client_state)
        assert self.monitor.current_state == self.monitor.CLIENT_STATE

        self.monitor._wpa_props_changed(scanning_state)
        assert self.monitor.current_state == self.monitor.SCAN_STATE

        self.monitor._wpa_props_changed(wpa_client_state)
        assert self.monitor.current_state == self.monitor.CLIENT_STATE
        stub_func.assert_called_with('revert')

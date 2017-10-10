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


import dbus
import dbus.service
import dbus.mainloop.glib
import logging
from . import WiFiControl

try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject

logger = logging.getLogger(__name__)

DBUS_PROPERTIES_IFACE = 'org.freedesktop.DBus.Properties'

WPAS_INTERFACE_DBUS_OPATH = "/fi/w1/wpa_supplicant1/Interfaces/1"
WPAS_INTERFACE_DBUS_IFACE = "fi.w1.wpa_supplicant1.Interface"

SYSTEMD_DBUS_SERVICE = 'org.freedesktop.systemd1'
SYSTEMD_DBUS_OPATH = '/org/freedesktop/systemd1'
SYSTEMD_MANAGER_DBUS_IFACE = 'org.freedesktop.systemd1.Manager'
HOSTAPD_DBUS_UNIT_OPATH = '/org/freedesktop/systemd1/unit/hostapd_2eservice'


class WiFiMonitorError(Exception):
    pass


class WiFiMonitor(object):
    CLIENT_STATE = 'CLIENT'
    HOST_STATE = 'HOST'
    SCAN_STATE = 'SCAN'
    OFF_STATE = 'OFF'

    SUCCESS_EVENT = 'SUCCESS'
    REVERT_EVENT = 'REVERT'

    STATES = {
        'completed': CLIENT_STATE,
        'scanning': SCAN_STATE,
        'disconnected': OFF_STATE,

        WiFiControl.HOST_STATE: HOST_STATE,
        WiFiControl.WPA_STATE: CLIENT_STATE,
        WiFiControl.OFF_STATE: OFF_STATE,

        ('active', 'running'): HOST_STATE,
        ('deactivating', 'stop-post'): OFF_STATE,
        ('failed', 'failed'): OFF_STATE,
    }

    def __init__(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()
        self._mainloop = GObject.MainLoop()

        self.wifi_manager = WiFiControl()

        self.callbacks = {}

        self.current_state = self.OFF_STATE
        self.current_ssid = None

    def _initialize(self):
        systemd_obj = self.bus.get_object(SYSTEMD_DBUS_SERVICE,
                                          SYSTEMD_DBUS_OPATH)
        self.sysd_manager = dbus.Interface(systemd_obj,
                                           dbus_interface=SYSTEMD_MANAGER_DBUS_IFACE)
        self.sysd_manager.Subscribe()

        self.bus.add_signal_receiver(self._wpa_props_changed,
                                     dbus_interface=WPAS_INTERFACE_DBUS_IFACE,
                                     signal_name="PropertiesChanged",
                                     path=WPAS_INTERFACE_DBUS_OPATH)

        self.bus.add_signal_receiver(self._host_props_changed,
                                     dbus_interface=DBUS_PROPERTIES_IFACE,
                                     signal_name="PropertiesChanged",
                                     path=HOSTAPD_DBUS_UNIT_OPATH)

        self._register_local_callbacks()
        self._set_initial_state()

    def _register_local_callbacks(self):
        self.register_callback(self.CLIENT_STATE, self._check_current_ssid)
        self.register_callback(self.HOST_STATE, self._clear_ssid)

    def _set_initial_state(self):
        state = self.wifi_manager.get_state()
        logger.debug('Initiate WiFiMonitor with "{}" state'.format(state))
        self._process_new_state(state)

    def _host_props_changed(self, *args):
        _, props, _ = args
        active_state = props.get('ActiveState')
        sub_state = props.get('SubState')

        if active_state and sub_state:
            self._process_new_state((active_state, sub_state))

    def _wpa_props_changed(self, props):
        state = props.get('State')
        disconnect = props.get('DisconnectReason', None)

        if disconnect is not None:
            state = 'disconnected'

        if state:
            self._process_new_state(state)

    def _process_new_state(self, state):
        state = self.STATES.get(state)
        if state and self.current_state != state:
            logger.debug('Switching to {} state'.format(state))
            self.current_state = state
            self._execute_callbacks(state)

    def _check_current_ssid(self):
        event = self.REVERT_EVENT

        if self._ssid_updated:
            event = self.SUCCESS_EVENT

        self._execute_callbacks(event)

    @property
    def _ssid_updated(self):
        _, status = self.wifi_manager.get_status()

        try:
            ssid = status['ssid']
        except (KeyError, TypeError) as error:
            logger.debug('Got empty network status')
            raise WiFiMonitorError(error)

        if self.current_ssid != ssid:
            self.current_ssid = ssid
            return True

        return False

    def _clear_ssid(self):
        self.current_ssid = None

    def register_callback(self, msg, callback, args=()):
        if msg not in self.callbacks:
            self.callbacks[msg] = []

        self.callbacks[msg].append((callback, args))

    def _execute_callbacks(self, msg):
        callbacks = self.callbacks.get(msg)
        if callbacks:
            for callback in callbacks:
                callback, args = callback
                try:
                    callback(*args)
                except Exception as error:
                    logger.error('Callback {} execution error. {}'.format(callback.__name__, error))

    def run(self):
        try:
            self._initialize()
        except dbus.exceptions.DBusException as error:
            logger.error(error)
            raise WiFiMonitorError(error)

        self._mainloop.run()

    def shutdown(self):
        self._deinitialize()
        self._mainloop.quit()
        logger.info('WiFiMonitor stopped')

    def _deinitialize(self):
        try:
            self.sysd_manager.Unsubscribe()
        except dbus.exceptions.DBusException as error:
            logger.error(error)
            raise WiFiMonitorError(error)

import dbus
import dbus.service
import dbus.mainloop.glib
import signal
import logging
from wificontrol import WiFiControl
from reachstatus import StateClient
from daemon_tree import DaemonTreeObj, DaemonTreeError
from wifireconnect import WORKER_NAME

try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject

logging.basicConfig()
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

        self.current_state = None
        self.current_ssid = None

        self.reconnect_worker = DaemonTreeObj(WORKER_NAME)
        self.disconnect_reason = None

        try:
            self._initialize()
        except dbus.exceptions.DBusException as error:
            logger.error(error)
            raise WiFiMonitorError(error)

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
        self.register_callback(self.CLIENT_STATE, self._stop_reconnect_worker)

        self.register_callback(self.HOST_STATE, self._clear_ssid)
        self.register_callback(self.HOST_STATE, self._stop_reconnect_worker)

        self.register_callback(self.OFF_STATE, self._check_disconnect_reason)

    def _set_initial_state(self):
        state = self.wifi_manager.get_state()
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
            self.disconnect_reason = disconnect
            state = 'disconnected'

        if state:
            self._process_new_state(state)

    def _process_new_state(self, state):
        state = self.STATES.get(state)
        if state and self.current_state != state:
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
            raise WiFiMonitorError(error)

        if self.current_ssid != ssid:
            self.current_ssid = ssid
            return True

        return False

    def _clear_ssid(self):
        self.current_ssid = None

    def _check_disconnect_reason(self):
        if self._station_went_offline:
            self._start_reconnect_worker()
        self.disconnect_reason = None

    @property
    def _station_went_offline(self):
        return self.disconnect_reason in (0, 3)

    def _start_reconnect_worker(self):
        try:
            self.reconnect_worker.call('start_reconnection', args=(self.current_ssid,))
        except DaemonTreeError as error:
            raise WiFiMonitorError(error)

    def _stop_reconnect_worker(self):
        try:
            self.reconnect_worker.call('stop_reconnection')
        except DaemonTreeError as error:
            raise WiFiMonitorError(error)

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
                except WiFiMonitorError as error:
                    logger.error(error)
                except Exception as error:
                    logger.error(error)
                    raise WiFiMonitorError(error)

    def run(self):
        self._mainloop.run()

    def shutdown(self):
        self._deinitialize()
        self._mainloop.quit()

    def _deinitialize(self):
        try:
            self.sysd_manager.Unsubscribe()
        except dbus.exceptions.DBusException as error:
            logger.error(error)
            raise WiFiMonitorError(error)


def main():
    def handler(signum, frame):
        wifi.shutdown()

    wifi = WiFiMonitor()

    wifi.register_callback(wifi.HOST_STATE, StateClient.set_network_state, ('hotspot',))
    wifi.register_callback(wifi.CLIENT_STATE, StateClient.set_network_state, ('client',))
    wifi.register_callback(wifi.OFF_STATE, StateClient.set_network_state, ('disabled',))
    wifi.register_callback(wifi.SCAN_STATE, StateClient.set_network_state, ('scan',))
    wifi.register_callback(wifi.REVERT_EVENT, StateClient.send_notification, ('connection_failed',))
    wifi.register_callback(wifi.SUCCESS_EVENT, StateClient.send_notification,
                           ('connection_success',))

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    wifi.run()


if __name__ == '__main__':
    main()

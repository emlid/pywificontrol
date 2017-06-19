import pytest
import mock
import threading
from wificontrol.wifireconnect import ReconnectWorker


@pytest.fixture
def valid_network():
    network = {
        'ssid': 'TEST_SSID'
    }
    return network


class FakeReconnectWorker(ReconnectWorker):
    def __init__(self):
        self.manager = mock.MagicMock()
        self.interrupt = threading.Event()
        self.worker = None


class TestReconnectWorker:
    def setup_method(self):
        self.reconnect_worker = FakeReconnectWorker()
        self.reconnect_worker.TIMEOUT = 0.1

    def teardown_method(self):
        self.reconnect_worker.stop_reconnection()

    def test_reconnection_start_and_stop(self, valid_network):
        self.reconnect_worker.start_reconnection(valid_network['ssid'])

        self.reconnect_worker.interrupt.wait(0.5)

        self.reconnect_worker.manager.scan.assert_called()
        self.reconnect_worker.manager.get_scan_results.assert_called()

        self.reconnect_worker.stop_reconnection()

        assert self.reconnect_worker.interrupt.is_set()
        assert self.reconnect_worker.worker is None

    def test_reconnection_worker_success_connection(self, valid_network):
        def start_connecting(network, callback, *args, **kwargs):
            assert network == valid_network
            callback(True)

        self.reconnect_worker.manager.start_connecting.side_effect = start_connecting

        self.reconnect_worker.start_reconnection(valid_network['ssid'])
        self.reconnect_worker.interrupt.wait(0.5)

        self.reconnect_worker.manager.get_scan_results.return_value = [valid_network]

        self.reconnect_worker.interrupt.wait(2)
        assert self.reconnect_worker.interrupt.is_set()

        self.reconnect_worker.stop_reconnection()
        assert self.reconnect_worker.worker is None

    def test_second_worker_start(self, valid_network):
        self.reconnect_worker.start_reconnection(valid_network['ssid'])
        worker = self.reconnect_worker.worker
        self.reconnect_worker.start_reconnection(valid_network['ssid'])
        assert self.reconnect_worker.worker == worker

    def test_worker_restart(self, valid_network):
        self.reconnect_worker.start_reconnection(valid_network['ssid'])
        self.reconnect_worker.interrupt.wait(1)
        self.reconnect_worker.stop_reconnection()

        self.reconnect_worker.start_reconnection(valid_network['ssid'])
        self.reconnect_worker.interrupt.wait(1)
        self.reconnect_worker.stop_reconnection()

        assert self.reconnect_worker.interrupt.is_set()
        assert self.reconnect_worker.worker is None

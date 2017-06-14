import platform
import sys
import pytest
import mock

not_edison = "edison" not in platform.platform()
edison = pytest.mark.skipif(not_edison,
                            reason="Not supported in this platform")

if not_edison:
    sys.modules['dbus'] = mock.MagicMock()
    sys.modules['dbus.service'] = mock.MagicMock()
    sys.modules['dbus.mainloop'] = mock.MagicMock()
    sys.modules['dbus.mainloop.glib'] = mock.MagicMock()
    sys.modules['gobject'] = mock.MagicMock()

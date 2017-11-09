import platform
import pytest

not_edison = "edison" not in platform.platform()
edison = pytest.mark.skipif(not_edison,
                            reason="Not supported in this platform")
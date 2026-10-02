import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class FakeClient:
    """Stand-in for databento.Historical: records calls, never touches the network."""

    def __init__(self, cost_per_request: float = 0.10):
        self.cost_calls = []
        self.download_calls = []
        self.cost_per_request = cost_per_request
        self.metadata = SimpleNamespace(get_cost=self._get_cost)
        self.timeseries = SimpleNamespace(get_range=self._get_range)

    def _get_cost(self, **kw):
        self.cost_calls.append(kw)
        return self.cost_per_request

    def _get_range(self, path=None, **kw):
        self.download_calls.append(kw)
        Path(path).write_bytes(b"fake-dbn")


@pytest.fixture
def fake_client():
    return FakeClient()

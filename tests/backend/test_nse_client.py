import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from data.nse_client import NSEClient


class _DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _DummyClient:
    def __init__(self, payload):
        self._payload = payload

    async def get(self, *args, **kwargs):
        return _DummyResponse(self._payload)


@pytest.mark.asyncio
async def test_fetch_option_chain_falls_back_to_mock_when_chain_empty(monkeypatch):
    payload = {
        "records": {
            "underlyingValue": 0,
            "expiryDates": [],
            "data": [],
        }
    }

    client = NSEClient()

    async def _mock_refresh_cookies():
        return None

    async def _mock_get_client():
        return _DummyClient(payload)

    async def _mock_cache_get(_key):
        return None

    async def _mock_cache_set(_key, _value, ttl=None):
        return None

    monkeypatch.setattr(client, "_refresh_cookies", _mock_refresh_cookies)
    monkeypatch.setattr(client, "_get_client", _mock_get_client)

    from data import nse_client as nse_client_module
    monkeypatch.setattr(nse_client_module.cache, "get", _mock_cache_get)
    monkeypatch.setattr(nse_client_module.cache, "set", _mock_cache_set)

    result = await client.fetch_option_chain("BANKNIFTY")

    assert result.get("is_mock") is True
    assert len(result.get("chain", [])) > 0

import pytest

from tests.conftest import NETWORK_PING, NETWORK_PONG


def test_bridge(bridge, owner, contracts):
    with bridge.use(NETWORK_PING) as provider:
        contracts.Ping.sendPing(sender=owner)

    with bridge.use(NETWORK_PONG) as provider:
        assert contracts.Pong.pings() == 1
        contracts.Pong.sendPong(sender=owner)

    with bridge.use(NETWORK_PING) as provider:
        assert contracts.Ping.pongs() == 1

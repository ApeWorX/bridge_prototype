import pytest

from tests.conftest import NETWORK_PING, NETWORK_PONG


def test_bridge(bridge, owner, ping, pong):
    with bridge.use(NETWORK_PING) as provider:
        ping.sendPing(sender=owner)

    with bridge.use(NETWORK_PONG) as provider:
        assert pong.pings() == 1
        pong.sendPong(sender=owner)

    with bridge.use(NETWORK_PONG) as provider:
        assert ping.pongs() == 1

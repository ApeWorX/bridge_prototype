import pytest

from tests.conftest import NETWORK_PING, NETWORK_PONG


def test_bridge(bridge, owner, ping, pong):
    with bridge.connect(NETWORK_PING):
        ping.sendPing(sender=owner)

    with bridge.connect(NETWORK_PONG):
        assert pong.pings() == 1
        pong.sendPong(sender=owner)

    with bridge.connect(NETWORK_PING):
        assert ping.pongs() == 1

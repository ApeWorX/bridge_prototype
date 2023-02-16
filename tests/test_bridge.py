from tests.conftest import NETWORK_PING, NETWORK_PONG


def test_bridge(bridge, owner, ping, pong):
    with bridge.use_network(NETWORK_PING):
        ping.sendPing(sender=owner)

    with bridge.use_network(NETWORK_PONG):
        assert pong.pings() == 1

    with bridge.use_network(NETWORK_PING):
        assert ping.pongs() == 1

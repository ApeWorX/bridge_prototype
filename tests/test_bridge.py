from tests.conftest import NETWORK_PING, NETWORK_PONG


def test_bridge(bridge, owner, ping, pong):
    """
    Tests nested cross-chain calls between the Ping and Pong contracts:
        - User initiates ping-pong via Ping.sendPing()
        - Bridge picks up Ping's xcall and relays it to Pong
        - Pong makes its own xcall which the bridge relays back to Ping
    """
    with bridge.use_network(NETWORK_PING):
        ping.sendPing(sender=owner)

    with bridge.use_network(NETWORK_PONG):
        assert pong.pings() == 1

    with bridge.use_network(NETWORK_PING):
        assert ping.pongs() == 1

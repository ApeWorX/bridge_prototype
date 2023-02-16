import pytest

from .utils import ConnextBridge


NETWORK_PING = "network_ping"
NETWORK_PONG = "network_pong"


@pytest.fixture(scope="session")
def owner(accounts):
    return accounts[0]


@pytest.fixture(scope="session")
def bridge(owner):
    return ConnextBridge(owner, NETWORK_PING, NETWORK_PONG)


@pytest.fixture(scope="session")
def contracts(project, owner, bridge):
    with bridge.use_network(NETWORK_PING) as provider:
        ping = owner.deploy(project.Ping, bridge.connext.address, owner)
        bridge.register_contract(ping)

        ping_network_id = provider.network.network_id

    with bridge.use_network(NETWORK_PONG) as provider:
        pong = owner.deploy(project.Pong, bridge.connext.address, owner)
        bridge.register_contract(pong)

        pong_network_id = provider.network.network_id

    with bridge.use_network(NETWORK_PING):
        ping.authenticate(pong_network_id, pong.address, sender=owner)

    with bridge.use_network(NETWORK_PONG):
        pong.authenticate(ping_network_id, ping.address, sender=owner)

    return ping, pong


@pytest.fixture(scope="session")
def ping(contracts):
    return contracts[0]


@pytest.fixture(scope="session")
def pong(contracts):
    return contracts[1]

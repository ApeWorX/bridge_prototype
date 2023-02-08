import pytest

from .utils import ConnextBridge


NETWORK_PING = "network-ping"
NETWORK_PONG = "network-pong"


@pytest.fixture(scope="session")
def owner(accounts):
    return accounts[0]


@pytest.fixture(scope="session")
def bridge(owner):
    return ConnextBridge(owner, NETWORK_PING, NETWORK_PONG)


@pytest.fixture(scope="session")
def ping(project, owner, bridge):
    with bridge.provider(NETWORK_PING) as provider:
        contract = owner.deploy(
            project.Ping,
            bridge.at(NETWORK_PING),
            owner,
            provider.network.chain_id,
            bridge.at(NETWORK_PONG),
        )

        bridge.register(NETWORK_PING, contract)
        return contract


@pytest.fixture(scope="session")
def pong(project, owner, bridge):
    with bridge.provider(NETWORK_PONG) as provider:
        contract = owner.deploy(
            project.Pong,
            bridge.at(NETWORK_PONG),
            owner,
            provider.network.chain_id,
            bridge.at(NETWORK_PING),
        )

        bridge.register(NETWORK_PONG, contract)
        return contract

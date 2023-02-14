from dataclasses import dataclass

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
    @dataclass
    class Contracts:
        Ping: "Contract" = None
        Pong: "Contract" = None

    contracts = Contracts()

    with bridge.provider(NETWORK_PING) as provider:
        contracts.Ping = owner.deploy(
            project.Ping,
            bridge.at(NETWORK_PING),
            owner,
        )

        bridge.register(NETWORK_PING, contracts.Ping)

    with bridge.provider(NETWORK_PONG) as provider:
        contracts.Pong = owner.deploy(
            project.Pong,
            bridge.at(NETWORK_PONG),
            owner,
        )

        bridge.register(NETWORK_PONG, contracts.Pong)

    with bridge.provider(NETWORK_PING) as provider:
        contracts.Ping.authenticate(
            bridge.networks[NETWORK_PONG].provider.network.network_id,
            contracts.Pong.address,
            sender=owner,
        )

    with bridge.provider(NETWORK_PONG) as provider:
        contracts.Ping.authenticate(
            bridge.networks[NETWORK_PING].provider.network.network_id,
            contracts.Ping.address,
            sender=owner,
        )

    return contracts

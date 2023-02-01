import pytest

from .utils import ConnextBridge


NETWORK_A = "network-a"
NETWORK_B = "network-b"


@pytest.fixture(scope="session")
def owner(accounts):
    return accounts[0]


@pytest.fixture(scope="session")
def bridge(owner):
    return ConnextBridge(owner, NETWORK_A, NETWORK_B)


@pytest.fixture(scope="session")
def sender_contract(project, owner, bridge):
    return bridge.deploy(
        project.Sender,
        owner,
        NETWORK_A,
        bridge.get_connext_address(NETWORK_B),
    )


@pytest.fixture(scope="session")
def receiver_contract(project, owner, bridge):
    return bridge.deploy(
        project.Receiver,
        owner,
        NETWORK_B,
    )

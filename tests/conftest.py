import pytest

from .utils import ConnextBridge


@pytest.fixture(scope="session")
def owner(accounts):
    return accounts[0]


@pytest.fixture(scope="session")
def bridge(owner):
    return ConnextBridge(owner)


@pytest.fixture(scope="session")
def sender_contract(project, owner, bridge):
    return bridge.deploy_contract(
        project.Sender,
        owner,
        "A",
        bridge.connext,
    )


@pytest.fixture(scope="session")
def receiver_contract(project, owner, bridge):
    return bridge.deploy_contract(
        project.Receiver,
        owner,
        "A",
    )

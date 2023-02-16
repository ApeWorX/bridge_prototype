import pytest

from .utils import ConnextBridge

# For now our ConnextBridge is responsible for creating the networks and
# providers used in cross-chain calls. The prototype implementation accepts
# name strings, which determine the number and names of networks to create.
#
# In the future the user will be able to provide their own network/provider, so
# that they can utilize live testnet versions of Connext.
NETWORK_PING = "network_ping"
NETWORK_PONG = "network_pong"


@pytest.fixture(scope="session")
def owner(accounts):
    """
    The default test account to use for Connext, Ping, and Pong deployments.
    """
    return accounts[0]


@pytest.fixture(scope="session")
def bridge(owner):
    """
    The bridge that stands up two local networks for Connext testing.

    During this constructor the bridge will create two HardhatProvider instances
    and deploy its Connext.sol contract to each of them.
    """
    return ConnextBridge(owner, NETWORK_PING, NETWORK_PONG)


@pytest.fixture(scope="session")
def contracts(project, owner, bridge):
    """
    The Ping and Pong contracts, deployed to their respective networks.

    Because this example includes authentication, we must place both contracts
    in this 'contracts' fixture so that we can call authenticate() appropriately
    after the contracts deploy.
    """
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

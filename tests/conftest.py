import pytest

from ape.types import LogFilter


class BridgeListener:
    def __init__(self, context, addresses):
        self._context = context
        self._addresses = addresses

    def __enter__(self):
        self._context.__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        logs = list(
            *self._context.provider.get_contract_logs(
                LogFilter(addresses=self._addresses),
            ),
        )

        print(logs)

        return self._context.__exit__(exc_type, exc_value, traceback)


class Bridge:
    def __init__(self, networks):
        self._networks = networks
        self._addresses = []

    def add_contract(self, addr):
        self._addresses.append(addr)

    def network(self, name: str):
        return BridgeListener(
            self._networks.ethereum.local.use_provider(name),
            self._addresses,
        )


@pytest.fixture(scope="session")
def owner(accounts):
    return accounts[0]


@pytest.fixture(scope="session")
def bridge(networks):
    return Bridge(networks)


@pytest.fixture(scope="session")
def sender_contract(project, owner, bridge):
    with bridge.network("test"):
        contract = owner.deploy(project.Sender)
        bridge.add_contract(contract.address)
        return contract


@pytest.fixture(scope="session")
def receiver_contract(project, owner, bridge):
    with bridge.network("test"):
        contract = owner.deploy(project.Receiver)
        bridge.add_contract(contract.address)
        return contract

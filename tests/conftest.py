from collections import defaultdict
from contextlib import contextmanager
from itertools import chain

import pytest

from ape.types import LogFilter


class Bridge:
    def __init__(self, networks):
        self._networks = networks

        # For each provider (later, network) we save the contracts we deployed to it via the bridge
        # Dict[str, Contract]
        self._contracts = defaultdict(list)

        # For each contract, and event the contract defines, have a listener list
        # Dict[ContractAddr, Dict[str, Callable]]
        self._listeners = defaultdict(dict)

    @contextmanager
    def provider(self, name):
        try:
            with self._networks.ethereum.local.use_provider(name) as provider:
                yield provider

                events = []
                for contract in self._contracts[name]:
                    events.extend(contract.contract_type.events)

                log_filter = LogFilter(
                    addresses=[contract.address for contract in self._contracts[name]],
                    events=events,
                    start_block=provider.chain_manager.blocks.height,
                    stop_block=provider.chain_manager.blocks.height + 100,
                )

                for log in provider.get_contract_logs(log_filter):
                    if log.contract_address not in self._listeners:
                        continue

                    listener_map = self._listeners[log.contract_address]

                    if log.event_name not in listener_map:
                        continue

                    listener_map[log.event_name]()

        finally:
            pass

    def add_listener(self, contract, event, func):
        self._listeners[contract.address][event.name] = func

    def deploy_contract(self, contract, owner, provider):
        with self._networks.ethereum.local.use_provider(provider):
            result = owner.deploy(contract)
            self._contracts[provider].append(result)
            return result


@pytest.fixture(scope="session")
def owner(accounts):
    return accounts[0]


@pytest.fixture(scope="session")
def bridge(networks):
    return Bridge(networks)


@pytest.fixture(scope="session")
def sender_contract(project, owner, bridge):
    return bridge.deploy_contract(project.Sender, owner, "test")


@pytest.fixture(scope="session")
def receiver_contract(project, owner, bridge):
    return bridge.deploy_contract(project.Receiver, owner, "test")

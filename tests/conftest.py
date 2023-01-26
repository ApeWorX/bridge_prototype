from collections import defaultdict
from contextlib import contextmanager
from itertools import chain
from tempfile import mkdtemp
from typing import List

import pytest

from ape.api import NetworkAPI, ProviderContextManager, create_network_type, Address
from ape.types import LogFilter
from ape_test.provider import LocalProvider


class Bridge:
    def __init__(self, *network_names: str):
        self._providers = {}

        chain_id = 1
        network_id = 1
        for network_name in network_names:
            network = NetworkAPI.create_adhoc_network()
            network.name = network_name

            provider = LocalProvider(
                name="test",
                network=network,
                provider_settings={},
                data_folder=network.data_folder,
                request_header=network.request_header,
            )

            self._providers[network_name] = provider

        # For each provider (later, network) we save the contracts we deployed to it via the bridge
        # Dict[str, Contract]
        self._contracts = defaultdict(list)

        # For each contract, and event the contract defines, have a listener list
        # Dict[ContractAddr, Dict[str, Callable]]
        self._listeners = defaultdict(dict)

    @contextmanager
    def use_network(self, network_name):
        try:
            with ProviderContextManager(self._providers[network_name]) as provider:
                yield provider

                events = []
                addresses = []
                for contract in self._contracts[network_name]:
                    addresses.append(contract.address)
                    events.extend(contract.contract_type.events)

                log_filter = LogFilter(
                    addresses=addresses,
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

    def deploy_contract(self, contract, owner, network_name, *args):
        with ProviderContextManager(self._providers[network_name]):
            result = owner.deploy(contract, *args)
            self._contracts[network_name].append(result)
            return result


@pytest.fixture(scope="session")
def owner(accounts):
    return accounts[0]


@pytest.fixture(scope="session")
def bridge():
    return Bridge("testnet1", "testnet2")


@pytest.fixture(scope="session")
def sender_contract(project, owner, bridge):
    return bridge.deploy_contract(
        project.Sender,
        owner,
        "testnet1",
        Address("0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45"),
    )


@pytest.fixture(scope="session")
def receiver_contract(project, owner, bridge):
    return bridge.deploy_contract(project.Receiver, owner, "testnet2")

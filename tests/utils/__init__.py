import os
import shutil
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import mkdtemp
from typing import List

import ape
from ape.api import Address, create_network_type, NetworkAPI, ProviderContextManager
from ape.types import HexBytes, LogFilter
from ape_hardhat.provider import HardhatProvider, HardhatNetworkConfig


@dataclass
class ConnextNetwork:
    connext: "Contract" = None
    contracts: "dict[Address, Contract]" = field(default_factory=dict)
    provider: "ProviderAPI" = None
    processed_events: "set[HexBytes]" = field(default_factory=set)

    @property
    def name(self) -> str:
        return self.provider.name


class ConnextBridge:
    networks: dict[str, ConnextNetwork] = dict()

    def __init__(self, owner, *network_names: list[str]):
        chain_id = 0
        network_id = 0

        ethereum_class = None
        for plugin_name, ecosystem_class in NetworkAPI.plugin_manager.ecosystems:
            if plugin_name == "ethereum":
                ethereum_class = ecosystem_class
                break

        if ethereum_class is None:
            raise Exception("Core Ethereum plugin missing.")

        for network_name in set(network_names):
            data_folder = mkdtemp()
            request_header = NetworkAPI.config_manager.REQUEST_HEADER

            network = create_network_type(chain_id, network_id)(
                name="hardhat",
                ecosystem=ethereum_class(
                    data_folder=data_folder,
                    request_header=request_header,
                ),
                data_folder=data_folder,
                request_header=request_header,
                _default_provider="hardhat",
            )

            provider = HardhatProvider(
                name="hardhat",
                network=network,
                provider_settings=HardhatNetworkConfig(),
                data_folder=network.data_folder,
                request_header=network.request_header,
            )
            provider.connect()

            self.networks[name] = ConnextNetwork(
                provider=provider,
                connext=owner.deploy(
                    ape.project.dependencies["ApeConnext"]["local"].Connext,
                    required_confirmations=0,
                ),
            )

            chain_id += 1
            network_id += 1

    def connext(self, network_name: str) -> "Contract":
        """
        Returns the Connext contract instance deployed for the given network.
        """
        if network_name not in self.networks:
            raise ValueError

        return self.networks[network_name].connext

    @contextmanager
    def bridge(self, network_name: str):
        if network_name not in self.networks:
            raise ValueError

        network = self.networks[network_name]

        with ProviderContextManager(provider=network.provider) as provider:
            yield provider

            log_filter = LogFilter(
                addresses=[self.connext.address],
                events=self.connext.contract_type.events,
                start_block=self.provider.chain_manager.blocks.height,
                stop_block=self.provider.chain_manager.blocks.height + 100,
            )

            for log in provider.get_contract_logs(log_filter):
                event_name = log.event_name
                event_args = log.event_arguments

                if event_name != network.connext.XCalled.name:
                    continue

                transfer_id = event_args["transferId"]
                if transfer_id in network.processed_events:
                    continue

                asset = event_args["asset"]
                amount = event_args["amount"]

                (
                    origin_domain,
                    _,  # destination_domain
                    _,  # canonical_domain
                    to_addr,
                    _,  # delegate_addr
                    _,  # receive_local
                    calldata,
                    _,  # slippage
                    origin_sender,
                    _,  # bridged_amount
                    _,  # normalized_in
                    _,  # nonce
                    _,  # canonical_id
                ) = event_args["params"]

                to_addr = HexBytes(to_addr)
                if to_addr not in network.contracts:
                    raise ValueError(f"Unhandled address {to_addr}")

                contracts[to_addr].xReceive(
                    transfer_id,
                    amount,
                    asset,
                    origin_sender,
                    origin_domain,
                    calldata,
                    sender=origin_sender,
                )

    def deploy(self, contract, owner, network_name, *args):
        result = owner.deploy(contract, *args)
        self.contracts[network_name][HexBytes(result.address)] = result
        return result

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
        chain_id = 31337
        network_id = 0
        port = 8545

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
                name=network_name,
                ecosystem=ethereum_class(
                    data_folder=data_folder,
                    request_header=request_header,
                ),
                data_folder=data_folder,
                request_header=request_header,
                _default_provider="hardhat",
            )

            # TODO: Open a new PR to allow NetworkAPI to have a default-config
            #       see NetworkAPI.config, the default is just {} currently.
            #       This direct assignment hack gets around that.
            network.__dict__["gas_limit"] = "max"

            provider = HardhatProvider(
                name="hardhat",
                network=network,
                provider_settings=HardhatNetworkConfig(port=port),
                data_folder=network.data_folder,
                request_header=network.request_header,
            )
            provider.connect()

            with ProviderContextManager(provider=provider) as provider:
                self.networks[network_name] = ConnextNetwork(
                    provider=provider,
                    connext=owner.deploy(
                        ape.project.dependencies["ApeConnext"]["local"].Connext,
                        required_confirmations=0,
                    ),
                )

            port += 1
            network_id += 1

    def at(self, network_name: str) -> "Address":
        """
        Returns the Connext contract address for the given network.
        """
        if network_name not in self.networks:
            raise ValueError

        return self.networks[network_name].connext.address

    def provider(self, network_name: str) -> "Provider":
        if network_name not in self.networks:
            raise ValueError

        return ProviderContextManager(provider=self.networks[network_name].provider)

    @contextmanager
    def use(self, network_name: str):
        if network_name not in self.networks:
            raise ValueError

        network = self.networks[network_name]

        with ProviderContextManager(provider=network.provider) as provider:
            yield provider

            log_filter = LogFilter(
                addresses=[network.connext.address],
                events=network.connext.contract_type.events,
                start_block=provider.chain_manager.blocks.height,
                stop_block=provider.chain_manager.blocks.height + 100,
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
                    destination_domain,
                    _,  # canonical_domain
                    to_addr,
                    delegate_addr,
                    _,  # receive_local
                    calldata,
                    _,  # slippage
                    origin_sender,
                    _,  # bridged_amount
                    _,  # normalized_in
                    _,  # nonce
                    _,  # canonical_id
                ) = event_args["params"]

                destination_network = None
                for other_network in self.networks.values():
                    other_network_id = other_network.provider.network.network_id
                    if other_network_id == destination_domain:
                        destination_network = other_network
                        break

                if destination_network is None:
                    raise ValueError(f"Unhandled domain {destination_domain}")

                to_addr = HexBytes(to_addr)
                if to_addr not in destination_network.contracts:
                    raise ValueError(f"Unhandled address {str(to_addr)}")

                with ProviderContextManager(provider=destination_network.provider):
                    destination_network.contracts[to_addr].xReceive(
                        transfer_id,
                        amount,
                        asset,
                        origin_sender,
                        origin_domain,
                        calldata,
                        # FIXME: Don't think delegate is supposed to be used
                        #        this way. Need to make sure we pass owner
                        #        around correctly in xcall()/XCalled.
                        sender=delegate_addr,
                    )

    def register(self, network_name: str, contract: "Contract"):
        if network_name not in self.networks:
            raise ValueError

        assert contract.is_contract

        for network in self.networks.values():
            if contract.address == network.connext.address:
                raise Exception

        network = self.networks[network_name]

        address = HexBytes(contract.address)
        if address in network.contracts:
            raise ValueError("Contract already deployed on this network")

        network.contracts[address] = contract

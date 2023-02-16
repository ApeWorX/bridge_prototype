from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps
from tempfile import mkdtemp

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
        return self.provider.network.name

    @property
    def id(self) -> int:
        return self.provider.network.network_id


class ConnextBridge:
    networks: dict[str, ConnextNetwork] = dict()

    def __init__(self, owner, *network_names: list[str]):
        chain_id = 31337
        network_id = 1
        port = 8545

        ethereum_class = None
        for plugin_name, ecosystem_class in NetworkAPI.plugin_manager.ecosystems:
            if plugin_name == "ethereum":
                ethereum_class = ecosystem_class
                break

        if ethereum_class is None:
            raise RuntimeError("Core Ethereum plugin missing.")

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
                        network_id,
                    ),
                )

            port += 1
            network_id += 1

    @contextmanager
    def use_network(self, network_name: str) -> "ProviderAPI":
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

                # NOTE: Only dealing with XCalled for the demo
                if event_name != network.connext.XCalled.name:
                    continue

                transfer_id = HexBytes(event_args["transferId"])
                if transfer_id in network.processed_events:
                    continue

                asset = event_args["asset"]
                amount = event_args["amount"]

                (
                    origin_domain,
                    destination_domain,
                    _,  # canonical_domain
                    to_addr,
                    _,  # delegate_addr,
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

                network.processed_events.add(transfer_id)

                with self.use_network(destination_network.name):
                    destination_network.contracts[to_addr].xReceive(
                        transfer_id,
                        amount,
                        asset,
                        origin_sender,
                        origin_domain,
                        calldata,
                        # FIXME: Get actual owner AccountAPI in a better way
                        sender=ape.accounts.test_accounts[0],
                    )

    @staticmethod
    def requires_bridging(fn):
        @wraps(fn)
        def wrapper(self, *args, **kwargs):
            network_name = ape.networks.active_provider.network.name
            if network_name not in self.networks:
                raise ValueError("Active network is not a bridged network")
            return fn(self, self.networks[network_name], *args, **kwargs)

        return wrapper

    @requires_bridging
    def register_contract(self, network: ConnextNetwork, contract: "Contract"):
        """
        Registers a contract with the bridge that has been deployed on the
        active network.

        You must call this within a `use_provider()` context.
        """
        assert contract.is_contract

        if contract.address == network.connext.address:
            raise ValueError("Only user contracts should be registered")

        network.contracts[HexBytes(contract.address)] = contract

    @property
    @requires_bridging
    def connext(self, network: ConnextNetwork) -> "Address":
        """
        Returns the Connext contract for the given network.

        You must call this within a `use_provider()` context.
        """
        return network.connext

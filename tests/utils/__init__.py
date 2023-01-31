import os
import shutil
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from tempfile import mkdtemp
from typing import List

import ape
from ape.api import Address
from ape.types import HexBytes, LogFilter


# IDEA
class ConnextNetwork:
    owner: "Account"
    connext: "Contract"
    contracts: "dict[Address, Contract]"
    provider: "ProviderAPI"
    processed_events: "set[HexBytes]"


class ConnextBridge:
    def __init__(self, owner, *networks):
        self.contracts = defaultdict(dict)

        # FIXME: One per network
        self.connext = owner.deploy(
            ape.project.dependencies["ApeConnext"]["local"].Connext,
            required_confirmations=0,
        )

        # FIXME: Will need multiple providers + multiple owners/accounts
        self.provider = owner.provider
        self.owner = owner

        self.processed_events = set()

    @contextmanager
    def use_network(self, network_name):
        assert network_name in self.contracts

        yield

        log_filter = LogFilter(
            addresses=[self.connext.address],
            events=self.connext.contract_type.events,
            start_block=self.provider.chain_manager.blocks.height,
            stop_block=self.provider.chain_manager.blocks.height + 100,
        )

        for log in self.provider.get_contract_logs(log_filter):
            event_name = log.event_name
            event_args = log.event_arguments

            if event_name != self.connext.XCalled.name:
                continue

            transfer_id = event_args["transferId"]
            if transfer_id in self.processed_events:
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
            contracts = self.contracts["A"]

            if to_addr not in contracts:
                raise Exception(f"Unhandled address {to_addr}")

            contracts[to_addr].xReceive(
                transfer_id,
                amount,
                asset,
                origin_sender,
                origin_domain,
                calldata,
                sender=self.owner,
            )

    def deploy_contract(self, contract, owner, network_name, *args):
        result = owner.deploy(contract, *args)
        self.contracts[network_name][HexBytes(result.address)] = result
        return result

import os
import shutil
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from tempfile import mkdtemp
from typing import List

import ape
from ape.api import Address
from ape.types import LogFilter


class ConnextBridge:
    def __init__(self, owner, *networks):
        self.contracts = defaultdict(list)
        self.connext = owner.deploy(
            ape.project.dependencies["ApeConnext"]["local"].Connext,
            required_confirmations=0,
        )
        self.provider = owner.provider
        self.owner = owner

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
            if log.event_name == self.connext.XCalled.name:
                # bytes32 _transferId,
                # uint256 _amount,
                # address _asset,
                # address _originSender,
                # uint32 _origin,
                # bytes memory _callData
                self.contracts["A"][1].xReceive(
                    bytes(),
                    0,
                    "0x0000000000000000000000000000000000000000",
                    self.connext.address,
                    0,
                    bytes(),
                    sender=self.owner,
                )

    def deploy_contract(self, contract, owner, network_name, *args):
        result = owner.deploy(contract, *args)
        self.contracts[network_name].append(result)
        return result

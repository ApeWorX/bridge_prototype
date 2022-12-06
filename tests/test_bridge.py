import pytest


def test_bridge(bridge, owner, sender_contract, receiver_contract):
    with bridge.network("test"):
        sender_contract.transfer(receiver_contract.address, sender=owner)

    with bridge.network("test"):
        assert receiver_contract.transfered

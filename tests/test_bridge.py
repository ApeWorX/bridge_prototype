import pytest


def test_bridge(bridge, owner, sender_contract, receiver_contract):
    with bridge.use_network("testnet1"):
        sender_contract.transfer(0, receiver_contract.address, sender=owner)

    with bridge.use_network("testnet2"):
        assert receiver_contract.transferrer() == sender_contract.address

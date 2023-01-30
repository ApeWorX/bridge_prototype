import pytest


def test_bridge(bridge, owner, sender_contract, receiver_contract):
    with bridge.use_network("A"):
        sender_contract.transfer(0, receiver_contract.address, sender=owner)

    with bridge.use_network("A"):
        assert receiver_contract.received()

import pytest


def test_bridge(bridge, owner, sender_contract, receiver_contract):
    with bridge.use(NETWORK_A) as provider:
        sender_contract.transfer(0, receiver_contract.address, sender=owner)

    with bridge.use(NETWORK_B) as provider:
        assert receiver_contract.received()

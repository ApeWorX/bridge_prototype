import pytest


def test_bridge(bridge, owner, sender_contract, receiver_contract):
    bridge.add_listener(
        sender_contract,
        sender_contract.Transfer,
        lambda: print("hello world"),
    )

    with bridge.use_network("testnet1") as provider:
        sender_contract.transfer(receiver_contract.address, sender=owner)

    with bridge.use_network("testnet2"):
        assert receiver_contract.transferrer() == sender_contract.address

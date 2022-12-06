import pytest


def test_bridge(bridge, owner, sender_contract, receiver_contract):
    bridge.add_listener(
        sender_contract,
        sender_contract.Transfer,
        lambda: print("hello world"),
    )

    with bridge.provider("test"):
        sender_contract.transfer(receiver_contract.address, sender=owner)

    # with bridge.provider("test"):
    # assert receiver_contract.transferrer() == sender_contract.address

# @version 0.3.7

event Transfer:
    sender: indexed(address)
    receiver: indexed(address)

@external
def transfer(to: address):
	log Transfer(msg.sender, to)

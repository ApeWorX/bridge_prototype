# @version 0.3.7

transferrer: public(address)

@external
def __init__():
	self.transferrer = empty(address)

@external
def receive(sender: address):
	self.transferrer = sender

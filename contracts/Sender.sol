pragma solidity ^0.8.17;

import {IConnext} from "@connext/core/connext/interfaces/IConnext.sol";

contract Sender {
	IConnext public immutable connext;

	constructor(IConnext _connext) {
		connext = _connext;
	}

	function transfer(uint32 destination, address target) external payable {
		connext.xcall{value: 0}(
			destination,
			target,
			address(0),
			msg.sender,
			0,
			0,
			"0x"
		);
	}
}

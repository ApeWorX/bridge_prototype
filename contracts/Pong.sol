pragma solidity ^0.8.17;

import {IConnext} from "@connext/core/connext/interfaces/IConnext.sol";
import {IXReceiver} from "@connext/core/connext/interfaces/IXReceiver.sol";

contract Pong is IXReceiver {
	uint256  public pings;
	IConnext public immutable connext;
	address  public immutable owner;
	uint32   public immutable authenticatedDomain;
	address  public immutable authenticatedSender;

	constructor(
		IConnext _connext,
		address _owner,
		uint32 _origin,
		address _sender
	) {
		connext = _connext;
		owner = _owner;
		authenticatedDomain = _origin;
		authenticatedSender = _sender;
	}

	modifier isAuthenticated() {
		require(msg.sender == owner);
		_;
	}

	modifier isBridgeAuthenticated(uint32 _origin, address _sender) {
		require(msg.sender == address(connext));
		require(_origin == authenticatedDomain, "Unauthorized origin domain");
		require(_sender == authenticatedSender, "Unauthorized origin sender");
		_;
	}

	function sendPong() external isAuthenticated() payable {
		connext.xcall{value: 0}(
			authenticatedDomain,
			authenticatedSender,
			address(0),
			msg.sender,
			0,
			0,
			"0x"
		);
	}

	function xReceive(
		bytes32 /* _transferId */,
	    uint256 /* _amount */,
	    address /* _asset */,
	    address _sender,
	    uint32 _origin,
	    bytes memory /* _callData */
	) external isBridgeAuthenticated(_origin, _sender) returns (bytes memory) {
		pings++;
	}
}

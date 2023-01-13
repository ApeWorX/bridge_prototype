pragma solidity ^0.8.17;

import {IConnext} from "@connext/core/connext/interfaces/IConnext.sol";
import {IXReceiver} from "@connext/core/connext/interfaces/IXReceiver.sol";

contract Receiver is IXReceiver {
	bool public received;

	function xReceive(
		bytes32 _transferId,
	    uint256 _amount,
	    address _asset,
	    address _originSender,
	    uint32 _origin,
	    bytes memory _callData
	) external {
		received = true;
	}
}

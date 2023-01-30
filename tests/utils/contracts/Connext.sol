pragma solidity ^0.8.17;

contract Connext {
	event XCalled();

	function xcall(
		uint32 _destination,
		address _to,
		address _asset,
		address _delegate,
		uint256 _amount,
		uint256 _slippage,
		bytes memory _callData
	) external payable returns (bytes32) {
	    emit XCalled();
	}
}

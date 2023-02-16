pragma solidity ^0.8.17;

struct TransferInfo {
    uint32 originDomain;
    uint32 destinationDomain;
    uint32 canonicalDomain;
    address to;
    address delegate;
    bool receiveLocal;
    bytes callData;
    uint256 slippage;
    address originSender;
    uint256 bridgedAmt;
    uint256 normalizedIn;
    uint256 nonce;
    bytes32 canonicalId;
}

contract Connext {
    uint256 internal nonce;
    uint32  internal domain;

    constructor(uint32 _domain) {
        domain = _domain;
    }

    event XCalled(
        bytes32 indexed transferId,
        uint256 indexed nonce,
        bytes32 indexed messageHash,
        TransferInfo params,
        address asset,
        uint256 amount,
        address local,
        bytes messageBody
    );

    function xcall(
        uint32 _destination,
        address _to,
        address _asset,
        address _delegate,
        uint256 _amount,
        uint256 _slippage,
        bytes memory _callData
    ) external payable returns (bytes32) {
        TransferInfo memory params = TransferInfo({
            to: _to,
            callData: _callData,
            originDomain: domain,
            destinationDomain: _destination,
            delegate: _delegate,
            receiveLocal: false,
            slippage: _slippage,
            originSender: msg.sender,
            nonce: nonce,
            canonicalDomain: 0,
            bridgedAmt: 0,
            normalizedIn: 0,
            canonicalId: bytes32(0)
        });

        emit XCalled(
            keccak256(abi.encode(params)),
            nonce,
            bytes32(0),
            params,
            _asset,
            _amount,
            // NOTE: Using null local asset address for demo
            address(0),
            bytes("")
        );

        nonce++;
    }
}

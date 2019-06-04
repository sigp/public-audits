pragma solidity ^0.4.24;

contract DOSContract  {

    // catch everything and consume all the gas
    function() payable {
        assert(1==2);
    }
}

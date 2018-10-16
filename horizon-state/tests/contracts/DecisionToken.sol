pragma solidity ^0.4.13;

import "./zeppelin-solidity/contracts/token/MintableToken.sol";
import "./zeppelin-solidity/contracts/math/SafeMath.sol";
import "./zeppelin-solidity/contracts/ownership/Claimable.sol";

/*
* Horizon State Decision Token Contract
*
* Version 0.9
*
* Author Nimo Naamani
*
* This smart contract code is Copyright 2017 Horizon State (https://Horizonstate.com)
*
* Licensed under the Apache License, version 2.0: http://www.apache.org/licenses/LICENSE-2.0
*
* @title Horizon State Token
* @dev ERC20 Decision Token (HST)
* @author Nimo Naamani
*
* HST tokens have 18 decimal places. The smallest meaningful (and transferable)
* unit is therefore 0.000000000000000001 HST. This unit is called a 'danni'.
*
* 1 HST = 1 * 10**18 = 1000000000000000000 dannis.
*
* Maximum total HST supply is 1 Billion.
* This is equivalent to 1000000000 * 10**18 = 1e27 dannis.
*
* HST are mintable on demand (as they are being purchased), which means that
* 1 Billion is the maximum.
*/

// @title The Horizon State Decision Token (HST)
contract DecisionToken is MintableToken, Claimable {

  using SafeMath for uint256;

  // Name to appear in ERC20 wallets
  string public constant name = "Decision Token";

  // Symbol for the Decision Token to appear in ERC20 wallets
  string public constant symbol = "HST";

  // Version of the source contract
  string public constant version = "1.0";

  // Number of decimals for token display
  uint8 public constant decimals = 18;

  // Release timestamp. As part of the contract, tokens can only be transfered
  // 10 days after this trigger is set
  uint256 public triggerTime = 0;

  // @title modifier to allow actions only when the token can be released
  modifier onlyWhenReleased() {
    require(now >= triggerTime);
    _;
  }


  // @dev Constructor for the DecisionToken.
  // Initialise the trigger (the sale contract will init this to the expected end time)
  function DecisionToken() MintableToken() {
    owner = msg.sender;
  }

  // @title Transfer tokens.
  // @dev This contract overrides the transfer() function to only work when released
  function transfer(address _to, uint256 _value) onlyWhenReleased returns (bool) {
    return super.transfer(_to, _value);
  }

  // @title Allow transfers from
  // @dev This contract overrides the transferFrom() function to only work when released
  function transferFrom(address _from, address _to, uint256 _value) onlyWhenReleased returns (bool) {
    return super.transferFrom(_from, _to, _value);
  }

  // @title finish minting of the token.
  // @dev This contract overrides the finishMinting function to trigger the token lock countdown
  function finishMinting() onlyOwner returns (bool) {
    require(triggerTime==0);
    triggerTime = now.add(10 days);
    return super.finishMinting();
  }
}

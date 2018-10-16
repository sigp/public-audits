pragma solidity ^0.4.13;

import "./DecisionToken.sol";
import "./zeppelin-solidity/contracts/ownership/Claimable.sol";
import './zeppelin-solidity/contracts/token/MintableToken.sol';
import './zeppelin-solidity/contracts/math/SafeMath.sol';

/**
* Horizon State Token Sale Contract
*
* Version 0.9
*
* @author Nimo Naamani
*
* This smart contract code is Copyright 2017 Horizon State (https://Horizonstate.com)
*
* Licensed under the Apache License, version 2.0: http://www.apache.org/licenses/LICENSE-2.0
*
*/

// @title The Decision Token Sale contract
// @dev A crowdsale contract with stages of tokens-per-eth based on time elapsed
// Capped by maximum number of tokens; Time constrained
contract DecisionTokenSale is Claimable {
  using SafeMath for uint256;

  // Start timestamp where investments are open to the public.
  // Before this timestamp - only whitelisted addresses allowed to buy.
  uint256 public startTime;

  // End time. investments can only go up to this timestamp.
  // Note that the sale can end before that, if the token cap is reached.
  uint256 public endTime;

  // Presale (whitelist only) buyers receive this many tokens per ETH
  uint256 public constant presaleTokenRate = 3750;

  // 1st day buyers receive this many tokens per ETH
  uint256 public constant earlyBirdTokenRate = 3500;

  // Day 2-8 buyers receive this many tokens per ETH
  uint256 public constant secondStageTokenRate = 3250;

  // Day 9-16 buyers receive this many tokens per ETH
  uint256 public constant thirdStageTokenRate = 3000;

  // Maximum total number of tokens ever created, taking into account 18 decimals.
  uint256 public constant tokenCap =  10**9 * 10**18;

  // Initial HorizonState allocation (reserve), taking into account 18 decimals.
  uint256 public constant tokenReserve = 4 * (10**8) * 10**18;

  // The Decision Token that is sold with this token sale
  DecisionToken public token;

  // The address where the funds are kept
  address public wallet;

  // Holds the addresses that are whitelisted to participate in the presale.
  // Sales to these addresses are allowed before saleStart
  mapping (address => bool) whiteListedForPresale;

  // @title Event for token purchase logging
  event TokenPurchase(address indexed purchaser, uint256 value, uint256 amount);

  // @title Event to log user added to whitelist
  event LogUserAddedToWhiteList(address indexed user);

  //@title Event to log user removed from whitelist
  event LogUserUserRemovedFromWhiteList(address indexed user);


  // @title Constructor
  // @param _startTime: A timestamp for when the sale is to start.
  // @param _wallet - The wallet where the token sale proceeds are to be stored
  function DecisionTokenSale(uint256 _startTime, address _wallet) {
    require(_startTime >= now);
    require(_wallet != 0x0);
    startTime = _startTime;
    endTime = startTime.add(14 days);
    wallet = _wallet;

    // Create the token contract itself.
    token = createTokenContract();

    // Mint the reserve tokens to the owner of the sale contract.
    token.mint(owner, tokenReserve);
  }

  // @title Create the token contract from this sale
  // @dev Creates the contract for token to be sold.
  function createTokenContract() internal returns (DecisionToken) {
    return new DecisionToken();
  }

  // @title Buy Decision Tokens
  // @dev Use this function to buy tokens through the sale
  function buyTokens() payable {
    require(msg.sender != 0x0);
    require(msg.value != 0);
    require(whiteListedForPresale[msg.sender] || now >= startTime);
    require(!hasEnded());

    // Calculate token amount to be created
    uint256 tokens = calculateTokenAmount(msg.value);

    if (token.totalSupply().add(tokens) > tokenCap) {
      revert();
    }

    // Add the new tokens to the beneficiary
    token.mint(msg.sender, tokens);

    // Notify that a token purchase was performed
    TokenPurchase(msg.sender, msg.value, tokens);

    // Put the funds in the token sale wallet
    wallet.transfer(msg.value);
  }

  // @dev This is fallback function can be used to buy tokens
  function () payable {
    buyTokens();
  }

  // @title Calculate how many tokens per Ether
  // The token sale has different rates based on time of purchase, as per the token
  // sale whitepaper and Horizon State's Token Sale page.
  // Presale:  : 3750 tokens per Ether
  // Day 1     : 3500 tokens per Ether
  // Days 2-8  : 3250 tokens per Ether
  // Days 9-16 : 3000 tokens per Ether
  //
  // A note for calculation: As the number of decimals on the token is 18, which
  // is identical to the wei per eth - the calculation performed here can use the
  // number of tokens per ETH with no further modification.
  //
  // @param _weiAmount : How much wei the buyer wants to spend on tokens
  // @return the number of tokens for this purchase.
  function calculateTokenAmount(uint256 _weiAmount) internal constant returns (uint256) {
    if (now >= startTime + 8 days) {
      return _weiAmount.mul(thirdStageTokenRate);
    }
    if (now >= startTime + 1 days) {
      return _weiAmount.mul(secondStageTokenRate);
    }
    if (now >= startTime) {
      return _weiAmount.mul(earlyBirdTokenRate);
    }
    return _weiAmount.mul(presaleTokenRate);
  }

  // @title Check whether this sale has ended.
  // @dev This is a utility function to help consumers figure out whether the sale
  // has already ended.
  // The sale is considered done when the token's minting finished, or when the current
  // time has passed the sale's end time
  // @return true if crowdsale event has ended
  function hasEnded() public constant returns (bool) {
    return token.mintingFinished() || now > endTime;
  }

  // @title White list a buyer for the presale.
  // @dev Allow the owner of this contract to whitelist a buyer.
  // Whitelisted buyers may buy in the presale, i.e before the sale starts.
  // @param _buyer : The buyer address to whitelist
  function whiteListAddress(address _buyer) onlyOwner {
    require(_buyer != 0x0);
    whiteListedForPresale[_buyer] = true;
    LogUserAddedToWhiteList(_buyer);
  }

  // @title Whitelist an list of buyers for the presale
  // @dev Allow the owner of this contract to whitelist multiple buyers in batch.
  // Whitelisted buyers may buy in the presale, i.e before the sale starts.
  // @param _buyers : The buyer addresses to whitelist
  function addWhiteListedAddressesInBatch(address[] _buyers) onlyOwner {
    require(_buyers.length < 1000);
    for (uint i = 0; i < _buyers.length; i++) {
      whiteListAddress(_buyers[i]);
    }
  }

  // @title Remove a buyer from the whitelist.
  // @dev Allow the owner of this contract to remove a buyer from the white list.
  // @param _buyer : The buyer address to remove from the whitelist
  function removeWhiteListedAddress(address _buyer) onlyOwner {
    whiteListedForPresale[_buyer] = false;
  }

  // @title Terminate the contract
  // @dev Allow the owner of this contract to terminate it
  // It also transfers the token ownership to the owner of the sale contract.
  function destroy() onlyOwner {
    token.finishMinting();
    token.transferOwnership(msg.sender);
    selfdestruct(owner);
  }
}

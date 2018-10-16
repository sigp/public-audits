# Horizon State Token Contract Audit

## Overview

Sigma Prime were commercially engaged by Horizon State to perform a public audit on the smart contracts used for the HST Token crowd sale.

This public document is the deliverable of the audit engagement.

## Summary

The contract as a whole produces the desired functionality specified and has no known major external vulnerabilities. 

There is a moderate vulnerability which could cause an inflated token total supply if Horizon State become malicious. Horizon State are aware of this and such an attack would be highly visible. 

It is possible for Horizon State to prevent the trading of the token after the token sale has ended. Horizon State are aware of this and express that such a scenario is not in their interests.

### Contract use-case

The series of solidity files contained within this audit aim to create a crowd sale contract for Horizon State whereby a resulting ERC20 token, known as a `Decision Token` (`HST`), divisible to 18 decimal places, is created from the crowd sale.

The `DecisionTokenSale` contract (token sale contract) will be deployed on the Ethereum mainnet, which will immediately perform the following actions:

 - Declare that the address which created the token sale contract is the owner of the contract. The owner may delegate another owner at any point in the future.
 - Create a new `DecisionToken` contract (token contract) and store the address of this new contract.
 - In the newly created token contract, mint `400,000,000 * 10^18` tokens into the control of the owner address.

In the creation of the token sale contract, a start time is specified. An end time is then defined as 14 days after the start time.

Before the start time arrives, an address may purchase tokens only if "white listed" by the contract owner. Once white listed, an account may purchase as many tokens as desired until one of the following conditions are met:

 1. The account is removed from the white list by the owner before the start time is reached
 2. The end time is reached
 3. The token cap of `1,000,000,000 * 10^18` is reached
 4. The owner finishes the token sale by calling the `finishMinting()` function

Once the start time has arrived, any account will now be able to purchase tokens until the above conditions (2), (3) or (4) are met.

Purchasing tokens is achieved by sending ether (ETH) to the contract whilst calling the `buyTokens()` function. Sending ether (ETH) without specifying a function will also cause the purchase of tokens.

The amount of tokens received is always determined by the amount of ether (ETH) sent, and the block time stamp. The purchasing power of `1 ETH` is documented below.

 - If the current block time is before the start time, `1 ETH` will purchase `3750 * 10^18` tokens.
 - If the current block time is less than 1 day after the start time, `1 ETH` will purchase `3500 * 10^18`
 - If the current block time is more than 1 day after the start time and less than 8 days since the start time, `1 ETH` will purchase `3250 * 10^18`
 - If the current block time is equal to or more than 8 days since the start time, `1 ETH` will purchase `3000 * 10^18`

During the token sale period, it is not possible to transfer tokens. The owner of the contract _must_ call the `finishMinting()` function, after which there is a 10 day delay before transfer is possible.

### Files audited

The files audited were obtained from the [HorizonState/token-sale Github Repository](https://github.com/HorizonState/token-sale) at the commit hash of `178033f05ee5e72d9dfa464dccac4abc767dca6b`. This commit is dated the 19th of September 2017.

The following directory tree shows which Solidity `.sol` files were the subject of the audit:

```
├── DecisionTokenSale.sol
├── DecisionToken.sol
└── zeppelin-solidity
    └── contracts
        ├── math
        │   └── SafeMath.sol
        ├── ownership
        │   ├── Claimable.sol
        │   └── Ownable.sol
        └── token
            ├── BasicToken.sol
            ├── ERC20Basic.sol
            ├── ERC20.sol
            ├── MintableToken.sol
            └── StandardToken.sol
```

_Note: The `zepplin-solidity/contracts/crowd sale/Crowdsale.sol` file was excluded as there was no reference to this contract in the `DecisionTokenSale.sol` contract._

### ERC20 Implementation

The `DecisionToken.sol` contract is ERC20-compliant, and implements the following interfaces:

  1. `function allowance(address owner, address spender) constant returns (uint256);`
  2. `function approve(address spender, uint256 value) returns (bool);`
  3. `function balanceOf(address who) constant returns (uint256);`
  4. `function transferFrom(address _from, address _to, uint256 _value) onlyWhenReleased returns (bool);`
  5. `function transfer(address _to, uint256 _value) onlyWhenReleased returns (bool);`

When a transfer or approval is not successful, a `throw` is generated. Otherwise, `true` is always returned.

The owner is unable to mint new tokens after the `finishMinting()` function has been called, therefore the token will be 'fixed-supply' after that function call.

The `totalSupply` variable is updated each time an account buys tokens.

*At any point the owner may call the `finishMinting()` function and prohibit ERC20 transfers for 10 days. If called repeatedly, transfers would be stopped permanently.*

## Recommendations

### Severe

We found nothing that we would classify as severe.

### Moderate


**M1: DecisionTokenSale.sol [100] - [121]** - The function `buyTokens()` allows the owner of the `wallet` address to essentially create as many tokens as they like up to the token cap, for free. The owner of the `wallet` address may send ETH to an arbitrary address (or series of addresses), which in turn calls `buyTokens()`. The calling address will then be credited with tokens, whilst the ETH is immediately sent back to the `wallet` address and the process can repeat.
This allows artificial creation of tokens whereby the owner of the `wallet` address can essentially dilute the investment of real crowd sale investors. As the number of tokens minted no longer corresponds to the amount of ETH invested in the crowd sale, investors should be weary about estimating market cap and potential dilution by the `wallet` owner.

We suggest a withdraw pattern, whereby the owner of the `wallet` address can withdraw the total ETH invested in the crowd sale after it's completion. This ensures that the tokens bought in the crowd sale correspond to a fixed amount of ETH invested.

* [x] Horizon State have acknowledged this attack vector and find it acceptable within their business model. If Horizon State were to execute this attack it would be publicly visible on the blockchain. Furthermore, it is a 'malicious owner' attack and their business model assumes an honest owner. Sigma Prime do not make any judgements on the Horizon State business model as it is out of scope.

**M2: DecisionToken.sol [85]** - The function `finishMinting()` can be called by the owner at any given time. This resets `triggerTime` to `now`, which prevents all transfers of any token for the following 10 days. This means the owner, or someone who has access to the owner's keys (at any time in the future), can stop all token transfers indefinitely through repeated calls to this function. Furthermore, the owner can finish the sale early, by calling `destroy()` in **DecisionTokenSale.sol [205]** within 4 days of the contract creation, allowing transfers earlier than the 14 days implied in the crowd sale documentation. Thus tokens can be come transferable >= 10 days after the start of the crowd sale at the owners discretion. Initially the owner is the parent DecisionTokenSale contract, however upon `destroy()` this becomes the creator of the contract allowing the above attack at any time in the future.

* [x] Fixed in commit `b2589cf`

**M3: DecisionTokenSale.sol [80]** - There is an unchecked over-flow possible here. If a sufficiently high `_startTime` is supplied. An over-flow could result in `endTime` < `now`, in which case `hasEnded()` will always be true and `validPurchase()` will never be true. Ultimately, an incorrect `_startTime` can render the crowd sale useless.  

* [x] Fixed in commit `b2589cf`

### Low

**L1: DecisionTokenSale.sol [205]** - The `destroy()` function can only be called by the `owner`. This opens up the possible scenario that if the owner loses their keys, the tokens that the investors have bought become unusable (as they cannot be transferred until `finishMinting()` has been called). Creating a separate function allowing any participant to call `finishMinting()` after the crowd sale end date can mitigate this unlikely scenario. Furthermore, it is possible that the owner intentionally never calls `destroy()` and thus never releases the investors tokens, as the current contract design already withdraws all the ETH as it is deposited. Typically, inside such a `destroy()` function, the total ETH invested would be transferred to the `wallet` address (see the issue listed in the severe category) giving a game-theoretic motivation for the owners to release the tokens (i.e. the owners only get the invested ETH once the tokens are released and able to be traded).

* [x] Horizon State have acknowledged this recommendation and communicated that they intend to use the history of the blockchain to rebuild a new token contract in the case of a lost `owner` private key. Refusal to call `destroy()` is a 'malicious owner' attack and the Horizon State business model assumes an honest owner. Sigma Prime do not make any judgements on the Horizon State business model as it is out of scope.

**L2: DecisionTokenSale.sol [136]** - The `validPurchase()` function is only called once in the `buyTokens()` function **[102]**, inside a `require()` statement. It may be simpler to read if the `validPurchase()` function was removed, and it's logic replaced by a series of `require()` statements in the `buyTokens()` function. The multiple `AND` one-liner on **[139]** seems unnecessarily complex and prone to human error.

* [x] Fixed in commit `b2589cf`

**L3: DecisionTokenSale.sol [104]** - The variable `weiAmount` is unnecessary and its initialisation just costs investors small amounts of extra gas when investing.

* [x] Fixed in commit `0f40bb6`

### General Suggestions

**G1: DecisionToken.sol [65]** - The DecisionToken contract does not need the `_triggerTime` parameter in the constructor. Setting the `triggerTime` state variable in the constructor is redundant, as it is only used in the `onlyWhenReleased` modifier which also checks for `mintingFinished`. The only case where `require(mintingFinished)` passes, is if `finishMinting()` is called, which itself sets the `triggerTime` state variable. I.e. there is no case where the `triggerTime` set in the constructor is tested.

* [x] Fixed in commit `0f40bb6`

**G2: DecisionToken.sol [73]** - By overloading an ERC20 function, you change the expected gas cost of the interface function. Therefore future external applications utilizing your token, could potentially run into issues if they assume the standard gas amount of the function. Furthermore, every transfer in the history of your token will now spend gas to check if `mintingFinished` is true and that `now > triggerTime`. Although this amount is insignificant for a single transaction, this is not an insignificant amount when summed across all transfers ever completed on this contract. We typically opt for a withdraw pattern which is available after the crowd sale, which moves the tokens into the ERC20 balance mapping, thus leaving the ERC20 Transfer function standard.

* [x] Commit `0f40bb6` reduces the gas used in the ERC20 functions. Whilst the functions do not use standard gas, Horizon State deems this to be fit for purpose.


**G3: DecisionTokenSale.sol [151]** - The function `calculateTokenAmount()` uses an exchange rate per ETH (according to the comments), yet is multiplied by an amount in wei (`_weiAmount`). There are semantics here in the variable naming. To be consistent with **DecisionTokenSale.sol [48] [51]**, which gives `tokenCap` and `tokenReserve` integers that include the concept of `decimals`, the tokenRates should also include `decimals`. This means, that for generic `decimals` the tokenRates should be calculated as `tokenRate_per_ETH*10^decimals`. In this very specific case, where `decimals = 18` which is the exact ratio of wei/ETH, the tokenRate can be converted to tokens per wei with the value unaltered. For this reason we suggest the comments change to reflect this.
Typically the `decimals` variable should be used in either the calculation of the exchangeRates or in the calculation of number of tokens i.e. in `calculateTokenAmount()`. As this case cancels with the conversion between ETH to wei, it is not necessary, however we point out that errors can arise easily if `decimals` is modified in future versions as it is not accounted for in the token calculations and the current calculations are only valid if and only if `decimals == 18`.

* [x] Fixed in commit `b2589cf`

### General Suggestions following revisions at commit `b2589cf`

**R1: DecisionToken.sol [53]** - The initialisation of this state variable to zero costs approximately 5000 gas. Regardless of the explicit initialisation the variable will be set to zero, without the ~5000 gas cost. As this only happens once during the deployment of the contract, the cost is negligible and raises no security risk.

**R2: DecisionTokenSale.sol [160]** - Checking for `token.mintingFinished()` is redundant as it can never be `true` in the context of this contract. This is because `destroy()` must be called before `token.mintingFinished()` could return `true`, however after this point the contract is destroyed. This poses no security risk and an negligibly small amount of gas usage.


## Tests

A number of unit tests were created to verify the functionality of the token contract. Specifically we tested each case of the purchasing periods to verify the correct amount of tokens and the exchange rates were given, the ownership functionality worked as expected, the ERC20 interface performs as expected and the constructor of the contracts performed as expected.

The tests were built based on the [Truffle](http://truffleframework.com/) framework which implements [Mocha](https://mochajs.org/).

To run the tests, install `testrpc` and `truffle`. From the `tests/` directory, run
```
$ ./largeTestAccounts.sh &
$ truffle test
```
To initialise a local testRPC instance, and initialise the truffle unit tests.

The result of the tests currently pass with the following output:

```
  Contract: DecisionTokenSale (constructor)
    ✓ should create a new token contract (154ms)
    ✓ should give reserve tokens to the owner (224ms)

  Contract: DecisionTokenSale (transferOwnership)
    ✓ should not allow a non-owner to transfer ownership (392ms)
    ✓ should allow an owner to transfer ownership (515ms)

  Contract: ENTToken (standardToken)
    ✓ transfers: ether transfer should be reversed. (1349ms)
    ✓ transfers: should transfer 7000 to accounts[1] with accounts[0] having 7000 (1396ms)
    ✓ transfers: throw when trying to transfer 7001 to accounts[1] with accounts[0] having 7000 (1292ms)
    ✓ transfers: should not allow zero-transfers (253ms)
    ✓ approvals: msg.sender should approve 100 to accounts[1] (1403ms)
    ✓ approvals: msg.sender approves accounts[1] of 100 & withdraws 20 once. (1667ms)
    ✓ approvals: msg.sender approves accounts[1] of 100 & withdraws 20 twice. (1616ms)
    ✓ approvals: msg.sender approves accounts[1] of 100 & withdraws 50 & 60 (2nd tx should fail) (1531ms)
    ✓ approvals: attempt withdrawal from account with no allowance (should fail) (1294ms)
    ✓ approvals: allow accounts[1] 100 to withdraw from accounts[0]. Withdraw 60 and then approve 0 & attempt transfer and throw. (287ms)
    ✓ approvals: approve max (2^256 - 1) (1307ms)
    ✓ events: should fire Transfer event properly (1259ms)
    ✓ events: should fire Approval event properly (1298ms)

  Contract: DecisionTokenSale (Create Tokens)
    ✓ should create 7.5e+23 from a 200 Eth deposit in the pre-sale (681ms)
    ✓ should create 1.12896e+23 from a 32.256 Eth deposit in the first day (642ms)
    ✓ should create 1462500000000000000 from a 0.00045 Eth deposit in the second stage (651ms)
    ✓ should create 6.9e+22 from a 23 Eth deposit in the third stage (650ms)
    ✓ should not allow purchases after 14 days (724ms)
    ✓ should not allow more than 1e+27 tokens to be produced. (1818ms)


  23 passing (23s)
```


## Audit information

### Limitations

Sigma Prime makes all effort, but holds no responsibility for the findings of this audit. Sigma Prime does not provide any guarantees relating to the function of the smart contract. Sigma Prime makes no judgements on, or provides audit on, the viability of the token sale, the underlying business model or the individuals involved in the token sale.

The procedures that we will perform will not constitute an audit or a review in accordance with Australian
Auditing Standards and, consequently, no assurance will be expressed. 

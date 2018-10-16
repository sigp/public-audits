# Skrilla Token Contract Audit

## Overview

Sigma Prime were commercially engaged by Skrilla to perform a public audit on the smart contracts used for the SKR Token crowd sale.

This public document is the deliverable of the audit engagement.

## Summary

The contract as a whole produces the desired functionality specified and has no known major external vulnerabilities.

## Contract use-case

The SkrillaToken contract constitutes a token sale to purchase an ERC20-compatible token, SKR. The token sale has two periods, the starts of which are defined by whomever creates the contract. These two periods are called the "pre sale" period and the "sale" period.

The pre sale period runs for a total of 3 days. In the first day 1 ETH purchases 3000 SKR, in the following two days 1 ETH purchases 2500 SKR.

The sale period runs for a total of 14 days. In the first day 1 ETH purchases 2400 SKR, in the following six days 1 ETH purchases 2200 SKR, and in the final seven days 1 ETH purchases 2000 SKR.

The above exchange rates do not apply if an address is "white listed". White listing happens at the discretion of the owner of the contract (the address who created the contract), and allows an address to have a custom exchange rate between 1 and 10,000 SKR/ETH. Furthermore, the white listed buyer is able to purchase tokens at any time, until 14 days after the sale starts. After this point, no address may purchase tokens and the contract becomes fixed-supply.

There is a 14 day period after the sale ends (28 days after the sale starts) in which no token transfers are permitted. After this period, the address which created the contract is then able transfer the entire ETH balance of the contract to themselves.

After an address invests, and before it is able to use the `transfer()` or `transferFrom()` functions, it must call the `withdraw()` function.

_Note: all SKR amounts mentioned in this section assume a decimal places of 6. I.e., the amount shown in the `balances` mapping will be 10^6 times larger than the amount stated here._

### Files audited

The files audited were obtained from a private [Bitbucket repository](https://bitbucket.org/getskrilla/skrilla-smart-contract) at the commit hash of `1932e8b72ab58489012098fe3d891c58637d14e7` dated 16th October 2017. 

Two previous audits were conducted:

 1. Commit hash `e449846964c4d13cfa4b713a127422ea0a68a20f` dated the 4th of October 2017.
 2. commit hash `037efbeb7802f244f831b36332f3091a242ecf03` dated the 12th October 2017. 

The following flat directory tree shows which Solidity `.sol` files were the subject of the audit:

```
├── ERC20.sol
├── SafeMath.sol
└── SkrillaToken.sol
```

### ERC20 Implementation

The token implements the [ERC20 Token Standard](https://github.com/ethereum/EIPs/blob/master/EIPS/eip-20-token-standard.md) with the following interfaces:

  1. `function allowance(address _owner, address _spender) constant returns (uint remaining);`
  2. `function approve(address _spender, uint _amount) returns (bool success);`
  3. `function balanceOf(address _owner) constant returns (uint256 balance);`
  4. `function transferFrom(address _from, address _to, uint256 _value) returns (bool success);`
  5. `function transfer(address _to, uint256 _value) returns (bool);`

When a transfer or approval is not successful, a `throw` is generated. Otherwise, `true` is always returned.

The owner becomes unable to mint new tokens 22 days after the sale starts, therefore the token will be 'fixed-supply' after that time.

The `totalSupply` variable is updated each time an account buys tokens.

Investors must call the `withdraw()` function after the sale has ended to be able to transfer their tokens.

## Recommendations

### Severe

**S1: SkrillaToken.sol [93]** - The cap of 150,000 ETH can be negated through the owner calling `withdrawal()`. The `withdrawal()` function can be called at any time and would reset `this.balance` to zero.
 * [x] Fixed in `037efbe`

**S2: SkrillaToken.sol [93]** - An attacker (potentially the owner of `withdrawAddress`) can end the token sale early by artificially increasing `this.balance`. Any user can forcibly send ether to this contract, either by having ether pre-sent to the contract address or by the use of a `selfdestruct()` call. This means that `this.balance` can be set arbitrarily high, without tokens being created, and therefore artificially reaching the cap. A better approach is to use an internal variable that keeps track of ether invested opposed to `this.balance`.
 * [x] Fixed in `037efbe`

**S3: SkrillaToken.sol [112]** - The owner is assigned all tokens (regardless of how many are bought in the crowd sale), and is then unable to utilize the tokens (i.e. cannot transfer), due to require statements prohibiting the transfer of the tokens on **[138]** and **[149]**. This renders these created tokens unusable, essentially giving a misrepresented `totalSupply`.
The current mechanism violates what is dictated in the "Token Sale Particulars" document which reads: `The total Token supply at the completion of the Token Sale will depend on the number of Purchased tokens sold...`. The current implementation has a fixed token supply, regardless of purchased tokens. It also violates the following line in the Token Sale Particulars document, which reads `Unsold Tokens from this budget will not be created`.

A simpler and more accurate realisation of the Token Sale Particulars document, would be to simply not create the tokens for the owner in the first place, and omit line **[217]** where the owners balance is reduced. In this case, `totalSupply` would need to be updated to reflect the true amount of tokens created. The checks on **[138]** and **[149]** are gas costs which must be paid for every single transfer in the future and should ideally be avoided. Furthermore, an incremented `totalSupply` would negate the need for `tokensSold` as `totalSupply` could be used for the counter.
 * [x] Fixed in `037efbe`

**S4: SkrillaToken.sol [102]-[103]** - Using the balances mapping, means that the addresses `team` and `growth` are able to transfer their tokens during the sale.
 * [x] Fixed in `1932e8b`

### Moderate

**M1: SkrillaToken.sol** - The contract does not inherit the `Ownable` contract which defines a number of useful functions typically related to contracts that have owners. One function in particular is the `transferOwnership()` function. If this contract for some reason has its owner's keys compromised, the contract is at the mercy of the attacker. However, if a `transferOwnership()` function were implemented, this would create an even greater attack, where the owner could transfer ownership to someone else, and then withdraw/transfer the entire `SALE_CAP` worth of tokens given to them in the constructor. Again we recommend that tokens be `minted` when bought rather than subtracted from an ad hoc unusable store (in this case, the `owner` account).
 * [x] Addressed in `037efbe`: the owner is no longer allocated `SALE_CAP` tokens and Skrilla have chosen not to implement transfer of contract ownership as the owner is only privileged during the pre sale.

**M2: SkrillaToken.sol [48]** - Possibility of an undetected overflow if the constants are defined as high enough integers.
 * [x] Fixed in `037efbe`

**M3: SkrillaToken.sol [87]** - The `inSalePeriod()` returns true if the contract is in the sale period, or the pre sale period. The naming of the function is misleading, as it will return true whilst `now` is not within the range of `getSaleStart()` and `getSaleEnd()`.
 * [x] Fixed in `037efbe`

**M4: SkrillaToken.sol [124]** - Possibility of overlapping `saleStageStartDates` if `_saleStart` is not adequately higher than `_presaleStart`.
 * [x] Fixed in `037efbe`

**M5: SkrillaToken.sol [126-132]** - Possibility of overflows in the  `saleStageStartDates` if `_saleStart` or `_presaleStart` are adequately high.
 * [x] Fixed in `037efbe`

**M6: SkrillaToken.sol [137]** `transfer()` - This implementation allows users to accidentally send tokens to the `0x0` which can happen by inadvertently by not entering an address into some interfaces. This is also the case for the `transferFrom()` function.
 * [x] Fixed in `037efbe`

**M7: SkrillaToken.sol [229]** - The owner of `withdrawAddress` could create as many tokens as they like up to the token cap, for free. The `withdrawAddress` may call `buyTokens()`, then `withdrawal()` over and over again, each time being credited with the tokens and then receiving a full refund. This allows artificial creation of tokens whereby the owner of the `withdrawAddress` can essentially dilute the investment of real crowd sale investors. As the number of tokens minted no longer corresponds to the amount of ETH invested in the crowd sale, investors should be weary about estimating market cap and potential dilution by the `wallet` owner.
 * [x] Fixed in `037efbe`

**M8: SkrillaToken.sol [205, 227]** - There is inconsistency in the use of SafeMath between these to statements. On [205] we assume an overlfow is impossible, but on [227] we protect against it. We reccomend using SafeMath in both cases.
 * [x] Fixed in `1932e8b`

**M9: SkrillaToken.sol [224, 226]** - As in **M8**, there is inconsistency in the use of SafeMath between these to statements. On [224] we assume an overlfow is impossible, but on [226] we protect against it. We reccomend using SafeMath in both cases.
 * [x] Fixed in `1932e8b`

### Low

**L1: SkrillaToken.sol [7]** - The correct type for decimals is `uint8` as per the Ethereum wiki [ERC20 Token Standard](https://github.com/ethereum/EIPs/blob/master/EIPS/eip-20-token-standard.md). Due to the exponential nature of the `decimals` variable it need only be a small integer.
 * [x] Fixed in `037efbe`

**L2: SkrillaToken.sol [9]** - The convention for passing ERC20 meta data is to use `string public constant name = "Skrilla"`. Solidity will automatically create a public getter function `name()` which saves the use of the unnecessary private variable `NAME` and removes the need for lines **[39] - [41]**. The same can be done for `totalSupply()`. The same should be done for `tokensSold`. Line **[28]** should be changed to `uint256 public tokensSold;`, which would allow lines **[67]-[69]** to be removed and the reference to `getTototalSold()` in line **[93]** to be replaced simply by, `tokensSold`.
 * [x] Fixed in `037efbe`

**L3: SkrillaToken.sol [48], [79], [93], [112]-[114], [218]** - Typically the number of tokens are inclusive of decimal places, indicated by `decimals`. The `decimals` variable is used by GUI interfaces to display the tokens, but the tokens themselves should defined inclusive of these decimals, as solidity as of yet does not handle floats. This means that `SALE_CAP`, `TEAM_TOKENS` and `GROWTH_TOKENS` should be multiplied by `10 ** decimals`. This means all multiplications of these throughout this contract can be removed saving excess gas costs.  
 * [x] Fixed in `037efbe`

**L4: SkrillaToken.sol [47]** - `totalSupply` typically represents an incrementing counter as tokens are minted. This is similar to **S3** but from the point-of-view of ERC20 implementation.
 * [x] Fixed in `037efbe`

**L5: SkrillaToken.sol [83], [88]** - There is inconsistencies with the dates at which sales end. The sale end date uses `<=` implying that the time corresponding to `getSaleEnd()` is valid for the sale period, however `<` is used for `getPreSaleEnd()`, implying the time corresponding to this is not valid. Thus, we have the scenario (when `now = getSaleEnd()`), where `inSalePeriod()` is true, but `buyTokens()` will throw, because of the inconsistent require on line **[201]**.
 * [x] Fixed in `037efbe`

**L6: SkrillaToken.sol [190]** - If the owner was to purchase tokens, the owner would be debited the amount of tokens purchased, then credited the amount and then finally unable to transfer the tokens. The net result would be an increased amount of ETH held by the smart contract, an increased `tokensSold` an no more actual tokens able to be transferred. This allows the owner to artificially end the crowd sale early.
 * [x] Fixed in `037efbe`

**L7: SkrillaToken.sol [218]** This requirement uses `<` which ensures that `SALE_CAP` can never be reached. This should be `<=` in order to sell the entire `SALE_CAP` worth of tokens.
 * [x] Fixed in `037efbe`

**L8: SkrillaToken.sol [93]-[96]** - These require() statements do not effectively check for overflows; an overflow will "wrap around". There is no need for these three statements, unless you are checking they have been set to zero.
 * [x] Fixed in `1932e8b`

**L9: SkrillaToken.sol [214]** - This variable is not needed, gas can be reduced by replacing `amountInWei` simply with `msg.sender`.
 * [x] Fixed in `1932e8b`


### General Suggestions

Modifiers help save gas costs (calls to constant functions cost more). Some functions here can be replaced by modifiers. One example is `capReached()`. These functions are used to check a state and the contract throws if not checked. For example, the `capReached()` function could be converted to an `underCap()` modifier which could be applied to the `buyTokens()` function. Modifiers such as the `onlyOwner` modifier can also be used instead of repeating the `require(msg.sender == owner)` logic.

**G1: SkrillaToken.sol** - Specifically state the visibility modifers for functions to clarify their intention, as has been done with state variables.
 * [x] Fixed in `1932e8b`

**G2: SkrillaToken.sol [19]-[21]** - To make these numbers easier to read, we suggest splitting them out like `600 * 10**6 * 10**decimals`. Solidity also allows for scientific notation of the form `6e8`
 * [x] Fixed in `037efbe`

**G3: SkrillaToken.sol [137, 148]** - By having specific `require()` statements in the `transfer()` function, means that every transfer in the history of your token will now spend gas to check if `now > getSaleEnd() + 14 days`. Although this amount is insignificant for a single transaction, this is not an insignificant amount when summed across all transfers ever completed on this contract. We typically opt for a withdraw pattern which is available after the crowd sale, which moves the tokens into the ERC20 balance mapping, thus removing the excess gas usage from ERC20 Transfer function.
 * [x] Fixed in `037efbe`

**G4: SkrillaToken.sol [173]** - In `addToWhiteList()`, renaming the `_amount` variable to `_price` would provide more clarity for code readers.
 * [x] Fixed in `037efbe`

**G5: SkrillaToken.sol [235]** - The `enableToSaleTime` modifier is not used anywhere.
 * [x] Fixed in `037efbe`

**G6: SkrillaToken.sol** - Specify the types for `uint`. I.e replace all `uint` with `uint256` (which is the type solidity compiles `uint` into).
 * [x] Fixed in `1932e8b`

## Tests

A number of unit tests were created to verify the functionality of the token contract. Specifically we tested each case of the purchasing periods to verify the correct amount of tokens and the exchange rates were given, the whitelist functionality worked as expected, the team, owner and growth accounts were debited the correct token balance, the ERC20 interface performs as expected and the constructor of the contracts performed as expected.

The tests were built based on the [Truffle](http://truffleframework.com/) framework which implements [Mocha](https://mochajs.org/).

To run the tests, install `testrpc` and `truffle`. From the `tests/` directory, run
```
$ ./largeTestAccounts.sh &
$ truffle test
```
To initialise a local testRPC instance, and initialise the truffle unit tests.

The result of the tests currently pass with the following output:

```
  Contract: SkrillaToken (constructor)
    ✓ the contract should deploy without errors (346ms)
    ✓ the contract should not deploy if saleStart is < 3 days after presaleStart (299ms)

  Contract: SkrillaToken (exchangeRates)
    ✓ should return an exchange rate of 3000 SKR/ETH half a day after presale start (865ms)
    ✓ should return an exchange rate of 2500 SKR/ETH one and a half a days after presale start (876ms)
    ✓ should return an exchange rate of 2400 SKR/ETH half a day after sale start (845ms)
    ✓ should return an exchange rate of 2200 SKR/ETH two days after sale start (835ms)
    ✓ should return an exchange rate of 2000 SKR/ETH 8 days after sale start (852ms)
    ✓ should allow a whitelisted exchange rate of 8000 (901ms)

  Contract: SkrillaToken (skrilla tokens)
    ✓ the team address should receive 100 * Math.pow(10, 12) tokens (967ms)
    ✓ the growth address should receive 300 * Math.pow(10, 12) tokens (978ms)
    ✓ the withdraw address should receive 0 tokens (925ms)
    ✓ the withdraw address should be able to retrieve the invested ETH (1306ms)

  Contract: SkrillaToken (timeBounds)
    ✓ should permit a whitelisted account before the presale starts (531ms)
    ✓ should not permit a non-whitelisted account before the presale starts (423ms)
    ✓ should not permit token purchase after the sale ends (361ms)

  Contract: SkrillaToken (standardToken)
    ✓ transfers: ether transfer should be reversed. (383ms)
    ✓ transfers: should transfer 10000 to accounts[1] with accounts[0] having 10000 (958ms)
    ✓ transfers: throw when trying to transfer 10001 to accounts[1] with accounts[0] having 10000 (956ms)
    ✓ transfers: should allow zero-transfers (875ms)
    ✓ approvals: msg.sender should approve 100 to accounts[1] (942ms)
    ✓ approvals: msg.sender approves accounts[1] of 100 & withdraws 20 once. (1200ms)
    ✓ approvals: msg.sender approves accounts[1] of 100 & withdraws 20 twice. (1232ms)
    ✓ approvals: msg.sender approves accounts[1] of 100 & withdraws 50 & 60 (2nd tx should fail) (1090ms)
    ✓ approvals: attempt withdrawal from account with no allowance (should fail) (919ms)
    ✓ approvals: allow accounts[1] 100 to withdraw from accounts[0]. Withdraw 60 and then approve 0 & attempt transfer and throw. (960ms)
    ✓ approvals: approve max (2^256 - 1) (991ms)
    ✓ events: should fire Transfer event properly (890ms)
    ✓ events: should fire Approval event properly (959ms)


  28 passing (24s)
```


## Audit information

### Limitations

Sigma Prime makes all effort, but holds no responsibility for the findings of this audit. Sigma Prime does not provide any guarantees relating to the function of the smart contract. Sigma Prime makes no judgements on, or provides audit on, the viability of the token sale, the underlying business model or the individuals involved in the token sale.

The procedures that we will perform will not constitute an audit or a review in accordance with Australian
Auditing Standards and, consequently, no assurance will be expressed.

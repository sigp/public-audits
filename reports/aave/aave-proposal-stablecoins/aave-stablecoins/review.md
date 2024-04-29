# Aave Chainlink Synchronicity Price Adapter Review

## Introduction

Sigma Prime was commercially engaged to perform a time-boxed security review of the Aave Chainlink Synchronicity Price Adapter smart contracts, as part of the [Master Services Agreement](https://governance.aave.com/t/sigma-prime-security-assessment-services-for-aave/8518) established between Sigma Prime and the Aave DAO.
The review focused on the security aspects of the Solidity smart contracts, along with the relevant migration processes.

### Disclaimer

Sigma Prime makes all effort but holds no responsibility for the findings of this security review. Sigma Prime does
not provide any guarantees relating to the function of the smart contract. Sigma Prime makes no judgements
on, or provides any security review, regarding the underlying business model or the individuals involved in the
project.

### Overview

This review covers updates to the oracle mechanisms associated with the `CLSynchronicityPriceAdapter` contract.
The purpose of the contract is to reduce the impact of lag time when multiple stable coins (USD) have different price feeds.
The updated price adapters will share a Base to USD price feed and have a unique Asset to USD feed.

The price adapter uses two feeds to establish the price for an asset.
- Asset to USD price (e.g. USDC to USD)
- Base to USD price (e.g. ETH to USD)

The final calculation is:

```
Asset to Base Price = Asset to USD Price / Base to USD Price
```

### Scope

The scope of the audit covers the following components:
* The `CLSynchronicityPriceAdapter.sol` contract, and
* Integration of the price adapter with the V2 `LendingPool.sol`.

### Summary of Findings

One informational findings and two miscellaneous findings were found during the review posing negligible security risks.


## 1. INFORMATIONAL: Potential `int256()` casting overflow may cause negative `DECIMALS_MULTIPLIER`.

There are three potential overflows during the `int256` castings in `_calcDecimalsMultiplier()`.
Casting from an `uint256` to a `int256` will cause an overflow if the left most bit of the `uint256` variable is a `1` bit.

This issue is raised as informational since it would require the decimals of one of the Chainlink feeds or the current contract to be 77.
A Chainlink feed will have a default of 8 decimal places thus this implies a malicious configuration.

Each of the three casts from `uint256` to `int256` in the following code will overflow if the exponent is 77, as 10^77 is greater than 2^255 and will have its left most bit set to `1`.
The result is an overflow causing `multiplier` to be negative:

```solidity
        int256 multiplier = int256(10 ** resultDecimals);
        if (assetToPegDecimals < baseToPegDecimals) {
            multiplier *= int256(10 ** (baseToPegDecimals - assetToPegDecimals));
        } else {
            multiplier /= int256(10 ** (assetToPegDecimals - baseToPegDecimals));
        }
```

**Resolution**

The issue has been resolved by ensuring each of the decimals is less than 18, thus it will be impossible to have an exponent of 77.
The resolution can be seen in commit [8311402](https://github.com/bgd-labs/aave-proposal-stablecoins-priceadapter/pull/1/commits/83114026d77f00e2013bfdf957f67a711eb203ad).


## Miscellaneous

### M1. Loose bounds check for `DECIMALS_MULTIPLIER`.

The variable `DECIMALS_MULTIPLIER` is of type `int256`. 
The following check exists on line #52.

 ```solidity
 if (DECIMALS_MULTIPLIER == 0) revert DecimalsMultiplierIsZero();
 ```
 
**Recommendations**

Consider also reverting if `DECIMALS_MULTIPLIER` is negative. e.g.

 ```solidity
 if (DECIMALS_MULTIPLIER <= 0) revert DecimalsMultiplierNotPositive();
 ```

### M2. Spelling Mistake.

On line #41 the variable `asseToPegAggregatorAddress` incorrectly spells `asset`.

Consider renaming it to `assetToPegAggregatorAddress`.


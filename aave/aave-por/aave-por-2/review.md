# Aave Proof of Reserve Review Round 2

## Introduction

Sigma Prime was commercially engaged to perform a time-boxed security review of the Aave Proof of Reserve smart contracts, as part of the [Master Services Agreement](https://governance.aave.com/t/sigma-prime-security-assessment-services-for-aave/8518) established between Sigma Prime and the Aave DAO.
The review focused on the security aspects of the Solidity smart contracts.

### Disclaimer

Sigma Prime makes all effort but holds no responsibility for the findings of this security review. Sigma Prime does
not provide any guarantees relating to the function of the smart contract. Sigma Prime makes no judgements
on, or provides any security review, regarding the underlying business model or the individuals involved in the
project.

### Overview

The review covers an update to the Proof of Reserve functionality.
The review is targeted at commit [fd3163c](https://github.com/bgd-labs/aave-proof-of-reserve/commit/fd3163c9053cb2b5aebfdff51fe4157e1133f234).

The core of the update the `ProofOfReserveExecutorV3` to set LTV for an asset to zero rather than disabling borrowing for all reserves.
Setting the LTV to zero will prevent users from borrowing using this asset as collateral.

### Scope

The scope of the review covers the following components:
* `AvaxBridgeWrapper.sol`
* `ProofOrReserveAggregator.sol`
* `ProofOfReserveExecutorBase.sol`
* `ProofOfReserveExecutorV2.sol`
* `ProofOfReserveExecutorV3.sol`
* `ProofOfReserveKeeper.sol`
* Integration of the contracts with `LendingPool` and `PoolConfigurator` for both Aave V2 and V3.

### Summary of Findings

One informational finding was found during the review.


## 1. INF: Interchanging `enableProofOfReserveFeed()` and `enableProofOfReserveFeedWithBridgeWrapper()` May Cause An Invalid State.

In `ProofOfReserveAggregator.sol`, the functions `enableProofOfReserveFeed()` and `enableProofOfReserveFeedWithBridgeWrapper()` may be called on existing feeds.

When `enableProofOfReserveFeedWithBridgeWrapper()` is called it will update the values `_proofOfReserveList[asset]` and `_bridgeWrapperList[asset]`.
Since `enableProofOfReserveFeed()` only updates `_proofOfReserveList[asset]` any residual values stored in `_bridgeWrapperList[asset]` will be preserved.

The impact of this issue is seen in the function `areAllReservesBacked()` which may incorrectly use the residual bridge value for `totalSupplyAddress`.
This can be seen in line #100-102 of `ProofOfReserveAggregator.sol`.

```solidity
  address totalSupplyAddress = bridgeAddress != address(0)
    ? bridgeAddress
    : assetAddress;
```

**Recommendation**

Consider enforcing `_proofOfReserveList[asset] == address(0)` in both `enableProofOfReserveFeed()` and `enableProofOfReserveFeedWithBridgeWrapper()`.
To update the feed it would require first calling `disableProofOfReserveFeed()` followed by either `enableProofOfReserveFeed()` or `enableProofOfReserveFeedWithBridgeWrapper()`.

An alternative solution is to set `delete _bridgeWrapperList[asset]` in `enableProofofReserveFeed()`.
This will delete any residual values from previous calls to `enableProofOfReserveFeedWithBridgeWrapper()`.




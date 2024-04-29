# Aave Proof of Reserve Review

## Introduction

Sigma Prime was commercially engaged to perform a time-boxed security review of the Aave Proof of Reserve smart contracts, as part of the [Master Services Agreement](https://governance.aave.com/t/sigma-prime-security-assessment-services-for-aave/8518) established between Sigma Prime and the Aave DAO.
The review focused on the security aspects of the Solidity smart contracts.

### Disclaimer

Sigma Prime makes all effort but holds no responsibility for the findings of this security review. Sigma Prime does
not provide any guarantees relating to the function of the smart contract. Sigma Prime makes no judgements
on, or provides any security review, regarding the underlying business model or the individuals involved in the
project.

### Overview

The review covers the introduction of the Proof of Reserve functionality.
The review is targeted at commit [23a1340](https://github.com/bgd-labs/aave-proof-of-reserve/tree/23a13401162a259495deacd46ee743510c382ca6).

Proof of Reserve is a risk mitigation technique. 
The system uses a Chainlink oracle to fetch quantity of the underlying asset stored by the bridge.
Using the total supply of the bridged ERC20 token it may then determine if the bridged token is fully backed by the underlying token.

For the case where the bridged token is not fully backed a Chainlink Keeper is set up to trigger the emergency action.
The emergency action will disable all borrowing in the `LendingPool` if any bridged token is unbacked.

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

One low, one informational and two miscellaneous findings were found during the review.


## 1. LOW: Race condition between malicious bridge operator and Chainlink Keeper

The design of the protocol has an inherent race condition for disabling borrowings.

`executeEmergencyAction()` can only be triggered after the bridge token total supply is larger quantity of underlying asset locked in the bridge as reported by the Chainlink Oracle.
This creates a race condition where a malicious set of bridge operators may infinite mint bridge tokens, deposit them into the `LendingPool` and make large borrowings of other non-bridge tokens.
As long as the malicious bridge operators perform their transactions before any user calls `executeEmergencyAction()` they may make arbitrary borrowings and exploit infinite minting in the bridge.

**Recommendations**

Calling `areAllReservesBacked()` before any borrowings in the `LendingPool` will prevent malicious bridge operators from being able to exploit infinite minting.
The solution works as `IERC20(assetAddress).totalSupply()` will be updated immediately when the infinite minting occurs and thus `areAllReservesBacked()` would return `false`.

If this solution is implemented then the Chainlink Keeper would no longer be required as the logic would occur on every borrow.


## 2. INFORMATIONAL: Delayed or malfunctioning Chainlink Oracle will cause all borrowing to be paused on `LendingPool`

If a Chainlink Oracle ceases to submit updates then the Keeper will trigger `executeEmergencyAction()` in turn pausing the borrowing of all reserves in the `LendingPool`.

The Keeper is triggered if `areAllReservesBacked()` is `false`, which will arise if the following condition is `true`. 

```solidity
// ProofOfReserveAggregator.sol #63
IERC20(assetAddress).totalSupply() > uint256(answer)
```

When tokens are transferred through the bridge, first the underlying asset is locked in the bridge increasing the value of `answer`.
After the lock transaction is verified then bridge tokens will be minted thereby increasing `IERC20(assetAddress).totalSupply()`.

When the Chainlink oracle is malfunctioning or significantly delayed `answer` is not updated.
Since `answer` represents the total amount of underlying tokens locked in the bridge but has not been updated, we will have the case where `IERC20(assetAddress).totalSupply() > answer`.
Therefore, the keeper will trigger `executeEmergencyAction()` and pause all borrowings.

This issue is raised as information as it is by design of the protocol.
The protocol is unable to determine if the issue is caused by a malfunctioning Chainlink Oracle or a malicious bridge which is not adequately backed.
However, the testing team has deemed a low likelihood of this issue occurring. 
It may occur if the Chainlink Oracle contract runs out of LINK tokens, there is a malformed update or a major bug in the Chainlink protocol.

**Resolution**

Consider implementing off-chain monitoring to validate the status of the Chainlink Oracle.
Furthermore, consider preparing a set of steps which may be rapidly implemented, to enable borrowing in the `LendingPool` when `executeEmergencyAction()` is triggered incorrectly.


## Miscellaneous

### M1. `ProofOfReserveAggregator.enableProofOfReserveFeed()` can be used to disable feeds

If the function parameter `proofOfReserveFeed` in `ProofOfReserveAggregator.enableProofOfReserveFeed()` is set to `address(0)` then it will essentially disable the feed for that asset.
However, the event `ProofOfReserveFeedStateChanged` will still be emitted with `enabled = true`.

**Recommendations**

Consider preventing `proofOfReserveFeed` from being zero in the function `ProofOfReserveAggregator.enableProofOfReserveFeed()`.

## Gas Optimisations

### G1. Use `immutable` rather than storage variables

`SLOAD` is an expensive operation.
It is significantly cheaper to use `immutable` values which are stored in the contract byecode.

The following variables are never modified except for in the constuctor.
Hence, they may be safely changed to `immutable`.

* `ProofOfReserveExecutorBase._proofOfReserveAggregator`
* `ProofOfReserveExecutorV2._addressesProvider`
* `ProofOfReserveExecutorV3._addressesProvider`

### G2. `ProofOfReserveExecutorBase.sol` cache storage array length

Each iteration of an array will execute the conditional statement fetching storage variables with a `SLOAD` instruction if required.

The following loops in `ProofOfReserveExecutorBase.sol` will fetch `_assets.length` from storage each time.

```solidity
// #72
for (uint256 i = 0; i < _assets.length; i++) {
  if (_assets[i] == asset) {
    if (i != _assets.length - 1) {
        _assets[i] = _assets[_assets.length - 1];
    }

    _assets.pop();
    break;
  }
}
```

```solidity
// #106
for (uint256 i = 0; i < _assets.length; i++) {
  if (unbackedAssetsFlags[i]) {
    emit AssetIsNotBacked(_assets[i]);
  }
}
```

Consider storing the value `_assets.length` in memory.

### G3. Import interfaces rather than contracts

`ProofOfReserveExecutorBase.sol` import and casts addresses to `ProofOfReserveAggregator` for external calls.
Hence, the entire bytecode of `ProofOfReserveAggregator` will be required in `ProofOfReserveExecutorBase`.
Increasing the size of the bytecode will increase the gas costs in deployment.

Consider creating an interface `IProofOfReserveAggregator` which exports function `areAllReservesBacked()`, then use the interface in `ProofOfExecutorBase.sol`.

### G4. Use `++i` rather than `i++` in `for` loops.

`++i` uses slightly less gas than `i++` due to the creation of a temporary variable.

Each of the scoped contracts only use `i++` during the _update_ statement in a `for` loop.
Within a `for` loop the return value of the _update_ statement `i++` is discarded, therefore either `i++` or `++i` can be used interchangeably.

Since `++i` is cheaper consider replacing all cases of `i++` with `++i`.
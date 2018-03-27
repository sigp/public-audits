# Havven Token Contract Audit


Sigma Prime was commercially engaged by Havven to perform a time-boxed public audit on the full set of smart contracts dictating the dynamics and functionality of the Havven (HAV) and Ether-back USD Nomins (eUSD) tokens.

Any analysis of the economic incentive structure or business case of the system is outside the scope of this smart contract audit.

This public document is the deliverable of the audit engagement.

## Project Overview

The Havven system is a two-token (ERC20) system, designed to establish a new form of stable coin. There are two tokens;

 - "Ether-backed USD Nomins" (`nomin` or `nomins`), the designated stable coin with a price set via an external oracle and collateralised by the second token,
 - "Havven" (`havven` or `havvens`), a token which collects fees from `nomin` transfers.

The [Havven Whitepaper](https://havven.io/uploads/havven_whitepaper.pdf) (subsequently referred to as "the whitepaper") details a the price stability mechanism mandating that `nomin` transactions incur a usage fee. The resulting pool of usage fees is distributed in turn to users who supply `havvens` as the collateral to produce a supply of stable `nomins`. In this way, the whitepaper infers that `havven` owners are incentivised to participate in the `nomin` price-stabilisation mechanism.

- The `nomin` supply is centrally controlled by the Havven foundation and backed solely by `ether`.
- `havven` holders cannot issue `nomins` against their `havvens`.
- A simplified fee incentive mechanism is employed, such that:
    - fees are distributed among `havven` holders in proportion to their average holdings over a time period.
    - the dynamic fee structure described in the whitepaper, which would apply to `havvens` held as collateral, is absent. (i.e., the fee rate is static).
- The collateral for `nomins` is `ether` which cannot be expanded by the market, meaning the total supply of the currency is constrained.

It is our understanding that the discrepancies between the whitepaper and the current smart contract functionality have been clearly communicated by Havven to the wider community. Instead, they are a step towards a final implementation accurately representing the whitepaper.

## Contract Overview

There are four main Solidity files, named `Court.sol`, `EtherNomin.sol`, `HavvenEscrow.sol` and `Havven.sol`, each of which possesses its own distinct logic. These four files define four primary Solidity `contracts`:

- The `Court` contract, which dictates a voting mechanism whereby participants of the system may vote to confiscate `havvens` from bad-actors. We understand this is primarily intended to prevent token wrapping contracts, as discussed in the whitepaper.  
- The `EtherNomin` contract, which specifies the `nomin` tokens, their creation and destruction, associated fees and price finding mechanism.
- The `HavvenEscrow` contract, which allows the foundation to allocate `havvens` to investors with specific vesting schedules. It is worth noting that investors may still claim the `nomin` fees accrued by their vested `havven` tokens.  
- The `Havven` contract, which specifies the `havven` tokens along with the mechanisms required to collect fees for passive token holders. It specifies the initial creation and subsequent distribution of the `havven` tokens.

## Audit Summary

The testing team has not identified any vulnerabilities affecting the mathematical operations used in the assessed contracts. Furthermore, no exploitable integer underflows/overflows, re-entrancy bugs nor contract ownership hijacking were identified.

Aside from the technical vulnerabilities described in this report and summarised in the **Overall Vulnerability List**, the testing team has identified that the contracts, as they stand are designed in a highly centralised fashion. The contracts specify an `owner` account whose privileges are paramount. As with most centralised systems, the greatest attack vector is to claim ownership of the contracts or to steal the private key(s) of the `owner` account. Should an attacker be successful, the entire system would be compromised, all tokens could be destroyed/stolen along with any `ether` contributed to the system.

In this audit, we dedicate a section to list the direct and indirect privileges the `owner` account has to demonstrate the extent of centralisation and potential danger of having a malicious actor with control of the `owner` account. Furthermore, the `owner` is capable of injecting arbitrary code which participants of the system may run in the course of a transaction, expanding the attack surface to not just the contracts audited here, but to all contracts in the Ethereum ecosystem (this is detailed further in the **Potential Attacks** section).

### Overall Vulnerability List

| Vulnerability 												  |File | Severity      |
|-----------------------------------------------------------------|---|:-------------:|
| Vote Manipulation via Improper Variable Resetting     		  |Court.sol| High		  |
| Inaccurate Vote Calculation due to Outdated Average Balance     |Court.sol| High		  |
| Token Wrapping Prevention Bypass 								  |Court.sol| High 		  |
| Arbitrary Dependent Contract Address Modification				  |EtherNomin.sol, Havven.sol, Court.sol, HavvenEscrow.sol| High 		  |
| Inactive Owner Leading to User Fund Lockups					  |HavvenEscrow.sol| Moderate	  |
| Insufficient Hardening of Contract Ownership Transfer			  |Owned.sol| Low 		  |
| Insufficient Recipient Address Validation						  |ERC20Token.sol, ERC20FeeToken.sol| Low 		  |
| Insufficient Transfer Fee Rate Validation						  |ERC20FeeToken.sol| Low 		  |
| Duplicate Event Call											  |HavvenEscrow.sol| Low 		  |
| Lack of Vesting Periods Validation							  |HavvenEscrow.sol| Low 		  |


### Per-Contract Vulnerability Summary

#### Nomin Contract (`EtherNomin.sol`)

Besides the attacks by the `owner` outlined in **Potential Attacks** we found no vulnerabilities with this contract.

#### Havven Contract (`Havven.sol`)

Besides the attacks by the `owner` outlined in **Potential Attacks** we found no vulnerabilities with this contract.

#### Voting Mechanism (`Court.sol`)

This element of the contracts contains two distinct high severity vulnerabilities:

 - A vector which allows an attacker to accumulate a theoretically infinite number votes (in two distinct ways) which they can use to negate any votes cast against them. As the owner of the contract only has authority if a vote passes, not even the owner of the contract can prevent the accumulation of votes and force the confiscation of `nomins` from the attacker.
 - A vector which allows a specially-designed fee-avoidance token wrapper contract to skirt the actions of the court in a decentralised manner (with respect to the participants in the wrapper contract). If one accepts that the primary purpose of the court is to avoid fee-avoiding token wrappers, the existence of such a contract makes the `Court` contract redundant at most, or an inconvenience at the least.

#### Havven Escrow (`HavvenEscrow.sol`)

The correct operation of this contract requires an active `owner`. If the `owner` loses their keys, or is absent, users who have vested tokens will not be able to claim any of their fees. We found no other serious vulnerabilities in this contract.

## Detailed Audit

This section details the technicalities of the issues found in the audit and gives Sigma Prime's recommendations for correcting these issues. Example potential attack scenario's are described to highlight the vulnerabilities and some gas saving techniques/suggestions are provided.

### Files audited
The files that were analysed in this audit are given below:

```
└── contracts
    ├── Court.sol
    ├── ERC20FeeToken.sol
    ├── ERC20Token.sol
    ├── EtherNomin.sol
    ├── HavvenEscrow.sol
    ├── Havven.sol
    ├── Owned.sol
    └── SafeDecimalMath.sol
```

### ERC20 Implementation

This section refers to the ERC20 specification outlined [here](https://github.com/ethereum/EIPs/blob/master/EIPS/eip-20.md). Discrepancies from this standard can potentially cause issues with third-party software or applications interacting with the tokens.

The `havven` and `nomin` tokens follow the ERC20 standard with the following two discrepancies:
- The initial creation of the tokens (**ERC20FeeToken.sol [70,71]** for `nomins` and **ERC20Token.sol [50,51]** for `havvens`) do not fire the `Transfer` event with the `0x0` address as the sender.
- The `decimals` variable is of type `uint256`, not the specified `uint8`. (see **SafeDecimalMath.sol [38]**).

#### Remarks

There is a known race condition in the `approve` function. See [here](https://docs.google.com/document/d/1YLPtQxZu1UAvO9cZ1O2RPXBbT0mooh4DYKjA_jp-RLM/edit) for a description. External applications should set the allowance first to `0`, before changing its value.

For the `nomin` token, third party applications must be aware that fees are added to the transfer value. For example, a user, `a` can call `approve()` to address `b` with a value of `10 nomins`. If an application subsequently tries to `transfer` (on behalf of `b`) for `10 nomins` from `a`, the transfer will revert, due to the fees being added on top of the value.

### Recommendations

This section details our recommendations for the contracts tested. The recommendations are classified into three categories of severity; high, moderate and low.

#### High

##### Vote Manipulation via Improper Variable Resetting

**Court.sol [410,448,477]** - The combination of functions `cancelVote`, `closeVote` and/or `vetoVote` allow attackers to collect an arbitrary number of votes, to be used on a target account at a future point. This vulnerability also allows attackers to lock other user's votes to prevent them from participating in other motions. The vulnerability originates from the fact that `closeVote` and `vetoVote` zeros votes against the target but does not zero the record of votes made by individual accounts. See **Potential Attacks** for examples of how to exploit this vulnerability. The logic in these functions should be modified.

##### Inaccurate Vote Calculation due to Outdated Average Balance

**Court.sol [379, 381]** - The calculation of vote weight relies on a potentially outdated average balance. This allows users to accumulate an arbitrary amount of votes (provided no one transfers them `havvens` or updates their accounts). Before assigning the weight variable, the `recomputeLastAverageBalance()` of the `Havven` contract should be called to update user's balances and hence weights for voting. See **Potential Attacks** for further details.

##### Token Wrapping Prevention Bypass

**Court.sol** - The purpose of this contract is to prevent token wrapper contracts. Specially-designed contracts can easily bypass this mechanism using proxy contracts to hold `nomins` and swapping-out these proxy contracts as court motions begin. This could be mitigated by freezing the `havvens` immediately after the motion is set against them, but this would require further logic (potentially slashing conditions) in setting up motions to prevent attackers from maliciously freezing `havvens`. Further discussion can be found in the **Potential Attacks** section.

##### Arbitrary Dependent Contract Address Modification

**Court.sol, Havven.sol, EtherNomin.sol, HavvenEscrow.sol** - Each of these contracts allow the owner to modify the address of dependent contracts at any time with no limitation, with the exception of the `Court.` contract where these variables are set only in the constructor. This grants the owner potentially undesired excessive privileges (see **Indirect Privileges** in **Owner Privileges** for a non-exhaustive list). This also allows the owner to trick users into running arbitrary code in standard functions (see **Potential Attacks**). We recommend that if these privileges are necessary (e.g., to update the contract) that they be at least bounded by time, such that users can choose whether to participate in the upgrade or code changes. This can be done in a two-step process, whereby the owner initially proposes a new contract address (for `Court`, `Havven`, `HavvenEscrow`, `EtherNomin`) and then sets the change into effect in a second transaction which must occur after a period of time, allowing users to decide if they still wish to participate.

#### Moderate

##### Inactive Owner Leading to User Fund Lockups

**HavvenEscrow.sol [210] - withdrawFees()** - A stagnant or absent owner (e.g., if the owner loses their keys) will prevent all users from withdrawing any fees from the `HavvenEscrow` contract. This function reverts if the owner has not withdrawn the fees from the last period. It is recommended that the logic is adjusted to not require an active owner.


#### Low

##### Insufficient Hardening of Contract Ownership Transfer
**Owner.sol** - Does not use a ["Claim Ownership"](https://github.com/OpenZeppelin/zeppelin-solidity/blob/master/contracts/ownership/Claimable.sol) style pattern for ownership transfer, making it possible to assign ownership to an address out of the control of the owners.

##### Insufficient Receipient Address Validation

**ERC20FeeToken [137,163] and ERC20Token.sol [57,76]** - Add validation for the `_to` address, to ensure it is not the `0x0` address. This will prevent tokens being accidentally sent to `0x0`. This is a common error for users of third party applications which default missing parameters to `0x0`.

##### Insufficient Transfer Fee Rate Validation

**ERC20FeeToken [72]** - The contract has a `maxTransferFeeRate` which is not respected in the constructor. We suggest adding the validation to ensure the `feeTransferRate` isn't artificially set higher than the maximum rate during deployment.

##### Duplicate Event Call

**HavvenEscrow.sol [219]** - The `ContractFeesWithdrawn()` event gets fired twice with the same parameters. If this is not intentional, one should be removed.

##### Lack of Vesting Periods Validation

**HavvenEscrow.sol [230] - appendVestingEntry()** - This function has no validation around the quantities that can be added to users vesting periods. As the contract stands, the actual `havven` balance in the `HavvenEscrow` contract is entirely decoupled from the balances it claims to have. In principle the owner can credit an account with more `havven` than exists (e.g., `totalSupply`). This can cause internal inconsistencies when the users withdraw. We recommend enforcing that the `totalSupply` of the `Havven` contract is at least as large as the new `totalVestedBalance` variable.

#### General Suggestions

**SafeDecimalMath.sol** - The typical convention to check over/underflows is to use the `assert()` function rather than `require()`. The `assert()` will consume all gas of the transaction and is typically desired if an over/underflow occurs (which shouldn't happen in normal execution). However, the ERC20 `transfer` functions (and a number of other functions, such as `withdrawFees()`) in these contracts, specifically rely on this `SafeDecimalMath` to ensure withdrawals have adequate balances. We suggest the method where an explicit `require()` is used to verify the balance of transfer events, `asserts()` are used in the `SafeDecimalMath` logic and overflow errors are rarely encountered. See the [OpenZeppelin contracts](https://github.com/OpenZeppelin/zeppelin-Solidity/tree/master/contracts) for examples.

**Court.sol [132,133]** - Havven and Nomin addresses are not public. Users will not easily be able to see which address is linked to this contract and therefore which code is being run to estimate their weights.

**EtherNomin.sol [62,123]** - This contract does not need to import `Havven.sol`, and the cast can be removed from the constructor.

**Havven.sol [108]** - This contract does not need to import `Court.sol`.

**Havven.sol** - The `lastAverageBalance` and `penultimateAverageBalance` are public but would quite frequently be out-of-date, potentially misleading users.

**ERC20FeeToken [36]** - Use of `uint256` in contrast to otherwise consistent `unit` usage.

**EtherNomin.sol [193]** - The variable naming in the parameter could be changed to `wei` from `eth` to accurately represent the units being passed to the function.

**EtherNomin.sol [125]** - There is inconsistent naming in the parameters. `initialEtherPrice` should be changed to `_initialEtherPrice` for consistent naming.

**EtherNomin.sol [87,90,94]** - We suggest making these variables public as they are important for users and applications to interact with the contract and understand its dynamics.

**EtherNomin.sol** - Make it very clear that variables should be supplied as multiples of `UNIT`. E.g., if the `ether` price on exchanges is `$1000`, provide `1000 * UNIT` to the `updatePrice()` method.

**EtherNomin.sol** - It may be prudent to allow any address to call `terminateLiquidation()`.


**Court.sol [266,512,513]** - The `Court` prefix is not required.

**All Contracts** - We recommend setting a fixed Solidity compiler version rather than allowing all future versions, in the very low chance there is backwards compatibility issues with future versions.

#### Remarks

We note the complexity of the `Court` contract and its current inadequacies in preventing token wrapping. Contracts can be prevented from using `nomins` by adding the requirement that `tx.origin == msg.sender` to `transfer()`, for example. This will also restrict multi-sig wallets and all other contracts from using `nomins` but is potentially a simpler solution than employing a voting mechanism.

We also note that the `Court` contract allows accounts to vote when motions are set against them. This can be beneficial as it prevents malicious users setting motions against the foundation which hold a significant amount of tokens. The mathematical analysis of such attacks is outside the scope of this audit and we simply point this out to ensure that this logic is expected.

### Potential Attacks

In this section we elucidate the vulnerabilities mentioned in the recommendation section by giving some potential attacks that can be employed with the current implementation of the contracts.

#### Owner Forcing Users to Run Arbitrary Code

There are a number of areas where this form of attack can work within the Havven contracts. Let us take **Havven.sol [419]** as an example:

This line of code is executed when there is a rollover period and can occur when a user users calls `transfer()`. To illustrate the issue with this line, let us take an unimaginative (potentially not realistic) scenario that someone has written an ERC20 token which uses `tx.origin` in their transfer function rather than `msg.sender`. In this scenario, let an arbitrary `havven` holder hold 100 tokens of this ERC20 token. A malicious owner of the `havven` contract can create a contract, with a fallback function (or a `feePool()` function) that calls `transfer()` on the made up ERC20 token and sends the balance to the `havven` contract owner. The owner then sets this contract to be the `nomin` contract. When an unsuspecting user runs `checkFeePeriodRollOver()` during a rollover period, they are forced to run the code in the malicious contract (the fallback function if no `feePool()` function exists), which will send their ERC20 token balance to the `owner` of the `havven` contract. Thus, the owner has performed an attack on users of the platform utilising external contracts.

Although this particular scenario may not be realistic (we hope future Solidity developers don't use `tx.origin` in this manner), the possibilities of arbitrary code running which can target any arbitrary contracts that has or can be built on Ethereum is a very large attack surface. A recent real-world example of hiding the executing code by changing the address of a contract is with this [honey pot example](https://www.reddit.com/r/ethdev/comments/7x5rwr/tricked_by_a_honeypot_contract_or_beaten_by/).

#### Accumulating Votes to Protect a Token Wrapper Contract

An attacker can accumulate an arbitrary amount of negative yes votes to protect a token wrapper contract address from being voted against. This attack works by first [pre-determining](https://ethereum.stackexchange.com/a/761/3573) a contract address (let us call this address `target`). Let us also assume an attacker holds `X`% of all `havvens` in `account1`. The attacker then does the following:
1. Call `beginConfiscationMotion()` against `target`.
2. Call `voteFor()` against `target`. This sets `userVote[account1] = Vote.Yea`, `voteTarget[account1] = target` and `voteWeight[account1] = weight`.
3. As no one else in the system wishes to vote against `target` (it's an arbitrary address holding no `havvens` or `nomins`), the vote could reasonably fail.
4. Once failed, the attacker calls `closeVote()` against `target`. This resets `voteStartTimes`, `votesFor` and `votesAgainst` to `0` for the target address.
5. The attacker transfers their `havvens` to `account2` and waits a `feePeriod` to maximize their voting `weight`.
6. They repeat steps 1-5 as many times as like, lets say `n`, which will give them `n`\*`weight from X% tokens` negative yes votes (this will become apparent).
7. Once happy with the accumulated votes, the attack creates a token wrapper contract at `target`.
8. The target accumulates `havvens` and users start a vote to confiscate their balance. Users will call `beginConfiscationMotion()`
9. The attacker can then use all tokens in the wrapper (`target`) address to vote against this motion.
10. If needed, the attacker can call `cancelVote` using `account1` which still has `userVote[account1] = Vote.Yea`, `voteTarget[account] = target` and  `voteWeight[account1] = weight`. This will subtract `voteWeight[account1]` from the yea votes against `target`. The attacker can repeat this for all accounts generated in step 6.
11. Incidentally, this will prevent all legitimate yea vote users from cancelling their votes in the voting period due to the revert caused by the `SafeDecimalMath` subtraction (i.e., only a subset of yea vote users will be able to cancel their vote in this voting period).

#### Locking users votes

On failed motions users are required to cancel their vote before participating in new motions. The `if()` statement in **Court.sol [420]** allows an attacker to continually renew a failed vote and hence set this `if()` evaluation to `true`. Users with failed votes who try to cancel their vote will have their transactions reverted due to the `SafeDecimalMath` on **lines [425,428]** (a new motion will reset the `votesFor` and `votesAgainst` to `0`, so any subtraction will from this will revert), in effect locking their voting rights to this singular address.

#### Accumulating Votes from Stale Balances

An attacker can accumulate votes via the following procedure:
1. Acquire a number, `X`, of `havven` tokens into `account1`.
2. Wait for the fee period to role over twice.
3. Transfer `havven` tokens to `account2`. This will set `penultimateAverageBalance[account1] = X` and `lastAverageBalance[account1] = X`.
4. Repeat steps 2-3 as many times as the attacker wants. Lets say `n` times.
5. Attacker can now vote using the `n` accounts each with `X` votes (provided an external agent has not transferred any `havvens` to their account).

#### Token Wrapper Avoiding the Court Mechanism

A token wrapper can be built which uses disposable proxy contracts to store its collected `nomins`. Consider a wrapper contract `A` which initially stores its `nomins` in a "proxy contract" `B`.

`A --controls--> B --calls--> EtherNomin`

As is common with token wrappers, users avoid fees by transferring token entitlements internally inside `A` (unbeknownst to the `EtherNomin` contract). When user wishes to exit the wrapper, a call on contract `A` will transfer the tokens from `B` to an user-specified address.

Freezing the address of `A` would be ineffective, as the tokens are held by contract `B`. Freezing the address of `B` would be effective, but contract `A` could read the public `Court` state and detect a vote approximately four weeks before the `B` address can be frozen. In this four week voting period, contract `A` could spawn a new proxy contract, `C`, and execute a transfer on the `EtherNomin` contract of the balance of `B` to `C`. The `B` contract would be discarded and the voting process would need to begin again on `C`, and so on.

`A --controls--> C --calls--> EtherNomin`

As discussed previously, an immediate freeze upon a confiscation motion would prevent `B` from transferring its `nomin` to `C`. Such functionality would be subject to abuse and would require further thought.

Considering the deterministic nature of contract addresses, one could submit a succinct, on-chain verifiable proof that `C` was created by frozen address `A` and have it immediately frozen (e.g., `proveIsProxyContract(address blacklisted, uint nonce)`). Unfortunately though, this is not a magic bullet as an almost endlessly complex tree of contract creation could be constructed, such that `C` is not created by `A`, but by `B` or arbitrary contract `Z`.

A crude example of such a contract can be found in `EvasiveWrapper.sol` and proof-of-concept testing can be found in `evasiveWrapper.js`.

### Owner Account Privileges

#### Direct

**The following are `Nomin` specific direct privileges:**

**EtherNomin.sol [147,155,163]** The owner can set the `oracle`, `court` and `beneficiary` addresses. Therefore, the owner can run any arbitrary code whenever these addresses are referenced by replacing them with a malicious address.

**EtherNomin.sol [171] - setPoolFeeRate()** - The owner can set an arbitrary pool fee rate, from 0 to 100%.

**EtherNomin.sol [413] - burn()** - The owner can burn any amount of `nomins` if they exist.

**EtherNomin.sol [482] - forceLiquidation()** - The owner can force the liquidation of the `nomin` contract at any time.

**EtherNomin.sol [180] - setStalePeriod()** - The owner can set the stale period to an arbitrary value.

The following are `Court` specific direct privileges:

**Court.sol [210,220,232,241,249]** - The owner can set an arbitrary `minStandingBalance` (as a result prevent anyone from starting motions). The owner can set the `votingPeriod`, `confirmationPeriod`, `requiredParticipation` and `requiredMajority`. The owner effectively controls all dynamics of voting, with some restrictions on the last three variables.

**The following are `Havven` specific direct privileges:**

**Havven.sol [182, 189, 196, 222]** - The owner can set the `nomin` and `escrow` contract to any arbitrary address. The owner distributes all `havvens` that initially come into existence. The owner can set the `targetFeePeriodDurationSeconds` variable.

**The following are `HavvenEscrow` specific direct privileges:**

**HavvenEscrow.sol [169, 177]** - The owner can set the `havven` and `nomin` contract addresses to any arbitrary address at any time.

**HavvenEscrow.sol [230] - purgeAccount()** - The owner can delete any vesting account balance and remove them from the contract at any time without restriction.

**HavvenEscrow.sol [254] - appendVestingEntry()** - The owner can add any account to the escrow contract with any balance (irrespective of `havvens` in existence or currently in the contract).

#### Indirect

**The following are `nomin` specific indirect privileges:**

**EtherNomin.sol [544] - confiscateBalance()** - The owner can confiscate anyone's `nomins` at will and freeze their accounts. This function has a require which checks `msg.sender = court`. As the owner can arbitrarily change court, they can easily create a wrapper contract passing all the requirements, then set the `court` variable to this contract and confiscate any users balances.

**EtherNomin.sol [375] - updatePrice()** - The owner can set any arbitrary price for `nomins`. They may change the oracle address to any address and therefore set the price to any arbitrary value.

**EtherNomin.sol [393] - issue()** - The owner can create `nomins` at manipulated prices. This function allows `nomins` to be created provided a collateralisation ratio is maintained. As the owner can can adjust the `etherPrice` at will, they can adjust the collateralisation ratio to manipulate the collateralisation cost of `nomins`.

**EtherNomin.sol [432] - buy()** - The owner can prevent any users from purchasing `nomins` at any time. This can be achieved by setting the `stalePeriod` to a very large value or by forcing liquidation.

**ERC20FeeToken.sol [200] - withdrawFee()** - The owner can withdraw any fees from the `nomin` contract at any time. The owner can change the `feeAuthority` variable which is the only requirement of this function. The owner creates a wrapper contract to call this function at will.


**The following are `Havven` specific indirect privileges:**

**Havven.sol [297]** - The owner can prevent any individual user or all users from withdrawing any fees, and force users to run arbitrary code. This is done by changing the `nomin` contract address to a malicious address.

The following are `Court` specific indirect privileges:

**Court.sol [347]** - The owner can pass or fail any confiscation motion. The owner can adjust the `havven` contract which specifies the `weight` for votes. The owner can give themselves arbitrary high votes and everyone else nothing, by replacing `havven` with a malicious contract.

**Court.sol [347]** - The owner can prevent specific or all confiscation motions. By manipulating the `havven` address the owner can fail this requirement for specific or all users.  

**Court.sol [347]** - The owner can get users to run arbitrary code when they call `beginConfiscationMotion` by replacing either `nomin` or `havven` with a malicious contract address.

**The following are `HavvenEscrow` specific indirect privileges:**

**HavvenEscrow.sol [161] - feePool()** - The owner can set the `feePool` variable to any arbitrary number. As `feePool()` returns `nomin.balanceOf(this)`, and the owner can change `nomin` to any address, the owner can create a contract with a function `balanceOf` that returns an arbitrary value. The owner then sets `nomin` to this contract to specify any `feePool()` they wish.

**HavvenEscrow.sol [187] - remitFees()** - The owner can remit fees of the `HavvenEscrow` contract. The owner can set the `havven` address to any address and as such can create a wrapper contract to pass the single requirement.

**HavvenEscrow.sol [187] - remitFees()** - The owner can get users to run arbitrary code and create attacks external to the Havven system for users (see *potential attacks* for further details). The owner can set `nomin` to an arbitrary (malicious) contract such that when a user runs `remitFees`, `nomin.dontateToFeePool()` runs arbitrary malicious code.  

**HavvenEscrow.sol [210] - withdrawFees()** - The owner can prevent all users from withdrawing their fees. If the owner hasn't withdrawn in the last period, this function will throw as only the owner can call `withdrawFeePool()`.

**HavvenEscrow.sol [222]** - The owner can arbitrarily specify any individual users or all user's shares and entitlements in the `HavvenEscrow` contract. The entitlement a participant has is calculated by referencing an external contract which can be arbitrarily changed by the owner and hence the owner can set this value arbitrarily.  

### Gas Information

Here we list rough estimates of the gas used to deploy and run various functions of the smart contracts. This is mainly to clarify potential issues with deployment (such as not being able to deploy all contracts in a single block, due to the block gas limit) and production. The values listed here are approximations.

#### Contract deployment
`EtherNomin` : 4.1 M gas
`Havven` : 2.8 M gas
`HavvenEscrow` : 4.1 M gas
`Court` : 3.2 M gas

Havven-related gas costs:
- Standard Havven Transfer (Outside Fee Period adjustment) : 50,000 gas (typical for ERC20)
- Havven Transfer (With fee period adjustment) : 130,000 gas (the client side should expect this gas increase)
- Havven Endow : 200,000 gas

#### Gas Reduction Changes

Initialising variables costs gas. Variables that are initialised to their default values cost unnecessary gas. Removing these initialisation will reduce the gas costs of the contract. Below is a list of initialisations that could be removed to reduce the gas costs.  

**ERC20FeeToken.sol [53]**

**EtherNomin.sol [81]**

**HavvenEscrow.sol [299]**

Using the `delete` keyword when resetting variables saves gas for users. The following code can utilise this strategy to save gas:

**Court.sol [356-357,441,449,459-461, 475-477,488-490]**

**HavvenEscrow.sol [236]**

**Havven.sol [380,381]**

**EtherNomin.sol [559,571]**

**Court.sol [363]** - This function can be set to a view function which will save gas usage.

**Court.sol [441]** - This line serves no purpose and can be removed to save gas.

**ERC20FeeToken.sol [151-153] and ERC20Token.sol [84-86]** - These lines add gas for every non-zero transaction. Can be removed.

In **SafeDecimalMath** the safe functions call other checking functions, such as **addIsSafe**. There is gas overhead in calling other functions, writing these as a single function reduces gas costs.


### Tests

The following tests were implemented during the audit. Tests were developed using [truffle](http://truffleframework.com/) and [ganache-cli](https://github.com/trufflesuite/ganache-cli).

To run the tests, navigate to the `truffle` directory and run `$ truffle test`.

```
Contract: Court scenarios
    ✓ should allow for a confiscation with 100% votes in favour and owner approval (3383ms)
    ✓ should not allow for a confiscation which has less than the required majority (3192ms)
    ✓ should not allow for a confiscation motion from an account with less than 100 havven (2248ms)

Contract: EvasiveWrapper malicious scenarios (passing means vulnerable)
    ✓ should successfully evade a confiscation attempt (3624ms)
    ✓ should not be affected by a confiscation to the EvasiveWrapper contract address (3459ms)

Contract: Havven scenarios
    ✓ should distribute fees evenly if there are only two equal havven holders (2387ms)
    ✓ should not allow double fee withdrawal (1292ms)
    ✓ should roll over uncollected fees into the next fee period (2721ms)
    ✓ should not give any fees to someone who dumped all havvens in the penultimate fee period (3448ms)
    ✓ should store an accurate penultimate avg. balance (3210ms)
    ✓ should show an average balance of half if tokens are moved halfway though the fee period (3441ms)

Contract: EtherNomin basic functionality
    ✓ should use the values supplied in the constructor (148ms)
    ✓ should return 4500 from a fiatValue(4.5) call if etherPrice is 1000 (111ms)
    ✓ should return a fiatBalance of 2000 if etherPrice is 1000 and the contract holds 2 ETH (281ms)
    ✓ should return 4.5 from a etherValue(4500) call if etherPrice is 1000 (107ms)
    ✓ should return false from priceIsStale() if the price was recently updated (332ms)
    ✓ should return true from priceIsStale() if the price was update more than 2 days ago (1035ms)
    ✓ should return a ratio 3000 if there is 3 ETH in the contract, 1 nomin issued and an ETH price of $1500 (168ms)
    ✓ should determine a pool fee of 0.01 nomins on a transfer of 2 nomin (89ms)
    ✓ should return a purchase cost of $4.02 to purchase 4 nomins (88ms)
    ✓ should return a purchase cost of 0.15075 ETH to purchase 300 nomins at an ethPrice of $2000 (77ms)
    ✓ should return proceeds of $348.25 when selling 350 nomins (90ms)
    ✓ should return proceeds of 70.39625 ETH when selling 283 nomins at an ETH price of $4 (111ms)
    ✓ should return false to canSelfDestruct() if the liquidationTimestamp is in the future (326ms)
    ✓ should return true to canSelfDestruct() if the liquidationPeriod has passed (1269ms)
    ✓ should return true to canSelfDestruct() if all nomin have been returned to pool and its been 1 week since liquidation (1212ms)
    ✓ should revert if the caller of updatePrice is not the oracle (76ms)
    ✓ should set etherPrice to the supplied variable if updatePrice() is called by oracle (107ms)
    ✓ should go into auto liquidation if the price is set so low the contract becomes under-collateralised (232ms)
    ✓ should throw if issue() called from not owner (136ms)
    ✓ should throw if issue() called when contract is liquidating (213ms)
    ✓ should throw if issue() called without sufficient collateralisation (123ms)
    ✓ should throw if issue() called when ethPrice is stale (867ms)
    ✓ should update totalSupply after issue() (139ms)
    ✓ should update nominPool after issue() (180ms)
    ✓ should throw if burn() called from not owner (153ms)
    ✓ should throw if burning more tokens than in the pool (135ms)
    ✓ should update totalSupply and nominPool after a burn() (188ms)
    ✓ should throw if buy() called when contract is liquidating (208ms)
    ✓ should throw if buy() is less than 1/100th of a nomin (141ms)
    ✓ should throw on buy() if price is stale (925ms)
    ✓ should update nominPool and balanceOf on successful buy (237ms)
    ✓ should update balanceOf and nominPool after sell() (285ms)
    ✓ should allow sell() when the ethPrice is stale and contract is liquidating (1046ms)
    ✓ should not allow sell() when the ethPrice is stale and contract is not liquidating (1144ms)
    ✓ should throw if selling more nomins than owned (214ms)
    ✓ should transfer eth to seller (666ms)
    ✓ should not allow a non-owner to call forceLiquidation() (104ms)
    ✓ should allow a owner to call forceLiquidation() (464ms)
    ✓ should not allow an owner to call forceLiquidation a second time (140ms)
    ✓ should not allow extendLiquidationPeriod() when not in liquidation (108ms)
    ✓ should extend liquidation period by 30 days (216ms)
    ✓ should not allow the liquidationPeriod to be extended to 180.1 days (164ms)
    ✓ should not allow a terminateLiquidation() call when not liquidating (136ms)
    ✓ should not allow a terminateLiquidation() call when not liquidating (120ms)
    ✓ should not allow liquidation termination when the collat ratio is too low and totalSupply > 0 (334ms)
    ✓ should allow liquidation termination when the collat ratio is too low but totalSupply is 0 (261ms)
    ✓ should allow liquidation termination when totalSupply > 0 but collatRatio is > 1 (303ms)
```

_These tests are a by-product of the audit do not represent comprehensive unit testing._

## Audit information

### Limitations

Sigma Prime makes all effort, but holds no responsibility for the findings of this audit. Sigma Prime does not provide any guarantees relating to the function of the smart contract. Sigma Prime makes no judgements on, or provides audit on, the viability of the token sale, the underlying business model or the individuals involved in the token sale.

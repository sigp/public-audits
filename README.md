# Havven Token Contract Audit

## Introduction

Sigma Prime was commercially engaged by Havven to perform a time-boxed public
audit on the full set of smart contracts dictating the dynamics and
functionality of the Havven (HAV) and Ether-back USD Nomins (eUSD) tokens.

Any analysis of the economic incentive structure or business case of the system
is outside the scope of this smart contract audit.

This public document is the deliverable of the audit engagement.

## Project History

This is the third and final round of the review process:

 - *Round 1*: A review was conducted on commit
   `f0c5f040336e97e5e71dc90f2d51ba8eeb04276e`.
 - *Round 2*: A review was conducted on commit
   `540006e0e2e5ef729482ad8bebcf7eafcd5198c2`. The code changes in this commit
address vulnerabilities found in Round 1 and also introduce new features to
the smart contract.
 - *Round 3*: Each open vulnerability raised in Round 2 was assessed
as of commit `fa705dd2feabc9def03bce135f6a153a4b70b111`. 

## Project Overview

The Havven system is a two-token (ERC20) system, designed to establish a new
form of stable coin. There are two tokens;

 - "Ether-backed USD Nomins" (`nomin` or `nomins`), the designated stable coin
   with a price set via an external oracle and collateralised by the second
token,
 - "Havven" (`havven` or `havvens`), a token which collects fees from `nomin`
   transfers.

The [Havven Whitepaper](https://havven.io/uploads/havven_whitepaper.pdf)
(subsequently referred to as "the whitepaper") details a price stability
mechanism mandating that `nomin` transactions incur a usage fee. The resulting
pool of usage fees is distributed in turn to users who supply `havvens` as the
collateral to produce a supply of stable `nomins`. In this way, the whitepaper
infers that `havven` owners are incentivised to participate in the `nomin`
price-stabilisation mechanism.

- The `nomin` supply is centrally controlled by the Havven foundation and
  backed solely by `ether`.
- `havven` holders cannot issue `nomins` against their `havvens`.
- A simplified fee incentive mechanism is employed, such that:
	- fees are distributed among `havven` holders in proportion to their
	  average holdings over a time period.
	- the dynamic fee structure described in the whitepaper, which would apply
	  to `havvens` held as collateral, is absent. (i.e., the fee rate is
static).
- The collateral for `nomins` is `ether` which cannot be expanded by the
  market, meaning the total supply of the currency is constrained.

It is our understanding that the discrepancies between the whitepaper and the
current smart contract functionality have been clearly communicated by Havven
to the wider community. Instead, the current implementation is a step towards a
final implementation that is detailed in the whitepaper.

## Contract Overview

There are four main Solidity files, named `Court.sol`, `EtherNomin.sol`,
`HavvenEscrow.sol` and `Havven.sol`, each of which possesses its own distinct
logic. These four files define four primary Solidity contracts:

- The `Court` contract, which dictates a voting mechanism whereby participants
  of the system may vote to confiscate `nomins` from bad-actors. We understand
this is primarily intended to prevent token wrapping contracts, as discussed in
the whitepaper.  
- The `EtherNomin` contract, which specifies the `nomin` tokens, their creation
  and destruction, associated fees and price finding mechanism.
- The `HavvenEscrow` contract, which allows the foundation to allocate
  `havvens` to investors with specific vesting schedules. It is worth noting
that investors may still claim the `nomin` fees accrued by their vested
`havven` tokens.  
- The `Havven` contract, which specifies the `havven` tokens along with the
  mechanisms required to collect fees for passive token holders. It specifies
the initial creation and subsequent distribution of the `havven` tokens.

It is important to note that the `EtherNomin` and `Havven` contracts each have
their own `Proxy` and `TokenState` contracts. Users should not interact with
each main contract (`EtherNomin`  and `Havven`) directly, instead they should
use the relevant `Proxy` contract; this allows for the main contracts to be
replaced without requiring users to learn a new contract address.  The
`TokenState` also provides easier contract upgrades by storing token balances
for each main contract so that an upgrade does not require iterative token
balance migration. See below for an illustration:

```
Proxy <--pass call & return data--> EtherNomin <--read/write state--> TokenState


Proxy <--pass call & return data--> Havven <--read/write state--> TokenState
```

The `Court` contract does not have proxy or external state contracts.

## Audit Summary

The testing team has not identified any vulnerabilities affecting the
mathematical operations used in the assessed contracts. Furthermore, no
exploitable integer underflows/overflows, re-entrancy bugs nor contract
ownership hijacking were identified.

Aside from the technical vulnerabilities described in this report and
summarised in the **Overall Vulnerability List**, the testing team has
identified that the contracts, as they stand are designed in a highly
centralised fashion. The contracts specify an `owner` account whose privileges
are paramount. As with most centralised systems, the greatest attack vector is
to claim ownership of the contracts or to gain control of the `owner` account
(or contract) by stealing private keys (or attacking multisigs). Should an
attacker be successful, the entire system would be compromised; all tokens
could be arbitrarily destroyed or stolen along with any `ether` contributed to
the system.

In this audit, we dedicate a section to list the direct and indirect privileges
the `owner` account has to demonstrate the extent of centralisation and
potential danger of having a malicious actor with control of the `owner`
account. Furthermore, the `owner` is capable of injecting arbitrary code which
participants of the system may run in the course of a transaction, expanding
the attack surface to not just the contracts audited here, but to all contracts
in the Ethereum ecosystem (this is detailed further in the **Potential
Attacks** section).

*The authors have acknowledged the issues outlined above and are aware of the
potential risks. The authors note that upon completion of the deployment,
ownership of the contracts will reside with a multsig wallet, so assuming a
majority of the foundation is not malicious, the job of seizing the ownership
is more difficult than obtaining one private key.*

### Overall Vulnerability List

This table does not list vulnerabilities which were resolved in previous
security review rounds (i.e., it only lists vulnerabilities which are currently
exploitable).

|Vulnerability|File|Severity|Status|
|-------------|----|:------:|------|
| Token Wrapping Prevention Bypass|Court.sol|High|Authors intend the Court contract to be an element of dissuasion and are comfortable with it only preventing "casual attackers" at this point in time.
| Arbitrary Dependent Contract Address Modification|EtherNomin.sol, Havven.sol, Court.sol, HavvenEscrow.sol, Proxy.sol, TokenState.sol|High|Is only exploitable by `owner` and authors are comfortable with the privileges granted to `owner`.


### Per-Contract Vulnerability Summary

#### Nomin Contract (`EtherNomin.sol` & `ExternStateProxyFeeToken.sol`)

Besides the attacks by the `owner` outlined in **Owner Account Privileges** no
known vulnerabilities have been identified.

#### Havven Contract (`Havven.sol` & `ExternStateProxyToken.sol`)

Besides the attacks by the `owner` outlined in **Owner Account Privileges** no
known vulnerabilities have been identified.

#### Confiscation Mechanism (`Court.sol`)

There exists a vector which allows a specially-designed fee-avoidance token
wrapper contract to skirt the actions of the court in a decentralised manner
(with respect to the participants in the wrapper contract). The authors
acknowledge and accept this vector with the following note:

*"In line with the outline in the whitepaper, the court contract is a statement
of intent as much as anything else. Ideally, it will never be used, and in this
capacity it must act as an instrument of dissuasion. To this end, building the
impression that the foundation is serious is as important as building the
capacity itself. The court contract can defeat casual attackers, but it can be
updated at a later stage if it becomes necessary. The foundation is prepared
take further steps to protect nomins being wrapped whenever it is needful."*

Apart from this vector, no known vulnerabilities have been identified.

#### Havven Escrow (`HavvenEscrow.sol`)

No known vulnerabilities have been identified.

#### Token State (`TokenState.sol`)

Besides the attacks by the `owner` outlined in **Owner Account Privileges** no
known vulnerabilities have been identified.

#### Proxy (`Proxy.sol`)

Besides the attacks by the `owner` outlined in **Owner Account Privileges** no
known vulnerabilities have been identified.

#### Owned (`Owned.sol`)

No known vulnerabilities have been identified.

#### Safe Decimal Math (`SafeDecimalMath.sol`)

No known vulnerabilities have been identified.

#### Self Destructible (`SelfDestructible.sol`)

No known vulnerabilities have been identified.

#### Limited Setup (`LimitedSetup.sol`)

No known vulnerabilities have been identified.

## Detailed Audit

This section details the technicalities of the issues found in the audit and
gives Sigma Prime's recommendations for correcting these issues. Example
potential attack scenario's are described to highlight the vulnerabilities and
some gas saving techniques/suggestions are provided.

### Files audited

The files that were analysed in Round 1 of the audit are given below:

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

The files that were analysed in Round 2 of the audit are given below:

```
└── contracts
	├── Court.sol
	├── EtherNomin.sol
	├── ExternStateProxyFeeToken.sol
	├── ExternStateProxyToken.sol
	├── HavvenEscrow.sol
	├── Havven.sol
	├── LimitedSetup.sol
	├── Owned.sol
	├── Proxy.sol
	├── SafeDecimalMath.sol
	├── SelfDestructible.sol
	└── TokenState.sol
```

### ERC20 Implementation

This section refers to the ERC20 specification outlined
[here](https://github.com/ethereum/EIPs/blob/master/EIPS/eip-20.md).
Discrepancies from this standard can potentially cause issues with third-party
software or applications interacting with the tokens.

The `havven` and `nomin` tokens follow the ERC20 standard with the following
two discrepancies:
- The initial creation of the tokens (**ERC20FeeToken.sol [70,71]** for
  `nomins` and **ERC20Token.sol [50,51]** for `havvens`) do not fire the
`Transfer` event with the `0x0` address as the sender.

* [x] Addressed in `b420bf7`: `Transfer()` is fired when tokens are created.

- The `decimals` variable is of type `uint256`, not the specified `uint8`. (see
  **SafeDecimalMath.sol [38]**).

* [x] Addressed in `59f6734`: `uint` modified to `uint8` for `decimals`.

#### Remarks

There is a known race condition in the `approve` function. See
[here](https://docs.google.com/document/d/1YLPtQxZu1UAvO9cZ1O2RPXBbT0mooh4DYKjA_jp-RLM/edit)
for a description. External applications should set the allowance first to `0`,
before changing its value.

For the `nomin` token, third party applications must be aware that fees are
added to the transfer value. For example, a user, `a` can call `approve()` to
address `b` with a value of `10 nomins`. If an application subsequently tries
to `transfer` (on behalf of `b`) for `10 nomins` from `a`, the transfer will
revert, due to the fees being added on top of the value.

### Recommendations

This section details our recommendations for the contracts tested. The
recommendations are classified into three categories of severity; high,
moderate and low.

#### High

##### Vote Manipulation via Improper Variable Resetting

**Court.sol [410,448,477]** - The combination of functions `cancelVote`,
`closeVote` and/or `vetoVote` allow attackers to collect an arbitrary number of
votes, to be used on a target account at a future point. This vulnerability
also allows attackers to lock other user's votes to prevent them from
participating in other motions. The vulnerability originates from the fact that
`closeVote` and `vetoVote` zeros votes against the target but does not zero the
record of votes made by individual accounts. See **Potential Attacks** for
examples of how to exploit this vulnerability. The logic in these functions
should be modified.

 * [x] Addressed in `540006e`: An index for each motion is introduced which
 resolves the above issue.

##### Inaccurate Vote Calculation due to Outdated Average Balance

**Court.sol [379, 381]** - The calculation of vote weight relies on a
potentially outdated average balance. This allows users to accumulate an
arbitrary amount of votes (provided no one transfers them `havvens` or updates
their accounts). Before assigning the weight variable, the
`recomputeLastAverageBalance()` of the `Havven` contract should be called to
update user's balances and hence weights for voting. See **Potential Attacks**
for further details.

 * [x] Addressed in `540006e`: `recomputeLastAverageBalance()` is called before
   weight calculation.

##### Token Wrapping Prevention Bypass

**Court.sol** - The purpose of this contract is to prevent token wrapper
contracts. Specially-designed contracts can easily bypass this mechanism using
proxy contracts to hold `nomins` and swapping-out these proxy contracts as
court motions begin. This could be mitigated by freezing the `havvens`
immediately after the motion is set against them, but this would require
further logic (potentially slashing conditions) in setting up motions to
prevent attackers from maliciously freezing `havvens`. Further discussion can
be found in the **Potential Attacks** section.

* [ ] Acknowledged by authors (see *Per-Contract Vulnerability Summary* section
  for author's comment).

##### Arbitrary Dependent Contract Address Modification

**Court.sol, Havven.sol, EtherNomin.sol, HavvenEscrow.sol** - Each of these
contracts allow the owner to modify the address of dependent contracts at any
time with no limitation, with the exception of the `Court.` contract where
these variables are set only in the constructor. This grants the owner
potentially undesired excessive privileges (see **Indirect Privileges** in
**Owner Privileges** for a non-exhaustive list). This also allows the owner to
trick users into running arbitrary code in standard functions (see **Potential
Attacks**). We recommend that if these privileges are necessary (e.g., to
update the contract) that they be at least bounded by time, such that users can
choose whether to participate in the upgrade or code changes. This can be done
in a two-step process, whereby the owner initially proposes a new contract
address (for `Court`, `Havven`, `HavvenEscrow`, `EtherNomin`) and then sets the
change into effect in a second transaction which must occur after a period of
time, allowing users to decide if they still wish to participate.

* [x] Comment from authors: *"Not implemented: We are comfortable with the level
  of control granted to Owner."*

#### Moderate

##### Inactive Owner Leading to User Fund Lockups

**HavvenEscrow.sol [210] - withdrawFees()** - A stagnant or absent owner (e.g.,
if the owner loses their keys) will prevent all users from withdrawing any fees
from the `HavvenEscrow` contract. This function reverts if the owner has not
withdrawn the fees from the last period. It is recommended that the logic is
adjusted to not require an active owner.


 * [x] Addressed in `540006e`: Logic has been refactored into `Havven.sol`
 allowing all users to collect fees regardless of an active owner.

#### Low

##### Insufficient Notice of Token State Owner Change

**TokenState.sol [67]** - `associatedContract` can be changed without causing
an event. This makes it difficult for the public to detect a scenario where a
malicious owner changes the `associatedContract` address to one of their
choosing, freely manipulates token balances and then sets `associatedOwner`
back to the previous address.
 
* [x] Addressed in `fa705dd`: the `TokenState` contract now emits a
  `AssociatedContractUpdated` event whenever `associatedContract` is changed.

##### [NEW] Unused ContractFeesWithdrawn Event
**HavvenEscrow.sol** - There is an event `ContractFeesWithdrawn` defined,
however it is never called. If unnecessary, remove it.

##### Insufficient Hardening of Contract Ownership Transfer
**Owner.sol** - Does not use a ["Claim
Ownership"](https://github.com/OpenZeppelin/zeppelin-solidity/blob/master/contracts/ownership/Claimable.sol)
style pattern for ownership transfer, making it possible to assign ownership to
an address out of the control of the owners.

 * [x] Addressed in `540006e`: a potential owner must call `acceptOwnership()`
   before they are instated as the owner. Note: another vulnerability has been
raised as a result of this fix (see "Potentially Dangerous setOwner()
Function").

##### Insufficient Recipient Address Validation

**ERC20FeeToken [137,163] and ERC20Token.sol [57,76]** - Add validation for the
`_to` address, to ensure it is not the `0x0` address. This will prevent tokens
being accidentally sent to `0x0`. This is a common error for users of third
party applications which default missing parameters to `0x0`.

* [x] Addressed in `540006e`: a `require()` that `to !== 0x0` is now present in
  `ExternStateProxyFeeToken` and `ExternStateProxyToken`.

##### Insufficient Transfer Fee Rate Validation

**ERC20FeeToken [72]** - The contract has a `maxTransferFeeRate` which is not
respected in the constructor. We suggest adding the validation to ensure the
`feeTransferRate` isn't artificially set higher than the maximum rate during
deployment.

* [x] Addressed in `fa705dd`: the `ExternStateProxyFeeToken` contract (which
  replaced `ERC20FeeToken`) now ensures that the initial transfer fee rate is
less than `MAX_TRANSFER_FEE_RATE`.

##### Duplicate Event Call

**HavvenEscrow.sol [219]** - The `ContractFeesWithdrawn()` event gets fired
twice with the same parameters. If this is not intentional, one should be
removed.

* [x] Addressed in `540006e`: The `ContractFeesWithdrawn` event is not called
  twice; instead it is never called at all (see "Unused ContractFeesWithdrawn
Event").


##### Lack of Vesting Periods Validation

**HavvenEscrow.sol [230] - appendVestingEntry()** - This function has no
validation around the quantities that can be added to users vesting periods. As
the contract stands, the actual `havven` balance in the `HavvenEscrow` contract
is entirely decoupled from the balances it claims to have. In principle the
owner can credit an account with more `havven` than exists (e.g.,
`totalSupply`). This can cause internal inconsistencies when the users
withdraw. We recommend enforcing that the `totalSupply` of the `Havven`
contract is at least as large as the new `totalVestedBalance` variable.

* [x] Addressed in `540006e`: `appendVestingEntry()` now requires that
  `totalVestedBalance <= havven.balanceOf(this)`.

#### General Suggestions

**Proxy.sol[107]** - The modifier `onlyOwner_Proxy` is misleading and
dangerous as it can be easily bypassed. Anyone can use the proxy contract to
call `setMessageSender()` of a `proxyable` contract. Thus, anyone can set `messageSender`
to any address, including the `owner`, in effect allowing any user to call any
function that uses the `onlyOwner_Proxy`. This modifier is not used in any contracts,
but we suggest removing the modifier in case it ever gets used in future versions.  

* [x] Addressed in `fa705dd`: the `onlyOwner_Proxy` function has been removed.

**ExternStateProxyToken.sol[120]** - There is check to ensure that the
`from` address is not `0x0`. Such a check seems unnecessary. Furthermore, the
same check is not present in `ExternStatProxyFeeToken`.

* [x] Addressed in `fa705dd`: the check that to ensure `from != 0x0` was
  removed.

**Owner.sol** - Having the `_setOwner()` function seems unnecessarily
dangerous. In the very unusual case it were called erroneously the result might
be the owner being set to `0x0` (or whatever `nominatedOwner` is). It may be
prudent to either include this logic in the `acceptOwnership` function, make
the function `private`, or check for the `0x0` address.

* [x] Addressed in `fa705dd`: `_setOwner()` was removed and it is no longer
  possible to set the `owner` to an account without first having control over
that account.

**Havven.sol** - The Havven contract store its token balances in an
external state contract (`TokenState.sol`) to simplify a process where the
Havven contract may be replaced with a newer version. The average Havven
balances (used in determining an accounts share of Nomin fees) are not stored
in this external state and would need to be either discarded or migrated
manually.

* [x] Addressed by a note from the owners: *"We are aware of this, and are
  willing to perform such manual migration steps necessary, but we are also
considering further abstractions of the contract state to pull this information
into its own auxiliary contract(s)."*

**SafeDecimalMath.sol** - The typical convention to check over/underflows is to
use the `assert()` function rather than `require()`. The `assert()` will
consume all gas of the transaction and is typically desired if an
over/underflow occurs (which shouldn't happen in normal execution). However,
the ERC20 `transfer` functions (and a number of other functions, such as
`withdrawFees()`) in these contracts, specifically rely on this
`SafeDecimalMath` to ensure withdrawals have adequate balances. We suggest the
method where an explicit `require()` is used to verify the balance of transfer
events, `asserts()` are used in the `SafeDecimalMath` logic and overflow errors
are rarely encountered. See the [OpenZeppelin
contracts](https://github.com/OpenZeppelin/zeppelin-Solidity/tree/master/contracts)
for examples.

* [x] Comment from authors: *Not Implemented: We have decided against
  implementing assert due to the extra gas costs associated.*

**Court.sol [132,133]** - Havven and Nomin addresses are not public. Users will
not easily be able to see which address is linked to this contract and
therefore which code is being run to estimate their weights.

* [x] Addressed in `540006e`: `havven` and `nomin` addresses are now public
  variables of the court contract.

**EtherNomin.sol [62,123]** - This contract does not need to import
`Havven.sol`, and the cast can be removed from the constructor.

* [x] Addressed in `540006e`: `EtherNomin.sol` no longer imports `Havven.sol`.
  There is no longer a cast in the constructor.


**Havven.sol [108]** - This contract does not need to import `Court.sol`.

* [x] Addressed in `540006e`: `Havven.sol` no longer imports `Court.sol`.

**Havven.sol** - The `lastAverageBalance` and `penultimateAverageBalance` are
public but would quite frequently be out-of-date, potentially misleading users.

* [x] Comment from authors: *Not implemented: Added warning in comments that
  these values may be out-of-date.*

**ERC20FeeToken [36]** - Use of `uint256` in contrast to otherwise consistent
`unit` usage.

* [x] Addressed in `540006e`: This is no longer present in `TokenState` (the
  contract which replaced `ERC20FeeToken`).

**EtherNomin.sol [193]** - The variable naming in the parameter could be
changed to `wei` from `eth` to accurately represent the units being passed to
the function.

* [x] Addressed in `fa705dd`: variable now has been renamed to `etherWei`
  (`wei` cannot be used as it is a reserved keyword).

**EtherNomin.sol [125]** - There is inconsistent naming in the parameters.
`initialEtherPrice` should be changed to `_initialEtherPrice` for consistent
naming.

* [x] Addressed in `fa705dd`: variable now has a `_` prefix.

**EtherNomin.sol [87,90,94]** - We suggest making these variables public as
they are important for users and applications to interact with the contract and
understand its dynamics.

* [x] Comment from authors: *Not Implemented: We don't need to access these.
  Those who wish to verify the values can do so through the source code.*

**EtherNomin.sol** - It may be prudent to allow any address to call `terminateLiquidation()`.

* [x] Comment from authors: *Not Implemented: We do not want any user other
  than Owner to be able to call terminateLiquidation()*


**Court.sol [266,512,513]** - The `Court` prefix is not required.

* [x] Addressed in `540006e`: The `Vote` enum is now accessed directly, not
  with a `Court.` prefix.

**All Contracts** - We recommend setting a fixed Solidity compiler version
rather than allowing all future versions, in the very low chance there is
backwards compatibility issues with future versions.

* [x] Addressed in `fa705dd`: compiler versions are now fixed.

#### Remarks

We note the complexity of the `Court` contract and its current inadequacies in
preventing token wrapping. Contracts can be prevented from using `nomins` by
adding the requirement that `tx.origin == msg.sender` to `transfer()`, for
example. This will also restrict multi-sig wallets and all other contracts from
using `nomins` but is potentially a simpler solution than employing a voting
mechanism.

We also note that the `Court` contract allows accounts to vote when motions are
set against them. This can be beneficial as it prevents malicious users setting
motions against the foundation which hold a significant amount of tokens. The
mathematical analysis of such attacks is outside the scope of this audit and we
simply point this out to ensure that this logic is expected.

### Potential Attacks

In this section we elucidate the vulnerabilities mentioned in the
recommendation section by giving some potential attacks that can be employed
with the current implementation of the contracts.

#### Owner Forcing Users to Run Arbitrary Code

There are a number of areas where this form of attack can work within the
Havven contracts. Let us take **Havven.sol [419]** as an example:

This line of code is executed when there is a rollover period and can occur
when a user users calls `transfer()`. To illustrate the issue with this line,
let us take an unimaginative (potentially not realistic) scenario that someone
has written an ERC20 token which uses `tx.origin` in their transfer function
rather than `msg.sender`. In this scenario, let an arbitrary `havven` holder
hold 100 tokens of this ERC20 token. A malicious owner of the `havven` contract
can create a contract, with a fallback function (or a `feePool()` function)
that calls `transfer()` on the made up ERC20 token and sends the balance to the
`havven` contract owner. The owner then sets this contract to be the `nomin`
contract. When an unsuspecting user runs `checkFeePeriodRollOver()` during a
rollover period, they are forced to run the code in the malicious contract (the
fallback function if no `feePool()` function exists), which will send their
ERC20 token balance to the `owner` of the `havven` contract. Thus, the owner
has performed an attack on users of the platform utilising external contracts.

Although this particular scenario may not be realistic (we hope future Solidity
developers don't use `tx.origin` in this manner), the possibilities of
arbitrary code execution which can target any arbitrary contracts that has or can
be built on Ethereum is a very large attack surface. A recent real-world
example of hiding the executing code by changing the address of a contract is
with this [honey pot
example](https://www.reddit.com/r/ethdev/comments/7x5rwr/tricked_by_a_honeypot_contract_or_beaten_by/).

#### Token Wrapper Avoiding the Court Mechanism

A token wrapper can be built which uses disposable proxy contracts to store its
collected `nomins`. Consider a wrapper contract `A` which initially stores its
`nomins` in a "proxy contract" `B`.

`A --controls--> B --calls--> EtherNomin`

As is common with token wrappers, users avoid fees by transferring token
entitlements internally inside `A` (unbeknownst to the `EtherNomin` contract).
When user wishes to exit the wrapper, a call on contract `A` will transfer the
tokens from `B` to an user-specified address.

Freezing the address of `A` would be ineffective, as the tokens are held by
contract `B`. Freezing the address of `B` would be effective, but contract `A`
could read the public `Court` state and detect a vote approximately four weeks
before the `B` address can be frozen. In this four week voting period, contract
`A` could spawn a new proxy contract, `C`, and execute a transfer on the
`EtherNomin` contract of the balance of `B` to `C`. The `B` contract would be
discarded and the voting process would need to begin again on `C`, and so on.

`A --controls--> C --calls--> EtherNomin`

As discussed previously, an immediate freeze upon a confiscation motion would
prevent `B` from transferring its `nomin` to `C`. Such functionality would be
subject to abuse and would require further thought.

Considering the deterministic nature of contract addresses, one could submit a
succinct, on-chain verifiable proof that `C` was created by frozen address `A`
and have it immediately frozen (e.g., `proveIsProxyContract(address
blacklisted, uint nonce)`). Unfortunately though, this is not a magic bullet as
an almost endlessly complex tree of contract creation could be constructed,
such that `C` is not created by `A`, but by `B` or arbitrary contract `Z`.

### Owner Account Privileges

The authors have provided the following note:

*"We understand that there are a significant number of direct and indirect
priveleges for the Owner account. We are comfortable with the level of control
in this version of Havven. In future, upgraded versions of the contracts will
relinquish control."*

Considering this, we will mark all items in this section as resolved to
acknowledge the authors intent. However, this does not indicate that the level
of control of `owner` has been reduced.

#### Direct

**The following are `Nomin` specific direct privileges:**

**Proxy.sol [43] - _setTarget()** - The owner can set the
`target` to any address of their choosing and disrupt the
Havven system.

**TokenState.sol [63] - setAssociatedContract()** - The owner can set the
`associatedContract` to any address of their choosing and manipulate token
balances arbitrarily.

* [x] The author is comfortable with the level of control granted to `owner`

**EtherNomin.sol [147,155,163]** The owner can set the `oracle`, `court` and
`beneficiary` addresses. Therefore, the owner can run any arbitrary code
whenever these addresses are referenced by replacing them with a malicious
address.

* [x] The author is comfortable with the level of control granted to `owner`

**EtherNomin.sol [171] - setPoolFeeRate()** - The owner can set an arbitrary
pool fee rate, from 0 to 100%.

* [x] The author is comfortable with the level of control granted to `owner`

**EtherNomin.sol [413] - burn()** - The owner can burn any amount of `nomins`
if they exist.

* [x] The author is comfortable with the level of control granted to `owner`

**EtherNomin.sol [482] - forceLiquidation()** - The owner can force the
liquidation of the `nomin` contract at any time.

* [x] The author is comfortable with the level of control granted to `owner`

**EtherNomin.sol [180] - setStalePeriod()** - The owner can set the stale
period to an arbitrary value.

* [x] The author is comfortable with the level of control granted to `owner`

The following are `Court` specific direct privileges:

**Court.sol [210,220,232,241,249]** - The owner can set an arbitrary
`minStandingBalance` (as a result prevent anyone from starting motions). The
owner can set the `votingPeriod`, `confirmationPeriod`, `requiredParticipation`
and `requiredMajority`. The owner effectively controls all dynamics of voting,
with some restrictions on the last three variables.

* [x] The author is comfortable with the level of control granted to `owner`

**The following are `Havven` specific direct privileges:**

**Havven.sol [182, 189, 196, 222]** - The owner can set the `nomin` and
`escrow` contract to any arbitrary address. The owner distributes all `havvens`
that initially come into existence. The owner can set the
`targetFeePeriodDurationSeconds` variable.

* [x] The author is comfortable with the level of control granted to `owner`

**The following are `HavvenEscrow` specific direct privileges:**

**HavvenEscrow.sol [169, 177]** - The owner can set the `havven` and `nomin`
contract addresses to any arbitrary address at any time.

* [x] The author is comfortable with the level of control granted to `owner`

**HavvenEscrow.sol [230] - purgeAccount()** - The owner can delete any vesting
account balance and remove them from the contract at any time without
restriction.

* [x] The author is comfortable with the level of control granted to `owner`

#### Indirect

**The following are `nomin` specific indirect privileges:**

**EtherNomin.sol [544] - confiscateBalance()** - The owner can confiscate
anyone's `nomins` at will and freeze their accounts. This function has a
require which checks `msg.sender = court`. As the owner can arbitrarily change
court, they can easily create a wrapper contract passing all the requirements,
then set the `court` variable to this contract and confiscate any users
balances.

* [x] The author is comfortable with the level of control granted to `owner`

**EtherNomin.sol [375] - updatePrice()** - The owner can set any arbitrary
price for `nomins`. They may change the oracle address to any address and
therefore set the price to any arbitrary value.

* [x] The author is comfortable with the level of control granted to `owner`

**EtherNomin.sol [393] - issue()** - The owner can create `nomins` at
manipulated prices. This function allows `nomins` to be created provided a
collateralisation ratio is maintained. As the owner can can adjust the
`etherPrice` at will, they can adjust the collateralisation ratio to manipulate
the collateralisation cost of `nomins`.

* [x] The author is comfortable with the level of control granted to `owner`

**EtherNomin.sol [432] - buy()** - The owner can prevent any users from
purchasing `nomins` at any time. This can be achieved by setting the
`stalePeriod` to a very large value or by forcing liquidation.

* [x] The author is comfortable with the level of control granted to `owner`

**ERC20FeeToken.sol [200] - withdrawFee()** - The owner can withdraw any fees
from the `nomin` contract at any time. The owner can change the `feeAuthority`
variable which is the only requirement of this function. The owner creates a
wrapper contract to call this function at will.

* [x] The author is comfortable with the level of control granted to `owner`


**The following are `Havven` specific indirect privileges:**

**Havven.sol [297]** - The owner can prevent any individual user or all users
from withdrawing any fees, and force users to run arbitrary code. This is done
by changing the `nomin` contract address to a malicious address.

* [x] The author is comfortable with the level of control granted to `owner`

The following are `Court` specific indirect privileges:

**Court.sol [347]** - The owner can pass or fail any confiscation motion. The
owner can adjust the `havven` contract which specifies the `weight` for votes.
The owner can give themselves arbitrary high votes and everyone else nothing,
by replacing `havven` with a malicious contract.

* [x] The author is comfortable with the level of control granted to `owner`

**Court.sol [347]** - The owner can prevent specific or all confiscation
motions. By manipulating the `havven` address the owner can fail this
requirement for specific or all users.  

* [x] The author is comfortable with the level of control granted to `owner`

**Court.sol [347]** - The owner can get users to run arbitrary code when they
call `beginConfiscationMotion` by replacing either `nomin` or `havven` with a
malicious contract address.

* [x] The author is comfortable with the level of control granted to `owner`

**The following are `HavvenEscrow` specific indirect privileges:**

**HavvenEscrow.sol [161] - feePool()** - The owner can set the `feePool`
variable to any arbitrary number. As `feePool()` returns
`nomin.balanceOf(this)`, and the owner can change `nomin` to any address, the
owner can create a contract with a function `balanceOf` that returns an
arbitrary value. The owner then sets `nomin` to this contract to specify any
`feePool()` they wish.

* [x] The author is comfortable with the level of control granted to `owner`

**HavvenEscrow.sol [187] - remitFees()** - The owner can remit fees of the
`HavvenEscrow` contract. The owner can set the `havven` address to any address
and as such can create a wrapper contract to pass the single requirement.

* [x] The author is comfortable with the level of control granted to `owner`

**HavvenEscrow.sol [187] - remitFees()** - The owner can get users to run
arbitrary code and create attacks external to the Havven system for users (see
*potential attacks* for further details). The owner can set `nomin` to an
arbitrary (malicious) contract such that when a user runs `remitFees`,
`nomin.dontateToFeePool()` runs arbitrary malicious code.  

* [x] The author is comfortable with the level of control granted to `owner`

**HavvenEscrow.sol [210] - withdrawFees()** - The owner can prevent all users
from withdrawing their fees. If the owner hasn't withdrawn in the last period,
this function will throw as only the owner can call `withdrawFeePool()`.

* [x] The author is comfortable with the level of control granted to `owner`

**HavvenEscrow.sol [222]** - The owner can arbitrarily specify any individual
users or all user's shares and entitlements in the `HavvenEscrow` contract. The
entitlement a participant has is calculated by referencing an external contract
which can be arbitrarily changed by the owner and hence the owner can set this
value arbitrarily.  

* [x] The author is comfortable with the level of control granted to `owner`

#### Gas Reduction Changes

**LimitedSetup.sol** - `constructionTime + setupDuration` is calculated
each time the modifier is run, even though it will never change after the
contract is deployed. Long-term gas savings could be achieved by doing this
addition in the constructor.

* [x] Addressed in `fa705dd`: the computation is performed once in the
  constructor and stored in `setupExpiryTime`.

Initialising variables costs gas. Variables that are initialised to their
default values cost unnecessary gas. Removing these initialisation will reduce
the gas costs of the contract. Below is a list of initialisations that could be
removed to reduce the gas costs.  

 - **ERC20FeeToken.sol [53]**
 - **EtherNomin.sol [81]**
 - **HavvenEscrow.sol [299]**

* [x] Addressed in `540006e`: Variables are no longer initialised to zero.

**Court.sol [441]** - This line serves no purpose and can be removed to save gas.

* [x] Addressed in `540006e`: Line is no longer present.

**ERC20FeeToken.sol [151-153] and ERC20Token.sol [84-86]** - These lines add
gas for every non-zero transaction. Can be removed.

* [x] Addressed in `540006e`: These "gas-saving" checks are no longer present.

In **SafeDecimalMath** the safe functions call other checking functions, such
as **addIsSafe**. There is gas overhead in calling other functions, writing
these as a single function reduces gas costs.

* [x] Addressed in `540006e`: These function calls have been resolved.


### Tests

The following tests were implemented during the audit. Tests were developed
using [truffle](http://truffleframework.com/) and
[ganache-cli](https://github.com/trufflesuite/ganache-cli).

To run the tests, navigate to the `truffle` directory and run `$ truffle test`.

```
Contract: Court scenarios
    ✓ should allow for a confiscation with 100% votes in favour and owner approval (3316ms)
    ✓ should not allow for a confiscation which has less than the required majority (3310ms)
    ✓ should not allow for a confiscation motion from an account with less than 100 havven (2269ms)

  Contract: Havven scenarios
    ✓ should allow vested tokens to be withdrawn (6239ms)
    ✓ should distribute fees evenly if there are only two equal escrowed havven holders (2804ms)
    ✓ should distribute fees evenly if there are only two equal havven holders (2313ms)
    ✓ should not allow double fee withdrawal (1403ms)
    ✓ should roll over uncollected fees into the next fee period (2962ms)
    ✓ should not give any fees to someone who dumped all havvens in the penultimate fee period (3444ms)
    ✓ should store an accurate penultimate avg. balance (3427ms)
    ✓ should show an average balance of half if tokens are moved halfway though the fee period (3536ms)

  Contract: Ownable
    ✓ should set the owner to 0x0 if _setOwner() is called (109ms)

  Contract: EtherNomin basic functionality
    ✓ should use the values supplied in the constructor (133ms)
    ✓ should return 4500 from a fiatValue(4.5) call if etherPrice is 1000 (141ms)
    ✓ should return a fiatBalance of 2000 if etherPrice is 1000 and the contract holds 2 ETH (232ms)
    ✓ should return 4.5 from a etherValue(4500) call if etherPrice is 1000 (86ms)
    ✓ should return false from priceIsStale() if the price was recently updated (343ms)
    ✓ should return true from priceIsStale() if the price was update more than 30 mins ago (1322ms)
    ✓ should return a ratio 3000 if there is 3 ETH in the contract, 1 nomin issued and an ETH price of $1500 (357ms)
    ✓ should determine a pool fee of 0.01 nomins on a transfer of 2 nomin (99ms)
    ✓ should return a purchase cost of $4.02 to purchase 4 nomins (108ms)
    ✓ should return a purchase cost of 0.15075 ETH to purchase 300 nomins at an ethPrice of $2000 (104ms)
    ✓ should return proceeds of $348.25 when selling 350 nomins (92ms)
    ✓ should return proceeds of 70.39625 ETH when selling 283 nomins at an ETH price of $4 (102ms)
    ✓ should return false to canSelfDestruct() if the liquidationTimestamp is in the future (330ms)
    ✓ should return true to canSelfDestruct() if the liquidationPeriod has passed (1380ms)
    ✓ should return true to canSelfDestruct() if all nomin have been returned to pool and its been 1 week since liquidation (1330ms)
    ✓ should revert if the caller of updatePrice is not the oracle (335ms)
    ✓ should set etherPrice to the supplied variable if updatePrice() is called by oracle (336ms)
    ✓ should go into auto liquidation if the price is set so low the contract becomes under-collateralised (405ms)
    ✓ should throw if replenishPool() called from not owner (194ms)
    ✓ should throw if replenishPool() called when contract is liquidating (413ms)
    ✓ should throw if replenishPool() called without sufficient collateralisation (101ms)
    ✓ should throw if replenishPool() called when ethPrice is stale (787ms)
    ✓ should update nominPool after replenishPool() (129ms)
    ✓ should throw if diminishPool() called from not owner (138ms)
    ✓ should throw if diminishing more tokens than in the pool (138ms)
    ✓ should update nominPool after a diminishPool() (190ms)
    ✓ should throw if buy() called when contract is liquidating (515ms)
    ✓ should throw if buy() is less than 1/100th of a nomin (161ms)
    ✓ should throw on buy() if price is stale (822ms)
    ✓ should update nominPool and balanceOf on successful buy (349ms)
    ✓ should update balanceOf and nominPool after sell() (321ms)
    ✓ should allow sell() when the ethPrice is stale and contract is liquidating (1240ms)
    ✓ should not allow sell() when the ethPrice is stale and contract is not liquidating (1002ms)
    ✓ should throw if selling more nomins than owned (221ms)
    ✓ should transfer eth to seller (545ms)
    ✓ should not allow a non-owner to call forceLiquidation() (101ms)
    ✓ should allow a owner to call forceLiquidation() (340ms)
    ✓ should not allow an owner to call forceLiquidation a second time (127ms)
    ✓ should not allow extendLiquidationPeriod() when not in liquidation (124ms)
    ✓ should extend liquidation period by 30 days (223ms)
    ✓ should not allow the liquidationPeriod to be extended to 180.1 days (170ms)
    ✓ should not allow a terminateLiquidation() call when not liquidating (137ms)
    ✓ should not allow a terminateLiquidation() call when not liquidating (148ms)
    ✓ should not allow liquidation termination when the collat ratio is too low and totalSupply > 0 (507ms)
    ✓ should allow liquidation termination when the collat ratio is too low but totalSupply is 0 (454ms)
    ✓ should allow liquidation termination when totalSupply > 0 but collatRatio is > 1 (429ms)

  Contract: Test Rig
    ✓ should build a test rig without throwing (425ms)
    ✓ should allow for the reading of nomin etherPrice after deployment (532ms)

  Contract: Variable Return Data
    ✓ should allow for variable return data (194ms)
    ✓ should allow a call directly to the proxy using the .at() method (140ms)


  62 passing (55s)
```

_These tests are a by-product of the audit do not represent comprehensive unit
testing._

## Audit information

### Limitations

Sigma Prime makes all effort, but holds no responsibility for the findings of
this audit. Sigma Prime does not provide any guarantees relating to the
function of the smart contract. Sigma Prime makes no judgements on, or provides
audit on, the viability of the token sale, the underlying business model or the
individuals involved in the token sale.


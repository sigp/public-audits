const deployer = require("../deployer.js");
const BigNumber = require("bignumber.js");
const BN = require("bn.js");
const SupplySchedule = artifacts.require("./SupplySchedule.sol");
const SafeDecimalMath = artifacts.require("./SafeDecimalMath.sol");
const w3utils = require('web3-utils');
const zeroAddress = '0x0000000000000000000000000000000000000000'
const truffleAssert = require('truffle-assertions');

const helpers = require("../testHelpers.js");
const synthetixHelpers = require("../synthetixHelpers.js");
const toUnit = synthetixHelpers.toUnit;
const assertRevert = helpers.assertRevert;
const assertBNEqual = helpers.assertBNEqual;
const allocateSynthetixsTo = synthetixHelpers.allocateSynthetixsTo;
const toBN = web3.utils.toBN;
const toBigNumber = helpers.toBigNumber;
const withinPercentageOf = helpers.withinPercentageOf;
const getTimestamp = helpers.timestamp;
const fastForward = helpers.fastForward;
const assertEventEqual = helpers.assertEventEqual;
/*
 * Minor Helpers
 */

 const toBytes32 = key => w3utils.rightPad(w3utils.asciiToHex(key), 64);


const days = x => x * 60 * 60 * 24;
assert(days(2) == 172800, "days() is incorect");

const hours = x => x * 60 * 60;
assert(hours(2) == 7200, "hours() is incorrect");

const [sUSD, sETH, ETH, SNX] = ['sUSD', 'sETH', 'ETH', 'SNX'].map(toBytes32);


const MINUTE = 60;
const HOUR = 3600;
const DAY = 86400;
const WEEK = 604800;
const MONTH = 2629743; // 1 month = 30.437 days
const YEAR = 31536000;

const ONE_ETH = toUnit('1');
const TWO_ETH = toUnit('2');
const ISSUANCE_RATIO = toUnit('0.666666666666666667');

contract("DelegateApprovals", async function(accounts) {
  before("deploy test rig", async function() {
    // Save ourselves from having to await deployed() in every single test.
    // We do this in a beforeEach instead of before to ensure we isolate
    // contract interfaces to prevent test bleed.

    this.rig = await deployer.deployTestRig(accounts);
    this.supplySchedule = this.rig.supplySchedule;
    this.synthetix = this.rig.synthetix;
    this.synthetixTokenState = this.rig.synthetixTokenState;
    this.owner = this.rig.accounts.owner;
    this.oracle = this.rig.accounts.oracle;
    this.depot = this.rig.depot;
    this.ethcol = this.rig.ethcol;
    this.sUSD = this.rig.synths[toBytes32('sUSD')];
    this.sETH = this.rig.synths[toBytes32('sETH')];
    this.exchangeRates = this.rig.exchangeRates;
    this.synthetixProxy = this.rig.synthetixProxy;
    this.delegates = this.rig.delegateApprovals;
    this.delegateStorage = this.rig.delegateEternalStorage;
    this.feePool = this.rig.feePool;
    this.exchanger = this.rig.exchanger;
    this.resolver = this.rig.resolver;
    this.issuer = this.rig.issuer;
    this.rewardsDistribution = this.rig.rewardsDistribution;

    // Call setResolverAndSyncCache on all relevant contracts

    await this.synthetix.setResolverAndSyncCache(this.resolver.address, {from: this.owner});
    await this.feePool.setResolverAndSyncCache(this.resolver.address, {from: this.owner});
    await this.depot.setResolverAndSyncCache(this.resolver.address, {from: this.owner});
    await this.sUSD.setResolverAndSyncCache(this.resolver.address, {from: this.owner});
    await this.sETH.setResolverAndSyncCache(this.resolver.address, {from: this.owner});
    await this.exchanger.setResolverAndSyncCache(this.resolver.address, {from: this.owner});
    await this.issuer.setResolverAndSyncCache(this.resolver.address, {from: this.owner});

    alice = accounts[5];
    bob = accounts[6];
    carol = accounts[7];
    david = accounts[8];
    eve = accounts[9];

    timestamp = await getTimestamp()

    // update Rates
    await this.exchangeRates.updateRates([SNX, sETH, ETH], ['0.1', '172', '172'].map(toUnit), timestamp, {
			from: this.oracle,
		});

    // Update rate stale period for exchangeRates
    await this.exchangeRates.setRateStalePeriod(YEAR, {
			from: this.owner,
		});

    // Let's give Alice, Bob and Carol some SNX tokens
    // We made sure that the owner has some in the deployer (owner is allocated half the supply)

    await this.synthetix.transfer(alice, toUnit('10000'), {from: this.owner});
    await this.synthetix.transfer(bob, toUnit('10000'), {from: this.owner});
    await this.synthetix.transfer(carol, toUnit('10000'), {from: this.owner});
    await this.synthetix.transfer(david, toUnit('10000'), {from: this.owner});
    await this.synthetix.transfer(eve, toUnit('10000'), {from: this.owner});

    // Let's get alice, bob, and carol to issue Synths (100 sUSD)

    await this.synthetix.issueSynths(toUnit(100), {from: alice})
    await this.synthetix.issueSynths(toUnit(100), {from: bob})
    await this.synthetix.issueSynths(toUnit(100), {from: carol})

    // Transfer SNX to the reward distribution contract

    await this.synthetix.transfer(this.rewardsDistribution.address, toUnit('200000'), {from: this.owner});

  });
  beforeEach("snapshot", async function() {
    // set minimumStakeTime on issue and burning to 0
    await this.issuer.setMinimumStakeTime(0, {from: this.owner});

    // This reduces the need to fully deploy each time (quicker),
    // but also reverts changes to evm timestamps between tests
    // Give the depot contract some SNX
    this.mainSnapShot = await helpers.takeSnapShot();
  });
  afterEach("restore snapshot", async function() {
    await helpers.revertTestRPC(this.mainSnapShot);
    this.mainSnapShot = undefined;
  });

  context("Testing DelegateApprovals Contract", async function() {

    it("Should deploy successfully with relevant contract initialized", async function() {
      assert.strictEqual((await this.delegates.eternalStorage()), this.delegateStorage.address);
      assert.strictEqual((await this.delegates.owner()), this.owner);
    });

    it("Should not allow anyone non-owners to change the eternal storage contract", async function() {
      await assertRevert(this.delegates.setEternalStorage(this.oracle, {from: accounts[4]}));
      assert.strictEqual((await this.delegates.eternalStorage()), this.delegateStorage.address);
    });

    it("Should allow the owner to change the eternal storage contract", async function() {
      const tx = await this.delegates.setEternalStorage(this.oracle, {from: this.owner});
      assertEventEqual(tx, 'EternalStorageUpdated', { newEternalStorage: this.oracle });
      assert.strictEqual((await this.delegates.eternalStorage()), this.oracle);
    });

    it("Should not allow the owner to set the eternal storage to the zero address", async function() {
      await assertRevert(this.delegates.setEternalStorage(zeroAddress, {from: this.owner}));
    });

    it("Should allow an arbitrary user to act as a delegate for multiple users", async function() {
      await this.delegates.approveIssueOnBehalf(alice, {from: carol});
      await this.delegates.approveIssueOnBehalf(bob, {from: carol});
      assert.strictEqual((await this.delegates.canIssueFor(carol, alice)), true);
      assert.strictEqual((await this.delegates.canIssueFor(carol, bob)), true);
      assert.strictEqual((await this.delegates.canIssueFor(alice, carol)), false);
      assert.strictEqual((await this.delegates.canIssueFor(bob, carol)), false);
      assert.strictEqual((await this.delegates.canIssueFor(bob, alice)), false);
      assert.strictEqual((await this.delegates.canIssueFor(alice, bob)), false);
    });

    it("Should allow arbitrary users to approve arbitrary addresses to issue synths on their behalf", async function() {
      const tx = await this.delegates.approveIssueOnBehalf(bob, {from: alice});
      assertEventEqual(tx, 'Approval', {
        authoriser: alice,
        delegate: bob,
        action: toBytes32('IssueForAddress'),
      });
      assert.strictEqual((await this.delegates.canIssueFor(alice, bob)), true);
      assert.strictEqual((await this.delegates.canIssueFor(carol, bob)), false);
      assert.strictEqual((await this.delegates.canIssueFor(carol, alice)), false);
    });

    it("Should allow arbitrary users to approve arbitrary addresses to burn synths on their behalf", async function() {
      const tx = await this.delegates.approveBurnOnBehalf(bob, {from: alice});
      assertEventEqual(tx, 'Approval', {
        authoriser: alice,
        delegate: bob,
        action: toBytes32('BurnForAddress'),
      });
      assert.strictEqual((await this.delegates.canBurnFor(alice, bob)), true);
      assert.strictEqual((await this.delegates.canBurnFor(carol, bob)), false);
      assert.strictEqual((await this.delegates.canBurnFor(carol, alice)), false);
    });

    it("Should allow arbitrary users to approve arbitrary addresses to claim fees on their behalf", async function() {
      const tx = await this.delegates.approveClaimOnBehalf(bob, {from: alice});
      assertEventEqual(tx, 'Approval', {
        authoriser: alice,
        delegate: bob,
        action: toBytes32('ClaimForAddress'),
      });
      assert.strictEqual((await this.delegates.canClaimFor(alice, bob)), true);
      assert.strictEqual((await this.delegates.canClaimFor(carol, bob)), false);
      assert.strictEqual((await this.delegates.canClaimFor(carol, alice)), false);
    });

    it("Should allow arbitrary users to approve arbitrary addresses to exchange on their behalf", async function() {
      const tx = await this.delegates.approveExchangeOnBehalf(bob, {from: alice});
      assertEventEqual(tx, 'Approval', {
        authoriser: alice,
        delegate: bob,
        action: toBytes32('ExchangeForAddress'),
      });
      // assert.equal(w3utils.toAscii(event.args.action).replace(/\u0000/g, ''), "ExchangeForAddress");
      assert.strictEqual((await this.delegates.canExchangeFor(alice, bob)), true);
      assert.strictEqual((await this.delegates.canExchangeFor(carol, bob)), false);
      assert.strictEqual((await this.delegates.canExchangeFor(carol, alice)), false);
    });

    it("Should allow arbitrary users to approve arbitrary addresses for all operations", async function() {
      const tx = await this.delegates.approveAllDelegatePowers(alice, {from: carol});
      assertEventEqual(tx, 'Approval', {
        authoriser: carol,
        delegate: alice,
        action: toBytes32('ApproveAll'),
      });
      assert.strictEqual((await this.delegates.canIssueFor(carol, alice)), true);
      assert.strictEqual((await this.delegates.canBurnFor(carol, alice)), true);
      assert.strictEqual((await this.delegates.canClaimFor(carol, alice)), true);
      assert.strictEqual((await this.delegates.canExchangeFor(carol, alice)), true);
    });

    it("Should not allow arbitrary users that were previously approved and then removed to approve arbitrary addresses for all operations", async function() {
      await this.delegates.approveAllDelegatePowers(alice, {from: carol});
      const tx = await this.delegates.removeAllDelegatePowers(alice, {from: carol});
      assertEventEqual(tx, 'WithdrawApproval', {
        authoriser: carol,
        delegate: alice,
        action: toBytes32('ApproveAll'),
      });
      assert.strictEqual((await this.delegates.canIssueFor(carol, alice)), false);
      assert.strictEqual((await this.delegates.canBurnFor(carol, alice)), false);
      assert.strictEqual((await this.delegates.canClaimFor(carol, alice)), false);
      assert.strictEqual((await this.delegates.canExchangeFor(carol, alice)), false);
    });

    it("Should allow users to approve a single delegate power and have remove all delegate powers work as expected", async function() {
      await this.delegates.approveIssueOnBehalf(alice, {from: carol});
      await this.delegates.approveExchangeOnBehalf(alice, {from: carol});
      assert.strictEqual((await this.delegates.canIssueFor(carol, alice)), true);
      assert.strictEqual((await this.delegates.canBurnFor(carol, alice)), false);
      assert.strictEqual((await this.delegates.canClaimFor(carol, alice)), false);
      assert.strictEqual((await this.delegates.canExchangeFor(carol, alice)), true);
      await this.delegates.removeAllDelegatePowers(alice, {from: carol});
      assert.strictEqual((await this.delegates.canIssueFor(carol, alice)), false);
      assert.strictEqual((await this.delegates.canBurnFor(carol, alice)), false);
      assert.strictEqual((await this.delegates.canClaimFor(carol, alice)), false);
      assert.strictEqual((await this.delegates.canExchangeFor(carol, alice)), false);
      await this.delegates.approveBurnOnBehalf(alice, {from: carol});
      await this.delegates.approveClaimOnBehalf(alice, {from: carol});
      assert.strictEqual((await this.delegates.canIssueFor(carol, alice)), false);
      assert.strictEqual((await this.delegates.canBurnFor(carol, alice)), true);
      assert.strictEqual((await this.delegates.canClaimFor(carol, alice)), true);
      assert.strictEqual((await this.delegates.canExchangeFor(carol, alice)), false);
      await this.delegates.removeAllDelegatePowers(alice, {from: carol});
      assert.strictEqual((await this.delegates.canIssueFor(carol, alice)), false);
      assert.strictEqual((await this.delegates.canBurnFor(carol, alice)), false);
      assert.strictEqual((await this.delegates.canClaimFor(carol, alice)), false);
      assert.strictEqual((await this.delegates.canExchangeFor(carol, alice)), false);
      await this.delegates.approveAllDelegatePowers(alice, {from: carol});
      assert.strictEqual((await this.delegates.canIssueFor(carol, alice)), true);
      assert.strictEqual((await this.delegates.canBurnFor(carol, alice)), true);
      assert.strictEqual((await this.delegates.canClaimFor(carol, alice)), true);
      assert.strictEqual((await this.delegates.canExchangeFor(carol, alice)), true);
    });

    it("Should allow arbitrary users to remove approval to issue", async function() {
      const tx_1 = await this.delegates.approveIssueOnBehalf(bob, {from: alice});
      assertEventEqual(tx_1, 'Approval', {
        authoriser: alice,
        delegate: bob,
        action: toBytes32('IssueForAddress'),
      });
      assert.strictEqual((await this.delegates.canIssueFor(alice, bob)), true);
      const tx_2 = await this.delegates.removeIssueOnBehalf(bob, {from: alice});
      assertEventEqual(tx_2, 'WithdrawApproval', {
        authoriser: alice,
        delegate: bob,
        action: toBytes32('IssueForAddress'),
      });
      assert.strictEqual((await this.delegates.canIssueFor(alice, bob)), false);
    });

    it("Should allow arbitrary users to remove approval to burn", async function() {
      await this.delegates.approveBurnOnBehalf(bob, {from: alice});
      assert.strictEqual((await this.delegates.canBurnFor(alice, bob)), true);
      const tx = await this.delegates.removeBurnOnBehalf(bob, {from: alice});
      assertEventEqual(tx, 'WithdrawApproval', {
        authoriser: alice,
        delegate: bob,
        action: toBytes32('BurnForAddress'),
      });
      assert.strictEqual((await this.delegates.canBurnFor(alice, bob)), false);
    });

    it("Should allow arbitrary users to remove approval to claim", async function() {
      const tx_1 = await this.delegates.approveClaimOnBehalf(bob, {from: alice});
      assertEventEqual(tx_1, 'Approval', {
        authoriser: alice,
        delegate: bob,
        action: toBytes32('ClaimForAddress'),
      });
      assert.strictEqual((await this.delegates.canClaimFor(alice, bob)), true);
      const tx_2 = await this.delegates.removeClaimOnBehalf(bob, {from: alice});
      assertEventEqual(tx_2, 'WithdrawApproval', {
        authoriser: alice,
        delegate: bob,
        action: toBytes32('ClaimForAddress'),
      });
      assert.strictEqual((await this.delegates.canClaimFor(alice, bob)), false);
    });

    it("Allows users to remove approvals to non-existing delegates", async function() {
      const tx_1 = await this.delegates.approveExchangeOnBehalf(bob, {from: alice});
      assertEventEqual(tx_1, 'Approval', {
        authoriser: alice,
        delegate: bob,
        action: toBytes32('ExchangeForAddress'),
      });
      assert.strictEqual((await this.delegates.canExchangeFor(alice, bob)), true);
      const tx_2 = await this.delegates.removeExchangeOnBehalf(carol, {from: alice});
      truffleAssert.eventNotEmitted(tx_2, 'WithdrawApproval');
    });

  });

  context("Testing Exchanger Contract", async function() {

    it("Allows delegates to exchange on behalf of an arbitrary user through the synthetix exchange", async function() {
      await this.delegates.approveExchangeOnBehalf(bob, {from: alice});
      assert(await this.sETH.balanceOf(alice) == 0);
      await this.synthetix.exchangeOnBehalf(alice, sUSD, toUnit(10), sETH, {from: bob});
      assert(await this.sETH.balanceOf(alice) > 0);
    });

    it("Should not allow delegated exchanges if account has not been approved by user", async function() {
      await assertRevert(this.synthetix.exchangeOnBehalf(bob, sUSD, toUnit(10), sUSD, {from: alice}));
    });

  });

  context("Testing Issuer and Synthetix Contracts", async function() {

    it("Allows delegates to issue synths on behalf of an arbitrary user through the synthetix exchange", async function() {
      await this.delegates.approveIssueOnBehalf(bob, {from: david});
      assert(await this.sUSD.balanceOf(david) == 0);
      await this.synthetix.issueSynthsOnBehalf(david, toUnit(10), {from: bob});
      assert(await this.sUSD.balanceOf(david) > 0);
    });

    it("Should not allow delegated issuance if account has not been approved by user", async function() {
      await assertRevert(this.synthetix.issueSynthsOnBehalf(david, toUnit(10), {from: alice}));
    });

    it("Allows delegates to issue the maximum number of synths on behalf of an arbitrary user through the synthetix exchange", async function() {
      await this.delegates.approveIssueOnBehalf(bob, {from: eve});
      assert(await this.sUSD.balanceOf(eve) == 0);

      await this.synthetix.issueMaxSynthsOnBehalf(eve, {from: bob});
      assert(await this.sUSD.balanceOf(eve) > 0);
    });

    it("Should not allow delegated issuance if account has not been approved by user", async function() {
      await assertRevert(this.synthetix.burnSynthsOnBehalf(david, toUnit(10), {from: alice}));
    });

    it("Allows delegates to burn synth on behalf of an arbitrary user through the synthetix exchange", async function() {
      await this.delegates.approveIssueOnBehalf(bob, {from: david});
      assert(await this.sUSD.balanceOf(david) == 0);
      await this.synthetix.issueSynthsOnBehalf(david, toUnit(10), {from: bob});
      assert(await this.sUSD.balanceOf(david) > 0);
      await this.delegates.approveBurnOnBehalf(bob, {from: david});
      await this.synthetix.burnSynthsOnBehalf(david, toUnit(10), {from: bob});
      assert(await this.sUSD.balanceOf(david) == 0);
    });

    it("Allows delegate to issue synths on behalf of user and another delegate to burn synths on behalf of the same user", async function() {
      await this.delegates.approveIssueOnBehalf(bob, {from: david});
      assert(await this.sUSD.balanceOf(david) == 0);
      await this.synthetix.issueSynthsOnBehalf(david, toUnit(10), {from: bob});
      assert(await this.sUSD.balanceOf(david) > 0);
      await this.delegates.approveBurnOnBehalf(bob, {from: eve});
      await assertRevert(this.synthetix.burnSynthsOnBehalf(eve, toUnit(10), {from: bob}));
      assert(await this.sUSD.balanceOf(eve) == 0);
    });

    it("Should not allow a non-approved delegate to burn synths on behalf of a user", async function() {
      await this.delegates.approveIssueOnBehalf(bob, {from: david});
      await this.synthetix.issueSynthsOnBehalf(david, toUnit(10), {from: bob});
      await this.delegates.approveBurnOnBehalf(bob, {from: alice});
      await this.delegates.approveIssueOnBehalf(bob, {from: alice});
      await this.synthetix.issueSynthsOnBehalf(alice, toUnit(10), {from: bob});
      await this.synthetix.burnSynthsOnBehalf(alice, toUnit(10), {from: bob});
      await assertRevert(this.synthetix.burnSynthsOnBehalf(alice, toUnit(10), {from: bob}));
      await this.delegates.approveBurnOnBehalf(alice, {from: david});
      await assertRevert(this.synthetix.burnSynthsOnBehalf(david, toUnit(10), {from: david}));
      await this.delegates.approveBurnOnBehalf(david, {from: david});
      await this.synthetix.burnSynthsOnBehalf(david, toUnit(10), {from: david});
    });

    it("Allows delegates to burn synth on behalf of a user to the target c-ratio through the synthetix exchange", async function() {
      await this.synthetix.issueSynths(toUnit(50), {from: david});
      await this.exchangeRates.updateRates([SNX, sETH, ETH], ['0.01', '172', '172'].map(toUnit), timestamp, {
        from: this.oracle
      });
      await this.delegates.approveBurnOnBehalf(bob, {from: david});
      await this.synthetix.burnSynthsToTargetOnBehalf(david, {from: bob});
      await this.exchangeRates.updateRates([SNX, sETH, ETH], ['0.1', '172', '172'].map(toUnit), timestamp, {
        from: this.oracle
      });
    });

    it("Allows user to burn synth to the target c-ratio through the synthetix exchange", async function() {
      await this.synthetix.issueSynths(toUnit(50), {from: david});
      await this.exchangeRates.updateRates([SNX, sETH, ETH], ['0.01', '172', '172'].map(toUnit), timestamp, {
        from: this.oracle
      })
      await this.synthetix.burnSynthsToTarget({from: david});
      await this.exchangeRates.updateRates([SNX, sETH, ETH], ['0.1', '172', '172'].map(toUnit), timestamp, {
        from: this.oracle
      })
    });

  });

  context("Testing FeePool Contract", async function() {
    it("Allows only an approved delegate to claim fees on behalf of an arbitrary user through the fee pool", async function() {
      const exchange = toUnit((10).toString());
      await this.synthetix.exchange(sUSD, exchange, sETH, {from: alice});
      const feePeriodDuration = await this.feePool.feePeriodDuration();
      await fastForward(feePeriodDuration);
      const tx = await this.feePool.closeCurrentFeePeriod({from: alice});
      assertEventEqual(tx, 'FeePeriodClosed', {feePeriodId: 1});
      await assertRevert(this.feePool.claimOnBehalf(alice, {from: bob}));
      await this.delegates.approveClaimOnBehalf(bob, {from: alice});
      await this.feePool.claimOnBehalf(alice, {from: bob});
    });

    it("Allows 3 accounts who have issued the same amount to receive the same reward", async function() {

      // Alice, bob and carol have all issued 100 sUSD, they should have the same reward
      // Let's mint the inflationary supply:
      const feePeriodDuration = await this.feePool.feePeriodDuration();
      await fastForward(feePeriodDuration.toNumber() + 10);
      await this.synthetix.mint({from: this.owner});

      // Let's fast forward to the next 2 fee period and close the current fee period
      await fastForward(feePeriodDuration.toNumber() + 10);
      await this.feePool.closeCurrentFeePeriod({from: alice});

      await fastForward(feePeriodDuration.toNumber() + 10);
      await this.feePool.closeCurrentFeePeriod({from: alice});

      rewardAlice = await this.feePool.feesAvailable(alice);
      rewardBob = await this.feePool.feesAvailable(bob);
      rewardCarol = await this.feePool.feesAvailable(carol);

      assertBNEqual(rewardAlice[1], rewardBob[1]);
      assertBNEqual(rewardAlice[1], rewardCarol[1]);

    });

    it("Should allow rewards to rollover after mint", async function() {

      // Setup initial rewards
      const feePeriodDuration = await this.feePool.feePeriodDuration();
      await fastForward(feePeriodDuration.toNumber() + 10);
      const initial_rewards = (await this.supplySchedule.mintableSupply()).sub(
      await this.supplySchedule.minterReward());

      console.log("Initial Rewards to Distribute (mintable supply - minting reward): " + initial_rewards.toString())

      // Mint initial supply, adding to current period rewards
      await this.synthetix.mint({from: this.owner});

      // Close period allowing initial rewards to be distributed
      await this.feePool.closeCurrentFeePeriod({from: alice});

      let totalRewardsAvailable = await this.feePool.totalRewardsAvailable()
      let currentFeePeriod = await this.feePool.recentFeePeriods(0);
      let latestFeePeriod = await this.feePool.recentFeePeriods(1);
      // console.log("Total rewards available: " + totalRewardsAvailable.toString());

      // Verify current period is empty as we have just opened it
      assertBNEqual(currentFeePeriod.rewardsToDistribute, 0);
      assertBNEqual(currentFeePeriod.feesToDistribute, 0);

      // Verify inital rewards can be distributed
      assertBNEqual(latestFeePeriod.rewardsToDistribute, totalRewardsAvailable);
      assertBNEqual(initial_rewards, totalRewardsAvailable);

      // Attempt to rollover into the next period
      await fastForward(feePeriodDuration.toNumber() + 10);
      let current_rewards = (await this.supplySchedule.mintableSupply()).sub(
        await this.supplySchedule.minterReward());

      // Mint and close period
      await this.synthetix.mint({from: this.owner});
      await this.feePool.closeCurrentFeePeriod({from: alice});

      // Verify reward distribution has been rolled forward
      totalRewardsAvailable = await this.feePool.totalRewardsAvailable()
      currentFeePeriod = await this.feePool.recentFeePeriods(0);
      latestFeePeriod = await this.feePool.recentFeePeriods(1);
      // console.log("Total rewards available: " + totalRewardsAvailable.toString());
      // console.log("Latest Fee Period Rewards to Distribute: " + latestFeePeriod.rewardsToDistribute.toString());

      // Verify current period is empty as we have just opened it
      assertBNEqual(currentFeePeriod.rewardsToDistribute, 0);
      assertBNEqual(currentFeePeriod.feesToDistribute, 0);

      // Verify current rewards have been added to distribution
      assertBNEqual(current_rewards.add(initial_rewards), totalRewardsAvailable);
      assertBNEqual(latestFeePeriod.rewardsToDistribute, totalRewardsAvailable);
    });


    it("Should allow rewards to rollover before mint", async function() {

      // Setup initial rewards
      const feePeriodDuration = await this.feePool.feePeriodDuration();
      await fastForward(feePeriodDuration.toNumber() + 10);
      const initial_rewards = (await this.supplySchedule.mintableSupply()).sub(
      await this.supplySchedule.minterReward());

      // console.log("Initial Rewards to Distribute (mintable supply - minting reward): " + initial_rewards.toString())

      // Mint initial supply, adding to current period rewards
      await this.synthetix.mint({from: this.owner});

      // Close period allowing initial rewards to be distributed
      await this.feePool.closeCurrentFeePeriod({from: alice});

      let totalRewardsAvailable = await this.feePool.totalRewardsAvailable()
      let currentFeePeriod = await this.feePool.recentFeePeriods(0);
      let latestFeePeriod = await this.feePool.recentFeePeriods(1);
      // console.log("Total rewards available: " + totalRewardsAvailable.toString());

      // Verify current period is empty as we have just opened it
      assertBNEqual(currentFeePeriod.rewardsToDistribute, 0);

      // Verify inital rewards can be distributed
      assertBNEqual(latestFeePeriod.rewardsToDistribute, totalRewardsAvailable);
      assertBNEqual(initial_rewards, totalRewardsAvailable);

      // Attempt to rollover into the next period
      await fastForward(feePeriodDuration.toNumber() + 10);
      let current_rewards = (await this.supplySchedule.mintableSupply()).sub(
        await this.supplySchedule.minterReward());

      // Close period therefore creating a rollover before minting
      await this.feePool.closeCurrentFeePeriod({from: alice});
      await this.synthetix.mint({from: this.owner});

      // Verify reward distribution has been rolled forward
      totalRewardsAvailable = await this.feePool.totalRewardsAvailable()
      currentFeePeriod = await this.feePool.recentFeePeriods(0);
      latestFeePeriod = await this.feePool.recentFeePeriods(1);
      // console.log("Total rewards available: " + totalRewardsAvailable.toString());
      // console.log("Latest Fee Period Rewards to Distribute: " + latestFeePeriod.rewardsToDistribute.toString());

      // Verify current period has just minted certain rewards
      assertBNEqual(currentFeePeriod.rewardsToDistribute, current_rewards);

      // Verify current rewards have NOT been added to distribution
      assertBNEqual(initial_rewards, totalRewardsAvailable);
      assertBNEqual(latestFeePeriod.rewardsToDistribute, initial_rewards);
    });

  });

});

const deployer = require("../deployer.js");
const BigNumber = require("bignumber.js");
const BN = require("bn.js");
const SupplySchedule = artifacts.require("./SupplySchedule.sol");
const SafeDecimalMath = artifacts.require("./SafeDecimalMath.sol");
const w3utils = require('web3-utils');



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

// Open some number of loans of value, as a single account, one after the other
// if logEveryX is nonZero, we log progress every X
const openNLoansSerial = async function(ethcol, n, fromAccount, value, logEveryX) {
  for (let i = 0; i < n; i++) {
    if (logEveryX > 0 && (i+1)%logEveryX == 0) {
      console.log(`Opened ${i+1} loans`)
    }
    await ethcol.openLoan({from: fromAccount, value: value});
  }
}

// Like openNLoansSerial, but tries to process them concurrently in chunks of XConcurrent
const openNLoansConcurrent = async function(ethcol, n, fromAccount, value, XConcurrent) {
  if (XConcurrent > 0) {
    let promises = [];
    for (let i = 0; i < n; i++) {
      promises.push(ethcol.openLoan({from: fromAccount, value: value}));
      if ((i+2) % XConcurrent == 0) {
        // +1 to convert from index to size, +1 to count the one we just pushed
        // wait for chunk
        await Promise.all(promises);
        console.log(`Opened ${i+2} loans`);
        promises = [];
      }
    }
    await Promise.all(promises)
  } else {
    // Try to do them all concurrently - this might fall over if the number of loans is too high for ganache
    let promises = [];
    for (let i = 0; i < n; i++) {
      /*if (logEveryX > 0 && (i+1)%logEveryX == 0) {
        console.log(`Opened ${i+1} loans`)
      }*/
      promises.push(ethcol.openLoan({from: fromAccount, value: value}));
    }
    await Promise.all(promises)
  }
}



contract("EtherCollateral", async function(accounts) {
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
    this.borrower = accounts[6];
    this.depositor = accounts[5];

    // Finish linking all contracts:

    timestamp = await getTimestamp()

    // update Rates
    await this.exchangeRates.updateRates([sETH, SNX], ['190', '1.20'].map(toUnit), timestamp, {
			from: this.oracle,
		});

    // update Rates
    await this.exchangeRates.updateRates([SNX, sETH, ETH], ['0.1', '172', '172'].map(toUnit), timestamp, {
			from: this.oracle,
		});

    // Update price stale period for depot
    // await this.depot.setPriceStalePeriod(YEAR, {
    //   from: this.owner,
    // });

    // NOTE: this assumes tests make no changes to the rig javascript objects/contract object properties
    // We can deepcopy and restore this between tests if that is a problem
  });
  beforeEach("snapshot", async function() {
    // This reduces the need to fully deploy each time (quicker),
    // but also reverts changes to evm timestamps between tests
    // Give the depot contract some SNX
    this.mainSnapShot = await helpers.takeSnapShot();
  });

  it("should be able to open multiple loans (up to the accountLoanLimit, this will take a long time)", async function() {
  // Just double checking these defaults here, as calculations depend on them
    assertBNEqual((await this.ethcol.collateralizationRatio()), toUnit("150"), "unexpected collateralizationRatio");
    assertBNEqual((await this.ethcol.issueLimit()), toUnit("5000"), "unexpected max cap");
    assertBNEqual((await this.ethcol.minLoanSize()), ONE_ETH, "unexpected minLoanSize");

    // TODO check if this rounds as expected
    let sETHPerMinLoan = ONE_ETH.mul(toUnit("100")).divRound(toUnit("150"));
    assertBNEqual((await this.ethcol.issuanceRatio()), sETHPerMinLoan, "unexpected issueRatio");
    // Number of minLoanSize loans possible within the issueLimit
    let maxAllowedLoansPerAccount = await this.ethcol.accountLoanLimit()

    console.log("Max Allowed Loans Per Account = " + maxAllowedLoansPerAccount)
    // console.log("Max allowed loans: ", maxAllowedLoans.toString(10));
    // This is 7499
    console.log("NOTE: this will take a while!");
    // TODO any way to async them more?
    await openNLoansConcurrent(this.ethcol, maxAllowedLoansPerAccount, this.borrower, ONE_ETH, 100);
    assertBNEqual(await this.ethcol.totalLoansCreated(), maxAllowedLoansPerAccount)
});

it("after max number of loans have been opened, it should allow closing them)", async function() {
  // Just double checking these defaults here, as calculations depend on them
  // Let's get the borrower to close the last loan

  await this.synthetix.issueSynths(toUnit('10000'), { from: this.owner });
  await this.sUSD.transfer(this.depositor, toUnit('1000'), {from: this.owner});
  assertBNEqual(await this.sUSD.balanceOf(this.depositor), toUnit('1000'));

  await this.sUSD.approve(this.depot.address, toUnit('1000'), {from: this.depositor });
  assertBNEqual(await this.sUSD.allowance(this.depositor, this.depot.address), toUnit('1000'))
  await this.depot.depositSynths(toUnit('1000'), {from: this.depositor});
  await this.ethcol.closeLoan(50, {from: this.borrower});

});


});

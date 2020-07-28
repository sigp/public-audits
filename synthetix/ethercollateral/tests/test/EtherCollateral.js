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
const ISSUANCE_RATIO = toUnit('0.8');

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

    // Finish linking all contracts:

    timestamp = await getTimestamp()

    // update Rates
    await this.exchangeRates.updateRates([SNX, sETH, ETH], ['0.1', '172', '172'].map(toUnit), timestamp, {
			from: this.oracle,
		});

    // Update rate stale period for exchangeRates
    await this.exchangeRates.setRateStalePeriod(YEAR, {
			from: this.owner,
		});

    // Update price stale period for
    // await this.depot.setPriceStalePeriod(YEAR, {
    //   from: this.owner,
    // });


    // Set the sUSD contract in the depot:
    // await this.depot.setSynth(this.sUSD.address, { from: this.owner });

    // Set Synthetix contract in the depot:
    // await this.depot.setSynthetix(this.synthetix.address, { from: this.owner });


    // NOTE: this assumes tests make no changes to the rig javascript objects/contract object properties
    // We can deepcopy and restore this between tests if that is a problem
  });
  beforeEach("snapshot", async function() {
    // This reduces the need to fully deploy each time (quicker),
    // but also reverts changes to evm timestamps between tests
    // Give the depot contract some SNX
    this.mainSnapShot = await helpers.takeSnapShot();
  });
  afterEach("restore snapshot", async function() {
    await helpers.revertTestRPC(this.mainSnapShot);
    this.mainSnapShot = undefined;
  });

  it("should deploy successfully with relevant contracts initialized", async function() {
    assert.strictEqual((await this.ethcol.owner()), this.owner);
  });

  context("after successful deployment, we expect default values", async function() {
    it("should have a minLoanSize of 1", async function() {
      assertBNEqual((await this.ethcol.minLoanSize()), ONE_ETH, "Incorrect minLoanSize");
    });


    it("should have no issued synths or loans", async function() {
      assertBNEqual((await this.ethcol.totalIssuedSynths()), toBN("0"));
      assertBNEqual((await this.ethcol.totalLoansCreated()), toBN("0"));
    });
    it("should not have an open loan Liquidation state", async function() {
      assertBNEqual((await this.ethcol.loanLiquidationOpen()), false);
    });

    it('should have a collateralizationRatio of 125%', async function() {
     const defaultRatio = toUnit(125);
     const actualRatio = await this.ethcol.collateralizationRatio();
     assertBNEqual(actualRatio, defaultRatio);
    });

    it('should have an issuanceRatio of 80%', async function() {
     assertBNEqual(await this.ethcol.issuanceRatio(), ISSUANCE_RATIO);
    });

    it('should have an issueFeeRate of 50 bips', async function() {
     const mintingFee = toUnit('0.005');
     assertBNEqual(await this.ethcol.issueFeeRate(), mintingFee);
    });

    it('should have an interestRate of 5%', async function() {
     const interestRate = toUnit('0.05');
     assertBNEqual(await this.ethcol.interestRate(), interestRate);
    });

    it('should have an issueLimit of 5000', async function() {
     const limit = toUnit('5000');
     assertBNEqual(await this.ethcol.issueLimit(), limit);
    });

    it('should have a minLoanSize of 1', async function() {
     assertBNEqual(await this.ethcol.minLoanSize(), ONE_ETH);
    });

    it('should not be in a loanLiquidatio period', async function() {
     assert.equal(await this.ethcol.loanLiquidationOpen(), false);
    });

    it('should have a liquidationDeadline is set after 92 days', async function() {
     const now = await getTimestamp();
     // allow variance in reported liquidationDeadline to account for block time slippage
     assert((await this.ethcol.liquidationDeadline()).gt(Number(now) + 92 * DAY))
    });
  });

  context("after successful deployment, the owner", async function() {

    it("should be able to set a valid collateralisation ratio", async function() {
      await this.ethcol.setCollateralizationRatio(toUnit("200"), {from: this.owner});
      assertBNEqual((await this.ethcol.collateralizationRatio()), toUnit("200"), "property should be changed");
    });

    it("should not be able to set up an invalid collateralisation ratio", async function() {
      await assertRevert(this.ethcol.setCollateralizationRatio(toUnit("1500"), {from: this.owner}));
      assertBNEqual((await this.ethcol.collateralizationRatio()), toUnit("125"), "property should be unchanged");
    });

    it("should be able to change the interest rate", async function() {
      await this.ethcol.setInterestRate(toUnit("0.1"), {from: this.owner});
      assertBNEqual((await this.ethcol.interestRate()), toUnit("0.1"), "property should be changed");
    });

    it("should be able to change the minting fee (issueFeeRate)", async function() {
      await this.ethcol.setIssueFeeRate(toUnit("0.1"), {from: this.owner});
      assertBNEqual((await this.ethcol.issueFeeRate()), toUnit("0.1"), "property should be changed");
    });

    it("should be able to set minLoanSize", async function() {
      let recpt = await this.ethcol.setMinLoanSize(TWO_ETH, {from: this.owner});
      assertBNEqual((await this.ethcol.minLoanSize()), toUnit("2"), "property should be changed");
    });

    it("should be able to set issueLimit", async function() {
      let recpt = await this.ethcol.setIssueLimit(toUnit("10000"), {from: this.owner});
      assertBNEqual((await this.ethcol.issueLimit()), toUnit("10000"), "property should be changed");
    });

    it("should not be able to immediately open loan liquidation", async function() {
      await assertRevert(this.ethcol.setLoanLiquidationOpen(true, {from: this.owner}));
      assertBNEqual((await this.ethcol.loanLiquidationOpen()), false, "property should be unchanged");
    });
  });

  context("after successful deployment, a non-owner", async function() {
    before("identify non-owner", async function() {
      let someoneElse = accounts[6];
      assert.notEqual(someoneElse, this.owner, "Unexpected precondition: should not be the owner!");
      assert.notEqual((await this.ethcol.owner()), someoneElse, "Unexpected precondition: should not be owner!");
      this.someoneElse = someoneElse;
    });

    it("should not be able to set a valid collateralisation ratio", async function() {
      await assertRevert(this.ethcol.setCollateralizationRatio(toUnit("200"), {from: this.someoneElse}));
      assertBNEqual((await this.ethcol.collateralizationRatio()), toUnit("125"), "property should be unchanged");
    });

    it("should not not be able to set up an invalid collateralisation ratio", async function() {
      await assertRevert(this.ethcol.setCollateralizationRatio(toUnit("1500"), {from: this.someoneElse}));
      assertBNEqual((await this.ethcol.collateralizationRatio()), toUnit("125"), "property should be unchanged");
    });

    it("should not be able to change the interest rate", async function() {
      await assertRevert(this.ethcol.setInterestRate(toUnit("0.1"), {from: this.someoneElse}));
      assertBNEqual((await this.ethcol.interestRate()), toUnit("0.05"), "property should be unchanged");
    });

    it("should not be able to change the minting fee (issueFeeRate)", async function() {
      await assertRevert(this.ethcol.setIssueFeeRate(toUnit("0.1"), {from: this.someoneElse}));
      assertBNEqual((await this.ethcol.issueFeeRate()), toBN("5000000000000000"), "property should be unchanged");
    });

    it("should not not be able to set minLoanSize", async function() {
      await assertRevert(this.ethcol.setMinLoanSize(TWO_ETH, {from: this.someoneElse}));
      assertBNEqual((await this.ethcol.minLoanSize()), ONE_ETH, "minLoanSize should be ununchanged.");
    });

    it("should not be able to set issueLimit", async function() {
      await assertRevert(this.ethcol.setIssueLimit(toUnit("10000"), {from: this.someoneElse}));
      assertBNEqual((await this.ethcol.issueLimit()), toUnit("5000"), "property should be unchanged");
    });

    it("should not be able to open loan liquidation", async function() {
      await assertRevert(this.ethcol.setLoanLiquidationOpen(true, {from: this.someoneElse}));
      assertBNEqual((await this.ethcol.loanLiquidationOpen()), false, "property should be unchanged");
    });

    context("with enough ETH", async function() {
      before("check expected preconditions", async function() {
        let borrower = this.someoneElse;
        let preBalance = toBN(await web3.eth.getBalance(borrower));
        assert(preBalance.gt(toUnit("10000")), "Insufficient balance: check that you're starting ganache with a high enough defaultBalanceEther e.g. 'ganache-cli-script.sh'")
        this.borrower = borrower;
        this.depositor = accounts[5];
        this.alice = accounts[3];
        this.bob = accounts[4];
        this.carol = accounts[5];
      });

      it("should be able to open a loan with a value > minLoanSize", async function() {
        let preBalance = toBN(await web3.eth.getBalance(this.borrower));
        let recpt = await this.ethcol.openLoan({from: this.borrower, value: TWO_ETH});
        sETHBalance = await this.sETH.balanceOf(this.borrower);
        let postBalance = toBN(await web3.eth.getBalance(this.borrower));
        assert(sETHBalance.gt(0), "Should now own some sETH");
        assert(postBalance.lt(preBalance), "Eth balance should be reduced.")
      });

      it("should be able to open a loan with a value == minLoanSize", async function() {
        await this.ethcol.openLoan({from: this.borrower, value: ONE_ETH});
      });

      it("should not be able to open a loan with a value < minLoanSize", async function() {
        await assertRevert(this.ethcol.openLoan({from: this.borrower, value: toUnit("0.5")}));
      });

      it("should be able to open a loan to the maximum cap", async function() {
        assertBNEqual((await this.ethcol.issueLimit()), toUnit("5000"), "unexpected max cap");
        await this.ethcol.openLoan({from: this.borrower, value: toUnit("5000")});
        // TODO check via openLoans by account
      });

      it("should not be able to open a loan that exceeds the maximum cap", async function() {
        // This succeeds given the current bug in openLoan()
        assert(await this.sETH.balanceOf(this.borrower) == 0)
        await assertRevert(this.ethcol.openLoan({from: this.borrower, value: toUnit("10000")}));
        expectedBalance = toUnit('0')
        assertBNEqual(await this.sETH.balanceOf(this.borrower), expectedBalance, "unexpected loan amount");
      });

      it("should be able to open multiple loans (within the issueLimit)", async function() {
        await openNLoansConcurrent(this.ethcol, 10, this.borrower, ONE_ETH);
      });

      it("should allow borrower to close a loan", async function() {
        await (this.ethcol.openLoan({from: this.borrower, value: toUnit("100")}));
        // make sure the owner has SNX:
        assertBNEqual(await this.synthetix.balanceOf(this.owner), toUnit('50000000'));

        await helpers.increaseTime(days(20))

        await this.synthetix.issueSynths(toUnit('10000'), { from: this.owner });
        await this.sUSD.transfer(this.depositor, toUnit('1000'), {from: this.owner});
        assertBNEqual(await this.sUSD.balanceOf(this.depositor), toUnit('1000'));

        await this.sUSD.approve(this.depot.address, toUnit('1000'), {from: this.depositor });
        assertBNEqual(await this.sUSD.allowance(this.depositor, this.depot.address), toUnit('1000'))

        await this.depot.depositSynths(toUnit('1000'), {from: this.depositor});
        await this.ethcol.closeLoan(1, {from: this.borrower});
        assert(await this.sETH.balanceOf(this.borrower) == 0);

      });

      it("should prevent anyone from opening a loan when the liquidation period is on", async function() {

        await helpers.increaseTime(days(95))
        assertRevert(await this.ethcol.openLoan({from: this.borrower, value: ONE_ETH}));
      });

      it("should prevent anyone from closing a loan that's not theirs", async function() {

        await (this.ethcol.openLoan({from: this.borrower, value: toUnit("100")}));
        await (this.ethcol.openLoan({from: this.alice, value: toUnit("100")}));

        await helpers.increaseTime(days(20))

        await this.synthetix.issueSynths(toUnit('10000'), { from: this.owner });
        await this.sUSD.transfer(this.depositor, toUnit('1000'), {from: this.owner});
        await this.sUSD.transfer(this.alice, toUnit('1000'), {from: this.owner});

        assertBNEqual(await this.sUSD.balanceOf(this.depositor), toUnit('1000'));
        assertBNEqual(await this.sUSD.balanceOf(this.alice), toUnit('1000'));

        await this.sUSD.approve(this.depot.address, toUnit('1000'), {from: this.depositor });
        await this.sUSD.approve(this.depot.address, toUnit('1000'), {from: this.alice });

        assertBNEqual(await this.sUSD.allowance(this.depositor, this.depot.address), toUnit('1000'))
        assertBNEqual(await this.sUSD.allowance(this.alice, this.depot.address), toUnit('1000'))

        await this.depot.depositSynths(toUnit('1000'), {from: this.depositor});
        await assertRevert(this.ethcol.closeLoan(2, {from: this.borrower}));
        await assertRevert(this.ethcol.closeLoan(1, {from: this.alice}));

        assert(await this.sETH.balanceOf(this.borrower) > 0);
        assert(await this.sETH.balanceOf(this.alice) > 0);

      });

      it("should prevent anyone from closing a loan when their balance in sETH is insufficient", async function() {

        await (this.ethcol.openLoan({from: this.borrower, value: toUnit("100")}));
        // make sure the owner has SNX:
        assertBNEqual(await this.synthetix.balanceOf(this.owner), toUnit('50000000'));

        await helpers.increaseTime(days(20))

        await this.synthetix.issueSynths(toUnit('10000'), { from: this.owner });
        await this.sUSD.transfer(this.depositor, toUnit('1000'), {from: this.owner});
        assertBNEqual(await this.sUSD.balanceOf(this.depositor), toUnit('1000'));

        await this.sUSD.approve(this.depot.address, toUnit('1000'), {from: this.depositor });
        assertBNEqual(await this.sUSD.allowance(this.depositor, this.depot.address), toUnit('1000'))

        await this.depot.depositSynths(toUnit('1000'), {from: this.depositor});
        // Make the depositor spend some of their sETH
        await this.sETH.transfer(this.owner, toUnit('10'), {from: this.borrower});

        await assertRevert(this.ethcol.closeLoan(1, {from: this.borrower}));

        assert(await this.sETH.balanceOf(this.borrower) != 0);

      });

      it("should return valid loan details", async function() {

        await (this.ethcol.openLoan({from: this.borrower, value: toUnit("100")}));

        const loan = await this.ethcol.getLoan(this.borrower, 1)
        assert(loan[0] == this.borrower);
        assertBNEqual(loan[1], toUnit("100"));
        assertBNEqual(loan[2], await this.sETH.balanceOf(this.borrower));
        assert(loan[4] == 1);

      });

      it("should compute collateral from loan correctly", async function() {

        const collateral = await this.ethcol.collateralAmountForLoan(toUnit("500"))
        assertBNEqual(collateral, toUnit("625"))

      });

      context("after minLoanSize is increased", async function() {
        before("set minLoanSize to 2 ETH", async function() {
          await this.ethcol.setMinLoanSize(TWO_ETH, {from: this.owner});
        });

        it("should not be able to open a loan with a value < the new minLoanSize", async function() {
          await assertRevert(this.ethcol.openLoan({from: this.borrower, value: ONE_ETH}));
        });

        it("should be able to open a loan with a value == the new minLoanSize", async function() {
          await this.ethcol.openLoan({from: this.borrower, value: TWO_ETH});
        });
      });

      context("when the liquidation period is triggered", async function() {
        before("set minLoanSize to 2 ETH", async function() {
          await this.ethcol.setMinLoanSize(TWO_ETH, {from: this.owner});



        });

        before("get Alice and Bob to open loans", async function() {
          // Ensure the depot is setup properly
          await this.synthetix.issueSynths(toUnit('10000'), { from: this.owner });
          await this.sUSD.transfer(this.depositor, toUnit('1000'), {from: this.owner});
          assertBNEqual(await this.sUSD.balanceOf(this.depositor), toUnit('1000'));
          await this.sUSD.approve(this.depot.address, toUnit('1000'), {from: this.depositor });
          assertBNEqual(await this.sUSD.allowance(this.depositor, this.depot.address), toUnit('1000'))
          await this.depot.depositSynths(toUnit('1000'), {from: this.depositor});


          await (this.ethcol.openLoan({from: this.alice, value: toUnit("100")}));
          await (this.ethcol.openLoan({from: this.bob, value: toUnit("100")}));

          // verify that Alice opened a loan:
          const loanA = await this.ethcol.getLoan(this.alice, 1)
          assertBNEqual(loanA[1], toUnit("100"));
          assertBNEqual(loanA[2], await this.sETH.balanceOf(this.alice));

          // Verify that Bob opened a loan:
          const loanB = await this.ethcol.getLoan(this.bob, 2)
          assertBNEqual(loanB[1], toUnit("100"));
          assertBNEqual(loanB[2], await this.sETH.balanceOf(this.bob));

          // The owner issues sUSD and transfers some to the depot
          await this.synthetix.issueSynths(toUnit('10000'), { from: this.owner });
          await this.sUSD.transfer(this.depot.address, toUnit('1000'), {from: this.owner});


        });

        it("should make sure that the loans were opened correctly", async function() {
          // Alice
          const loanA = await this.ethcol.getLoan(this.alice, 1)
          assertBNEqual(loanA[1], toUnit("100"));
          assertBNEqual(loanA[2], await this.sETH.balanceOf(this.alice));

          // Bob
          const loanB = await this.ethcol.getLoan(this.bob, 2)
          assertBNEqual(loanB[1], toUnit("100"));
          assertBNEqual(loanB[2], await this.sETH.balanceOf(this.bob));

        });

        it("it should make sure that anyone with enough sETH can close a loan", async function() {
          // advance time to 93 days
          await helpers.increaseTime(days(93));

          // open the liquidation period
          await this.ethcol.setLoanLiquidationOpen(true, {from: this.owner});

          // Make sure that the liquidation period is open
          assertBNEqual((await this.ethcol.loanLiquidationOpen()), true, "property should be changed");
          // Record Bob's ETH balance before loan closure:
          balanceA = await web3.eth.getBalance(this.bob);

          // Get Bob to close Alice's loan
          await this.ethcol.liquidateUnclosedLoan(this.alice, 1, {from: this.bob});

          // Record Bob's ETH balance after loan closure:
          balanceB = await web3.eth.getBalance(this.bob);

          // Ensure that bob's sETH balance is 0
          assert(await this.sETH.balanceOf(this.bob) == 0);

          // Ensure Bob's ETH balance increased
          assert(balanceB > balanceA);

        });

        it.only("it shouldn't allow for a loan to be closed twice", async function() {
          // advance time to 93 days
          await helpers.increaseTime(days(93));

          // open the liquidation period
          await this.ethcol.setLoanLiquidationOpen(true, {from: this.owner});

          // Make sure that the liquidation period is open
          assertBNEqual((await this.ethcol.loanLiquidationOpen()), true, "property should be changed");

          // Get Bob to close Alice's loan
          await this.ethcol.liquidateUnclosedLoan(this.alice, 1, {from: this.bob});

          // Make sure carol can't close the same loan
          await assertRevert(this.ethcol.liquidateUnclosedLoan(this.alice, 1, {from: this.carol}));

        });

        it.only("it should make sure the liquidated account still keeps their sETH", async function() {
          // advance time to 93 days
          await helpers.increaseTime(days(93));

          // open the liquidation period
          await this.ethcol.setLoanLiquidationOpen(true, {from: this.owner});

          // Make sure that the liquidation period is open
          assertBNEqual((await this.ethcol.loanLiquidationOpen()), true, "property should be changed");

          // Record Alice's sETH balance before loan closure
          balanceA = await this.sETH.balanceOf(this.alice);

          // Get Bob to close Alice's loan
          await this.ethcol.liquidateUnclosedLoan(this.alice, 1, {from: this.bob});

          // Record Alice's sETH after loan closure
          balanceB = await this.sETH.balanceOf(this.alice);

          // Assert Alice's sETH balance is unchanged
          assertBNEqual(balanceA, balanceB);
        });

        it.only("it should make sure the loan count decreases when a loan is liquidated", async function() {
          // Record loan count
          loanCountA = await this.ethcol.totalOpenLoanCount();

          // advance time to 93 days
          await helpers.increaseTime(days(93));

          // open the liquidation period
          await this.ethcol.setLoanLiquidationOpen(true, {from: this.owner});

          // Make sure that the liquidation period is open
          assertBNEqual((await this.ethcol.loanLiquidationOpen()), true, "property should be changed");

          // Record Alice's sETH balance before loan closure
          balanceA = await this.sETH.balanceOf(this.alice);

          // Get Bob to close Alice's loan
          await this.ethcol.liquidateUnclosedLoan(this.alice, 1, {from: this.bob});

          // Record loan count after liquidation
          loanCountB = await this.ethcol.totalOpenLoanCount();

          // Assert the loan count has decreased
          assertBNEqual(loanCountB, loanCountA - 1);

        });

    });

  });

});

});

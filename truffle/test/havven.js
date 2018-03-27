const deployer = require('../deployer.js')
const BigNumber = require("bignumber.js")

const Court = artifacts.require('./Court.sol')
const Havven = artifacts.require('./Havven.sol')
const EtherNomin = artifacts.require('./EtherNomin.sol')
const HavvenEscrow = artifacts.require('./HavvenEscrow.sol')

const helpers = require('../testHelpers.js')
const assertRevert = helpers.assertRevert


/*
 * Multiply a number by the value of UNIT in the
 * smart contract's safe math.
 */
const toUnit = (x) => new BigNumber(x).times(Math.pow(10, 18))
assert(toUnit(3).toString() === "3000000000000000000", 'toUnit() is wrong')

/*
 * Return the amount of seconds in x days
 */
const days = (x) => x * 60 * 60 * 24
assert(days(2) === 172800, 'days() is wrong')

/*
 * Return the timestamp of the current block
 */
const timestamp = () => new BigNumber(web3.eth.getBlock(web3.eth.blockNumber).timestamp)

/*
 * Calculate the total fee value for a value and a given basis point
 * fee.
 */
const bpFee = (n, bp) => new BigNumber(n).times(new BigNumber(bp).dividedBy(10000))
assert(bpFee(10000, 50).toString() === "50", 'bpFee() is wrong')

/*
 * Determine that a is within a percentage of b
 */
const withinMarginOfError = (a, b) => helpers.withinPercentageOf(a, b, 0.0001)
assert(withinMarginOfError(10.00000999999, 10) === true, 'withinMarginOfError() broken')
assert(withinMarginOfError(10.0000100001, 10) === false, 'withinMarginOfError() broken')
const assertWithinMargin = (a, b, msg) => assert(withinMarginOfError(a, b), msg)
assertWithinMargin(10.00000999999, 10, 'assertWithinMargin() broken')

/*
 * Push a havven contract into its next fee period
 * `h` should be a havven contract instance
 */
const jumpToNextFeePeriod = async function(h) {
		const feePeriodStartTime = await h.feePeriodStartTime.call()
		const targetFeePeriodDuration = await h.targetFeePeriodDurationSeconds.call()
		helpers.setDate(feePeriodStartTime.plus(targetFeePeriodDuration))
		await h.rolloverFeePeriod()
		assert(feePeriodStartTime.lessThan(await h.feePeriodStartTime.call()), 'fee period did not change')
}


/*
 * It is assumed that all integers are to be multipled by the
 * UNIT constant, which is 10**18.
 */
contract('Havven scenarios', function(accounts) {


	it('should distribute fees evenly if there are only two equal havven holders', async function() {
		const rig = await deployer.setupTestRig(accounts)

		const owner = rig.accounts.owner
		const n = rig.nomin
		const h = rig.havven
		const holderA = accounts[4]
		const holderB = accounts[5]

		const etherPrice = await n.etherPrice.call()
		const nominIssuance = toUnit(10)
		const collateral = web3.toWei(nominIssuance.dividedBy(etherPrice).times(2), 'ether')
		
		// issue nomins and then have accounts[0] purchase them
		await n.issue(nominIssuance, {from: owner, value: collateral})
		const purchaseCost = await n.purchaseCostEther(nominIssuance)
		await n.buy(nominIssuance, {value: purchaseCost})
		assert(nominIssuance.equals(await n.balanceOf(accounts[0])), 'accounts[0] should have all the nomins')

		// do a bunch of transactions between accounts[0] and accounts[6]
		const rounds = 10
		const nominsSent = toUnit(1)
		const nominsReturned = toUnit(0.5)
		for(var i = 0; i < rounds; i++){
			await n.transfer(accounts[6], nominsSent, { from: accounts[0] })
			await n.transfer(accounts[0], nominsReturned, { from: accounts[6] })
		}

		// figure out how many fees should have been obtained from those transactions
		const transferVolume = nominsSent.plus(nominsReturned).times(rounds)
		const fees = bpFee(transferVolume, 20)
		// assert our expectation is reality
		assert(fees.equals(await n.feePool.call()), `feePool was not as expected`)

		// assign the havvens equally
		const hundredMillion = toUnit(Math.pow(10, 8))
		const havvens = hundredMillion.dividedBy(2)
		await h.endow(holderA, havvens, { from: owner })
		await h.endow(holderB, havvens, { from: owner })
		assert(havvens.equals(await h.balanceOf(holderA)), `holderA havven allocation is incorrect`)
		assert(havvens.equals(await h.balanceOf(holderB)), `holderB havven allocation is incorrect`)

		// push havven into the next fee period
		await jumpToNextFeePeriod(h)

		// check the fees can be withdrawn
		assert(toUnit(0).equals(await n.balanceOf(holderA)), 'holderA should not have nomins yet')
		assert(toUnit(0).equals(await n.balanceOf(holderB)), 'holderB should not have nomins yet')
		await h.withdrawFeeEntitlement({ from: holderA })
		await h.withdrawFeeEntitlement({ from: holderB })

		// assert the fees are as expected
		const halfOfFees = fees.dividedBy(2)
		assertWithinMargin(await n.balanceOf(holderA), halfOfFees, 'holderA should have half the fees collected')
		assertWithinMargin(await n.balanceOf(holderB), halfOfFees, 'holderB should have half the fees collected')
	})
	
	
	it('should not allow double fee withdrawal', async function() {
		const rig = await deployer.setupTestRig(accounts)

		const owner = rig.accounts.owner
		const n = rig.nomin
		const h = rig.havven
		const holder = accounts[4]

		const etherPrice = await n.etherPrice.call()
		const nominIssuance = toUnit(2)
		const collateral = web3.toWei(nominIssuance.dividedBy(etherPrice).times(2), 'ether')
		
		// issue nomins and then have accounts[0] purchase them
		await n.issue(nominIssuance, {from: owner, value: collateral})
		const purchaseCost = await n.purchaseCostEther(nominIssuance)
		await n.buy(nominIssuance, {value: purchaseCost})
		assert(nominIssuance.equals(await n.balanceOf(accounts[0])), 'accounts[0] should have all the nomins')

		// do a transaction between accounts[0] and accounts[6]
		const rounds = 1
		const nominsSent = toUnit(1)
		const nominsReturned = toUnit(0.5)
		for(var i = 0; i < rounds; i++){
			await n.transfer(accounts[6], nominsSent, { from: accounts[0] })
			await n.transfer(accounts[0], nominsReturned, { from: accounts[6] })
		}

		// figure out how many fees should have been obtained from those transactions
		const transferVolume = nominsSent.plus(nominsReturned).times(rounds)
		const fees = bpFee(transferVolume, 20)
		// assert our expectation is reality
		assert(fees.equals(await n.feePool.call()), `feePool was not as expected`)

		// assign the havvens equally
		const hundredMillion = toUnit(Math.pow(10, 8))
		await h.endow(holder, hundredMillion, { from: owner })
		assert(hundredMillion.equals(await h.balanceOf(holder)), `holder havven allocation is incorrect`)

		// push havven into the next fee period
		await jumpToNextFeePeriod(h)

		// check the fees can be withdrawn
		assert(toUnit(0).equals(await n.balanceOf(holder)), 'holder should not have nomins yet')
		await h.withdrawFeeEntitlement({ from: holder })
		assertWithinMargin(await n.balanceOf(holder),fees, 'holderA should have half the fees collected')
		await assertRevert(h.withdrawFeeEntitlement({ from: holder }))
	})
	
	
	it('should roll over uncollected fees into the next fee period', async function() {
		const rig = await deployer.setupTestRig(accounts)

		const owner = rig.accounts.owner
		const n = rig.nomin
		const h = rig.havven
		const holderA = accounts[4]
		const holderB = accounts[5]

		const etherPrice = await n.etherPrice.call()
		const nominIssuance = toUnit(8.828)
		const collateral = web3.toWei(nominIssuance.dividedBy(etherPrice).times(2), 'ether')
		
		// issue nomins and then have accounts[0] purchase them
		await n.issue(nominIssuance, {from: owner, value: collateral})
		const purchaseCost = await n.purchaseCostEther(nominIssuance)
		await n.buy(nominIssuance, {value: purchaseCost})
		assert(nominIssuance.equals(await n.balanceOf(accounts[0])), 'accounts[0] should have all the nomins')

		// do a bunch of transactions between accounts[0] and accounts[6]
		const rounds = 10
		const nominsSent = toUnit(0.883428)
		const nominsReturned = toUnit(0.594928)
		for(var i = 0; i < rounds; i++){
			await n.transfer(accounts[6], nominsSent, { from: accounts[0] })
			await n.transfer(accounts[0], nominsReturned, { from: accounts[6] })
		}

		// figure out how many fees should have been obtained from those transactions
		const transferVolume = nominsSent.plus(nominsReturned).times(rounds)
		const fees = bpFee(transferVolume, 20)
		const halfOfFees = fees.dividedBy(2)
		const quarterOfFees = fees.dividedBy(4)
		const threeQuartersOfFees = fees.times(0.75)
		// assert our expectation is reality
		assert(fees.equals(await n.feePool.call()), `feePool was not as expected`)

		// assign the havvens equally
		const hundredMillion = toUnit(Math.pow(10, 8))
		const havvens = hundredMillion.dividedBy(2)
		await h.endow(holderA, havvens, { from: owner })
		await h.endow(holderB, havvens, { from: owner })
		assert(havvens.equals(await h.balanceOf(holderA)), `holderA havven allocation is incorrect`)
		assert(havvens.equals(await h.balanceOf(holderB)), `holderB havven allocation is incorrect`)

		// push havven into the next fee period
		await jumpToNextFeePeriod(h)

		// only holderA is going to withdraw
		assert(toUnit(0).equals(await n.balanceOf(holderA)), 'holderA should not have nomins yet')
		await h.withdrawFeeEntitlement({ from: holderA })
		assertWithinMargin(await n.balanceOf(holderA), halfOfFees, 'holderA should have half the fees collected')

		// push havven into another fee period
		feePeriodStartTime = await h.feePeriodStartTime.call()
		targetFeePeriodDuration = await h.targetFeePeriodDurationSeconds.call()
		helpers.setDate(feePeriodStartTime.plus(targetFeePeriodDuration))
		await h.rolloverFeePeriod()
		assert(feePeriodStartTime.lessThan(await h.feePeriodStartTime.call()), 'fee period did not change')

		// check that the fees are distributed as expected
		await h.withdrawFeeEntitlement({ from: holderA })
		await h.withdrawFeeEntitlement({ from: holderB })
		assertWithinMargin(await n.balanceOf(holderA), threeQuartersOfFees, 'holderA should have 3/4 the fees collected')
		assertWithinMargin(await n.balanceOf(holderB), quarterOfFees, 'holderB should have 1/4 the fees collected')
	})

	
	it('should not give any fees to someone who dumped all havvens in the penultimate fee period', async function() {
		const rig = await deployer.setupTestRig(accounts)

		const owner = rig.accounts.owner
		const n = rig.nomin
		const h = rig.havven
		const holderA = accounts[4]
		const holderB = accounts[5]

		const etherPrice = await n.etherPrice.call()
		const nominIssuance = toUnit(8.828)
		const collateral = web3.toWei(nominIssuance.dividedBy(etherPrice).times(2), 'ether')
		
		// issue nomins and then have accounts[0] purchase them
		await n.issue(nominIssuance, {from: owner, value: collateral})
		const purchaseCost = await n.purchaseCostEther(nominIssuance)
		await n.buy(nominIssuance, {value: purchaseCost})
		assert(nominIssuance.equals(await n.balanceOf(accounts[0])), 'accounts[0] should have all the nomins')

		// do a bunch of transactions between accounts[0] and accounts[6]
		const rounds = 10
		const nominsSent = toUnit(0.883428)
		const nominsReturned = toUnit(0.594928)
		for(var i = 0; i < rounds; i++){
			await n.transfer(accounts[6], nominsSent, { from: accounts[0] })
			await n.transfer(accounts[0], nominsReturned, { from: accounts[6] })
		}

		// figure out how many fees should have been obtained from those transactions
		const transferVolume = nominsSent.plus(nominsReturned).times(rounds)
		const fees = bpFee(transferVolume, 20)
		const halfOfFees = fees.dividedBy(2)
		const quarterOfFees = fees.dividedBy(4)
		const threeQuartersOfFees = fees.times(0.75)
		// assert our expectation is reality
		assert(fees.equals(await n.feePool.call()), `feePool was not as expected`)

		// assign the havvens equally
		const hundredMillion = toUnit(Math.pow(10, 8))
		const havvens = hundredMillion.dividedBy(2)
		await h.endow(holderA, havvens, { from: owner })
		await h.endow(holderB, havvens, { from: owner })
		assert(havvens.equals(await h.balanceOf(holderA)), `holderA havven allocation is incorrect`)
		assert(havvens.equals(await h.balanceOf(holderB)), `holderB havven allocation is incorrect`)

		// push havven into the next fee period
		await jumpToNextFeePeriod(h)

		// only holderA is going to withdraw
		assert(toUnit(0).equals(await n.balanceOf(holderA)), 'holderA should not have nomins yet')
		await h.withdrawFeeEntitlement({ from: holderA })
		assertWithinMargin(await n.balanceOf(holderA), halfOfFees, 'holderA should have half the fees collected')
		
		// holderB will burn all havvens (bold move, holderB)
		const nowhere = "0x1337"
		await h.transfer(nowhere, havvens, { from: holderB })
		assert(havvens.equals(await h.balanceOf(nowhere)), 'tokens were not burnt')

		// push havven forward two fee periods (so holderB had no tokens in the 'last' fee period)
		await jumpToNextFeePeriod(h)
		await jumpToNextFeePeriod(h)
		
		// holderB should not be entitled to any fees
		await h.withdrawFeeEntitlement({ from: holderB })
		assert(toUnit(0).equals(await n.balanceOf(holderB)), 'holderB should not have any nomins')
	})
	
	
	it('should store an accurate penultimate avg. balance', async function() {
		const rig = await deployer.setupTestRig(accounts)

		const owner = rig.accounts.owner
		const n = rig.nomin
		const h = rig.havven
		const holderA = accounts[4]
		const holderB = accounts[5]

		const etherPrice = await n.etherPrice.call()
		const nominIssuance = toUnit(8.828)
		const collateral = web3.toWei(nominIssuance.dividedBy(etherPrice).times(2), 'ether')
		
		// issue nomins and then have accounts[0] purchase them
		await n.issue(nominIssuance, {from: owner, value: collateral})
		const purchaseCost = await n.purchaseCostEther(nominIssuance)
		await n.buy(nominIssuance, {value: purchaseCost})
		assert(nominIssuance.equals(await n.balanceOf(accounts[0])), 'accounts[0] should have all the nomins')

		// do a bunch of transactions between accounts[0] and accounts[6]
		const rounds = 10
		const nominsSent = toUnit(0.883428)
		const nominsReturned = toUnit(0.594928)
		for(var i = 0; i < rounds; i++){
			await n.transfer(accounts[6], nominsSent, { from: accounts[0] })
			await n.transfer(accounts[0], nominsReturned, { from: accounts[6] })
		}

		// figure out how many fees should have been obtained from those transactions
		const transferVolume = nominsSent.plus(nominsReturned).times(rounds)
		const fees = bpFee(transferVolume, 20)
		const halfOfFees = fees.dividedBy(2)
		// assert our expectation is reality
		assert(fees.equals(await n.feePool.call()), `feePool was not as expected`)

		// assign the havvens equally
		const hundredMillion = toUnit(Math.pow(10, 8))
		const havvens = hundredMillion.dividedBy(2)
		await h.endow(holderA, havvens, { from: owner })
		await h.endow(holderB, havvens, { from: owner })
		assert(havvens.equals(await h.balanceOf(holderA)), `holderA havven allocation is incorrect`)
		assert(havvens.equals(await h.balanceOf(holderB)), `holderB havven allocation is incorrect`)

		// push havven forward three fee periods (three to ensure the balance spanned the entire period)
		await jumpToNextFeePeriod(h)
		await jumpToNextFeePeriod(h)
		await jumpToNextFeePeriod(h)

		// force average balance computation
		await h.recomputeLastAverageBalance({ from: holderA })
		await h.recomputeLastAverageBalance({ from: holderB })

		// check that the penultimate average balance is correct for both hodlers
		assertWithinMargin(
			await h.penultimateAverageBalance(holderA), 
			havvens, 
			'holderA should have half the fees collected'
		)
		assertWithinMargin(
			await h.penultimateAverageBalance(holderB), 
			havvens, 
			'holderB should have half the fees collected'
		)
	})
	
	
	it('should show an average balance of half if tokens are moved halfway though the fee period', async function() {
		const rig = await deployer.setupTestRig(accounts)

		const owner = rig.accounts.owner
		const n = rig.nomin
		const h = rig.havven
		const holderA = accounts[4]
		const holderB = accounts[5]

		const etherPrice = await n.etherPrice.call()
		const nominIssuance = toUnit(8.828)
		const collateral = web3.toWei(nominIssuance.dividedBy(etherPrice).times(2), 'ether')
		
		// issue nomins and then have accounts[0] purchase them
		await n.issue(nominIssuance, {from: owner, value: collateral})
		const purchaseCost = await n.purchaseCostEther(nominIssuance)
		await n.buy(nominIssuance, {value: purchaseCost})
		assert(nominIssuance.equals(await n.balanceOf(accounts[0])), 'accounts[0] should have all the nomins')

		// do a bunch of transactions between accounts[0] and accounts[6]
		const rounds = 10
		const nominsSent = toUnit(0.883428)
		const nominsReturned = toUnit(0.594928)
		for(var i = 0; i < rounds; i++){
			await n.transfer(accounts[6], nominsSent, { from: accounts[0] })
			await n.transfer(accounts[0], nominsReturned, { from: accounts[6] })
		}

		// figure out how many fees should have been obtained from those transactions
		const transferVolume = nominsSent.plus(nominsReturned).times(rounds)
		const fees = bpFee(transferVolume, 20)
		const quarterOfFees = fees.dividedBy(4)
		// assert our expectation is reality
		assert(fees.equals(await n.feePool.call()), `feePool was not as expected`)

		// assign the havvens equally
		const hundredMillion = toUnit(Math.pow(10, 8))
		const havvens = hundredMillion.dividedBy(2)
		await h.endow(holderA, havvens, { from: owner })
		await h.endow(holderB, havvens, { from: owner })
		assert(havvens.equals(await h.balanceOf(holderA)), `holderA havven allocation is incorrect`)
		assert(havvens.equals(await h.balanceOf(holderB)), `holderB havven allocation is incorrect`)

		// push havven forward to the next fee period
		await jumpToNextFeePeriod(h)

		// push further forward into the middle of this fee period
		const feePeriodStartTime = await h.feePeriodStartTime.call()
		const targetFeePeriodDuration = await h.targetFeePeriodDurationSeconds.call()
		const targetTime = feePeriodStartTime.plus(targetFeePeriodDuration.dividedBy(2))
		helpers.setDate(targetTime)
		await h.rolloverFeePeriod()
		assert(feePeriodStartTime.equals(await h.feePeriodStartTime.call()), 'fee period has changed')

		// transfer entire a balance away from both holders
		const nowhere = "0x1337"
		await h.transfer(nowhere, havvens, { from: holderA })
		await h.transfer(nowhere, havvens, { from: holderB })
		assert(hundredMillion.equals(await h.balanceOf(nowhere)), 'tokens were not transferred')
		assert(toUnit(0).equals(await h.balanceOf(holderA)), `holderA still has havvens`)
		assert(toUnit(0).equals(await h.balanceOf(holderB)), `holderB still has havvens`)
		
		// push havven forward to the next fee period
		await jumpToNextFeePeriod(h)

		// force average balance computation
		await h.recomputeLastAverageBalance({ from: holderA })
		await h.recomputeLastAverageBalance({ from: holderB })

		// check that the fees are distributed as expected
		await h.withdrawFeeEntitlement({ from: holderA })
		await h.withdrawFeeEntitlement({ from: holderB })
		assertWithinMargin(await n.balanceOf(holderA), quarterOfFees, 'holderA should have 1/4 the fees collected')
		assertWithinMargin(await n.balanceOf(holderB), quarterOfFees, 'holderB should have 1/4 the fees collected')
	})


})

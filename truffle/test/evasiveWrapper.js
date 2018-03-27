const deployer = require('../deployer.js')
const BigNumber = require("bignumber.js")

const EvasiveWrapper = artifacts.require('./EvasiveWrapper.sol')

const helpers = require('../testHelpers.js')


/*
 * Multiply a number by the value of UNIT in the
 * smart contract's safe math.
 */
const toUnit = (x) => new BigNumber(x).times(Math.pow(10, 18))
assert(toUnit(3).toString() === "3000000000000000000", 'toUnit() is wrong')

/*
 * Return the timestamp of the current block
 */
const timestamp = () => new BigNumber(web3.eth.getBlock(web3.eth.blockNumber).timestamp)

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
 * Push a court contract to the end of a vote
 */
const jumpToVoteEnd = async function(c, addr) {
	const voteStart = await c.voteStartTimes.call(addr)
	assert(!toUnit(0).equals(voteStart), 'vote start is zero, wont jump')
	const votingPeriod = await c.votingPeriod.call()
	const target = voteStart.plus(votingPeriod)
	helpers.setDate(target)
	assert(await c.confirming(addr), 'vote is not in the confirmation period')
}


contract('EvasiveWrapper malicious scenarios (passing means vulnerable)', function(accounts) {


	it('should successfully evade a confiscation attempt', async function() {
		const rig = await deployer.setupTestRig(accounts)
		
		const owner = rig.accounts.owner
		const n = rig.nomin
		const h = rig.havven
		const c = rig.court
		const holderA = accounts[4]
		const holderB = accounts[5]
		const mallory = accounts[6]
		const dan = accounts[7]
		const frank = accounts[8]

		// assign the havvens equally
		const hundredMillion = toUnit(Math.pow(10, 8))
		const havvens = hundredMillion.dividedBy(2)
		await h.endow(holderA, havvens, { from: owner })
		await h.endow(holderB, havvens, { from: owner })
		assert(havvens.equals(await h.balanceOf(holderA)), `holderA havven allocation is incorrect`)
		assert(havvens.equals(await h.balanceOf(holderB)), `holderB havven allocation is incorrect`)

		// issue nomins and then have accounts[0] purchase them
		const etherPrice = await n.etherPrice.call()
		const nominIssuance = toUnit(10)
		const collateral = web3.toWei(nominIssuance.dividedBy(etherPrice).times(2), 'ether')
		await n.issue(nominIssuance, {from: owner, value: collateral})
		const purchaseCost = await n.purchaseCostEther(nominIssuance)
		await n.buy(nominIssuance, {value: purchaseCost, from: mallory})
		assert(nominIssuance.equals(await n.balanceOf(mallory)), 'accounts[0] should have all the nomins')
		
		// push time forward three fee periods
		await jumpToNextFeePeriod(h)
		await jumpToNextFeePeriod(h)
		await jumpToNextFeePeriod(h)

		// update the last and penultimate balances
		await h.recomputeLastAverageBalance({ from: holderA })
		await h.recomputeLastAverageBalance({ from: holderB })

		// deploy the evasive wrapper
		const w = await EvasiveWrapper.new(n.address)

		// drop the nomin into the evasive wrapper
		const depositAddress = await w.depositAddress()
		const x = await n.approve(depositAddress, nominIssuance, { from: mallory })
		const nomins = await n.priceToSpend(nominIssuance)
		await w.importFunds(nomins, { from: mallory })
		assert(nomins.equals(await w.balanceOf.call(mallory)), 'mallory should have wrapper tokens')
		
		// do a wrapper transfer (all of mallory to dan)
		await w.transfer(dan, nomins, { from: mallory })
		assert(toUnit(0).equals(await w.balanceOf.call(mallory)), 'mallory should have no wrapper tokens')
		assert(nomins.equals(await w.balanceOf.call(dan)), 'dan should have all wrapper tokens')

		// start a confiscation motion against the pawn contract
		const pawn = await w.pawn()
		await c.beginConfiscationMotion(pawn, { from: holderA })
		assert(await c.voting(pawn), 'the vote should have started')
		await c.voteFor(pawn, { from: holderA })
		await c.voteFor(pawn, { from: holderB })
		
		// do a wrapper transfer (all of dan back to mallory)
		const tx = await w.transfer(mallory, nomins, { from: dan})
		assert(nomins.equals(await w.balanceOf.call(mallory)), 'mallory should have all wrapper tokens')
		assert(toUnit(0).equals(await w.balanceOf.call(dan)), 'dan should have no wrapper tokens')

		// ensure a new pawn was generated in the last transfer, and that it has nomins
		const newPawn = await w.pawn.call()
		assert(newPawn !== pawn, 'there should be a new pawn')
		assert(toUnit(0).lessThan(await n.balanceOf(newPawn)), 'the new pawn should have nomins')

		// finish the confiscation motion against the pawn contract
		await jumpToVoteEnd(c, pawn)
		await c.approve(pawn, { from: owner })	
		assert(await n.isFrozen(pawn) === true, 'pawn contract should be frozen')

		// have a wrapper token user withdraw their tokens
		assert(toUnit(0).equals(await n.balanceOf(frank)), 'frank should not have any nomin tokens yet')
		await w.exitWrapper(frank, toUnit(1), { from: mallory })
		assert(toUnit(1).equals(await n.balanceOf(frank)), 'frank should have recieved a real nomin from the wrapper contract')
	})

	
	it('should not be affected by a confiscation to the EvasiveWrapper contract address', async function() {
		const rig = await deployer.setupTestRig(accounts)
		
		const owner = rig.accounts.owner
		const n = rig.nomin
		const h = rig.havven
		const c = rig.court
		const holderA = accounts[4]
		const holderB = accounts[5]
		const mallory = accounts[6]
		const dan = accounts[7]
		const frank = accounts[8]

		// assign the havvens equally
		const hundredMillion = toUnit(Math.pow(10, 8))
		const havvens = hundredMillion.dividedBy(2)
		await h.endow(holderA, havvens, { from: owner })
		await h.endow(holderB, havvens, { from: owner })
		assert(havvens.equals(await h.balanceOf(holderA)), `holderA havven allocation is incorrect`)
		assert(havvens.equals(await h.balanceOf(holderB)), `holderB havven allocation is incorrect`)

		// issue nomins and then have accounts[0] purchase them
		const etherPrice = await n.etherPrice.call()
		const nominIssuance = toUnit(10)
		const collateral = web3.toWei(nominIssuance.dividedBy(etherPrice).times(2), 'ether')
		await n.issue(nominIssuance, {from: owner, value: collateral})
		const purchaseCost = await n.purchaseCostEther(nominIssuance)
		await n.buy(nominIssuance, {value: purchaseCost, from: mallory})
		assert(nominIssuance.equals(await n.balanceOf(mallory)), 'accounts[0] should have all the nomins')
		
		// push time forward three fee periods
		await jumpToNextFeePeriod(h)
		await jumpToNextFeePeriod(h)
		await jumpToNextFeePeriod(h)

		// update the last and penultimate balances
		await h.recomputeLastAverageBalance({ from: holderA })
		await h.recomputeLastAverageBalance({ from: holderB })

		// deploy the evasive wrapper
		const w = await EvasiveWrapper.new(n.address)

		// drop the nomin into the evasive wrapper
		const depositAddress = await w.depositAddress()
		const x = await n.approve(depositAddress, nominIssuance, { from: mallory })
		const nomins = await n.priceToSpend(nominIssuance)
		await w.importFunds(nomins, { from: mallory })
		assert(nomins.equals(await w.balanceOf.call(mallory)), 'mallory should have wrapper tokens')

		// take note of the feePool
		let prevFeePool = await n.feePool.call()

		// do some transfers inside the wrapper contract
		await w.transfer(dan, nomins, { from: mallory })
		assert(toUnit(0).equals(await w.balanceOf.call(mallory)), 'mallory should have no wrapper tokens')
		assert(nomins.equals(await w.balanceOf.call(dan)), 'dan should have all wrapper tokens')
		await w.transfer(mallory, nomins, { from: dan})
		assert(nomins.equals(await w.balanceOf.call(mallory)), 'mallory should have all wrapper tokens')
		assert(toUnit(0).equals(await w.balanceOf.call(dan)), 'dan should have no wrapper tokens')

		// check that the fee pool didnt increase due to the wrapped transfers
		assert(prevFeePool.equals(await n.feePool.call()), 'the fee pool should not increase after wrapped transactions')

		// start and finish a confiscation motion against the wrapper contract (should do nothing)
		await c.beginConfiscationMotion(w.address, { from: holderA })
		assert(await c.voting(w.address), 'the vote should have started')
		await c.voteFor(w.address, { from: holderA })
		await c.voteFor(w.address, { from: holderB })
		await jumpToVoteEnd(c, w.address)
		await c.approve(w.address, { from: owner })	
		assert(await n.isFrozen(w.address) === true, 'main wrapper contract should be frozen')

		// have a wrapper token user withdraw their tokens
		assert(toUnit(0).equals(await n.balanceOf(frank)), 'frank should not have any nomin tokens yet')
		await w.exitWrapper(frank, toUnit(1), { from: mallory })
		assert(toUnit(1).equals(await n.balanceOf(frank)), 'frank should have recieved a real nomin from the wrapper contract')
	})

})

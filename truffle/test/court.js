const deployer = require('../deployer.js')
const BigNumber = require("bignumber.js")

const Court = artifacts.require('./Court.sol')
const Havven = artifacts.require('./Havven.sol')
const EtherNomin = artifacts.require('./EtherNomin.sol')
const HavvenEscrow = artifacts.require('./HavvenEscrow.sol')
const TokenState = artifacts.require('./TokenState.sol')

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
 * Push a court contract to the end of a vote
 */
const jumpToVoteEnd = async function(c, motionId) {
	const voteStart = await c.motionStartTime.call(motionId)
	assert(!toUnit(0).equals(voteStart), 'vote start is zero, wont jump')
	const votingPeriod = await c.votingPeriod.call()
	const target = voteStart.plus(votingPeriod)
	helpers.setDate(target)
	assert(await c.motionConfirming(motionId), 'vote is not in the confirmation period')
}


/*
 * It is assumed that all integers are to be multipled by the
 * UNIT constant, which is 10**18.
 */
contract('Court scenarios', function(accounts) {


	it('should allow for a confiscation with 100% votes in favour and owner approval', async function() {
		const rig = await deployer.setupTestRig(accounts)

		const owner = rig.accounts.owner
		const n = rig.nomin
		const h = rig.havven
		const c = rig.court
		const holderA = accounts[4]
		const holderB = accounts[5]
		const trevor = '0x1337'

		// assign the havvens equally
		const hundredMillion = toUnit(Math.pow(10, 8))
		const havvens = hundredMillion.dividedBy(2)
		await h.endow(holderA, havvens, { from: owner })
		await h.endow(holderB, havvens, { from: owner })
		assert(havvens.equals(await h.balanceOf(holderA)), `holderA havven allocation is incorrect`)
		assert(havvens.equals(await h.balanceOf(holderB)), `holderB havven allocation is incorrect`)

		// push time forward three voting periods
		await jumpToNextFeePeriod(h)
		await jumpToNextFeePeriod(h)
		await jumpToNextFeePeriod(h)

		// update the last and penultimate balances
		await h.recomputeLastAverageBalance({ from: holderA })
		await h.recomputeLastAverageBalance({ from: holderB })

		// ensure trevor is not currently frozen or being voted upon
		assert(await n.frozen(trevor) === false, 'trevor should not be frozen yet')

		// start the confiscation
		let motionId = await c.beginMotion(trevor, { from: holderA })
		motionId = motionId.logs[0].args.motionID
		assert(await c.motionVoting(motionId), 'the vote should have started')

		// have both holders vote against trevor
		await c.voteFor(motionId, { from: holderA })
		await c.voteFor(motionId, { from: holderB })

		// // ensure the votes have been counted
		assert(hundredMillion.equals(await c.votesFor.call(motionId)), 'votes for are wrong')
		assert(toUnit(0).equals(await c.votesAgainst.call(motionId)), 'votes against are wrong')

		// jump to the end of the voting period
		await jumpToVoteEnd(c, motionId)

		// check that the vote should pass
		assert(await c.motionPasses(motionId), 'the vote should pass if approved')

		// have the owner approve the vote
		await c.approveMotion(motionId, { from: owner })	

		// ensure the vote worked
		assert(await n.frozen.call(trevor) === true, 'trevor should be frozen')

		// close the vote
		await c.closeMotion(motionId)
		assert(toUnit(0).equals(await c.motionStartTime.call(motionId)))
	})


	it('should not allow for a confiscation which has less than the required majority', async function() {
		const rig = await deployer.setupTestRig(accounts)

		const owner = rig.accounts.owner
		const n = rig.nomin
		const h = rig.havven
		const c = rig.court
		const holderA = accounts[4]
		const holderB = accounts[5]
		const trevor = '0x1337'

		// assign the havvens equally
		const hundredMillion = toUnit(Math.pow(10, 8))
		const lessThanMajority = hundredMillion.times(2).dividedBy(3).floor()
		const leftOverHavven = hundredMillion.minus(lessThanMajority)
		await h.endow(holderA, lessThanMajority, { from: owner })
		await h.endow(holderB, leftOverHavven, { from: owner })
		assert(lessThanMajority.equals(await h.balanceOf(holderA)), `holderA havven allocation is incorrect`)
		assert(leftOverHavven.equals(await h.balanceOf(holderB)), `holderB havven allocation is incorrect`)

		// push time forward three voting periods
		await jumpToNextFeePeriod(h)
		await jumpToNextFeePeriod(h)
		await jumpToNextFeePeriod(h)

		// update the last and penultimate balances
		await h.recomputeLastAverageBalance({ from: holderA })
		await h.recomputeLastAverageBalance({ from: holderB })

		// ensure trevor is not currently frozen or being vote upon
		assert(await n.frozen(trevor) === false, 'trevor should not be frozen yet')

		// start the confiscation
		let motionId = await c.beginMotion(trevor, { from: holderA })
		motionId = motionId.logs[0].args.motionID
		assert(await c.motionVoting(motionId), 'the vote should have started')

		// have both holders vote against trevor
		await c.voteFor(motionId, { from: holderA })
		await c.voteAgainst(motionId, { from: holderB })

		// ensure the votes have been counted
		assert(lessThanMajority.equals(await c.votesFor.call(motionId)), 'votes for are wrong')
		assert(leftOverHavven.equals(await c.votesAgainst.call(motionId)), 'votes against are wrong')

		// jump to the end of the voting period
		await jumpToVoteEnd(c, motionId)

		// check that the vote should pass
		assert(await c.motionPasses(motionId) === false, 'the vote should not pass if approved')

		// have the owner approve the vote
		await assertRevert(c.approveMotion(motionId, { from: owner }))

		// ensure the vote did not freeze the account
		assert(await n.frozen(trevor) === false, 'trevor should not be frozen')

		// close the vote
		await c.closeMotion(motionId)
		assert(toUnit(0).equals(await c.motionStartTime.call(trevor)))
	})


	it('should not allow for a confiscation motion from an account with less than 100 havven', async function() {
		const rig = await deployer.setupTestRig(accounts)

		const owner = rig.accounts.owner
		const n = rig.nomin
		const h = rig.havven
		const c = rig.court
		const holderA = accounts[4]
		const holderB = accounts[5]
		const trevor = '0x1337'

		// assign the havvens equally
		const hundredMillion = toUnit(Math.pow(10, 8))
		const lowStanding = toUnit(10).minus(1)
		const leftOverHavven = hundredMillion.minus(lowStanding)
		await h.endow(holderA, lowStanding, { from: owner })
		await h.endow(holderB, leftOverHavven, { from: owner })
		assert(lowStanding.equals(await h.balanceOf(holderA)), `holderA havven allocation is incorrect`)
		assert(leftOverHavven.equals(await h.balanceOf(holderB)), `holderB havven allocation is incorrect`)

		// push time forward three voting periods
		await jumpToNextFeePeriod(h)
		await jumpToNextFeePeriod(h)
		await jumpToNextFeePeriod(h)

		// update the last and penultimate balances
		await h.recomputeLastAverageBalance({ from: holderA })
		await h.recomputeLastAverageBalance({ from: holderB })

		// ensure trevor is not currently frozen or being vote upon
		assert(await n.frozen(trevor) === false, 'trevor should not be frozen yet')

		// start the confiscation
		await assertRevert(c.beginMotion(trevor, { from: holderA }))
		assert(await c.motionVoting(trevor) === false, 'the vote should not have started')
	})


})

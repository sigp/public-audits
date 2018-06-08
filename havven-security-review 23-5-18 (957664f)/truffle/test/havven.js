const deployer = require('../deployer.js')
const BigNumber = require("bignumber.js")

const Court = artifacts.require('./Court.sol')
const Havven = artifacts.require('./Havven.sol')
const Nomin = artifacts.require('./Nomin.sol')
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

const hours = (x) => x * 60 * 60
assert(hours(2) == 7200, `hours() is wrong`)

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
const withinMarginOfError = (a, b) => helpers.withinPercentageOf(a, b, 0.001)
assert(withinMarginOfError(10.0000999999, 10) === true, 'withinMarginOfError() broken')
assert(withinMarginOfError(10.000100001, 10) === false, 'withinMarginOfError() broken')
const assertWithinMargin = (a, b, msg) => assert(withinMarginOfError(a, b), msg)
assertWithinMargin(10.0000999999, 10, 'assertWithinMargin() broken')

/*
 * Push a havven contract into its next fee period
 * `h` should be a havven contract instance
 */
const jumpToNextFeePeriod = async (h) => {
		const feePeriodStartTime = await h.feePeriodStartTime.call()
		const targetFeePeriodDuration = await h.targetFeePeriodDurationSeconds.call()
		helpers.setDate(feePeriodStartTime.plus(targetFeePeriodDuration))
		//await h.rolloverFeePeriod()
		await helpers.mineOne()
		await h.checkFeePeriodRollover()
		assert(feePeriodStartTime.lessThan(await h.feePeriodStartTime.call()), 'fee period did not change')
}


/*
 * It is assumed that all integers are to be multipled by the
 * UNIT constant, which is 10**18.
 */
contract('Havven scenarios', (accounts) => {

	it('should allow vested tokens to be withdrawn', async () => {
		const rig = await deployer.setupTestRig(accounts)

		const owner = rig.accounts.owner
		const n = rig.nomin
		const h = rig.havven
		const e = rig.escrow
		const holderA = accounts[4]

		// assign the havvens to the escrow contract
		const hundredMillion = toUnit(Math.pow(10, 8))
		await h.endow(e.address, hundredMillion, { from: owner })
		assert(hundredMillion.equals(await h.balanceOf(e.address)), `escrow havven allocation is incorrect`)

		// add the holders as escrowed users
		const havvens = hundredMillion.dividedBy(2)
		const intervals = 10
		const intervalLength = days(1)
		const startDate = timestamp().plus(1)
		// create an array of times
		const times = new Array(intervals)
			.fill(0)
			.map((v, i) => startDate.plus(i * intervalLength))
		// create an array of quantities to be release at each time
		const quantities = new Array(intervals)
			.fill(0)
			.map((v, i) => havvens.dividedBy(intervals));
		await e.addVestingSchedule(holderA, times, quantities, { from: owner })
		assert(havvens.equals(await e.totalVestedAccountBalance(holderA)), 'holderA should have vested tokens')

		for(i = 0; i < times.length; i++) {
			helpers.setDate(times[i].plus(100));
			await e.vest({ from: holderA})
			const expectedBalance = quantities[i].times(i + 1)
			const balance = await h.balanceOf(holderA)
			assert(balance.equals(expectedBalance), 'holderA should receive tokens from vest()')
		}
		assert(havvens.equals(await h.balanceOf(holderA)), 'holderA should have all tokens after vesting')
	})

	it('should not allow non-whitelisted address to issue Nomins', async () => {
		const rig = await deployer.setupTestRig(accounts)

		const owner = rig.accounts.owner
		const n = rig.proxies.nomin
		const h = rig.proxies.havven
		const e = rig.escrow

		const holderA = accounts[4]

		// Endow havvens
		const tenMillion = toUnit(Math.pow(10, 7))
		await h.endow(holderA, tenMillion, { from: owner })

		// Issue nomins to max
		await helpers.assertRevert(
			h.issueNominsToMax({ from: holderA }),
			`Expected non-whitelisted account to revert`
		)
	})

	it('should transfer the amount of havven to nomin', async () => {
		const rig = await deployer.setupTestRig(accounts)

		const owner = rig.accounts.owner
		const n = rig.proxies.nomin
		const h = rig.proxies.havven
		const e = rig.escrow

		const holderA = accounts[4]
		const holderB = accounts[5]

		// Endow havvens
		const tenMillion = toUnit(Math.pow(10, 7))
		await h.endow(holderA, tenMillion, { from: owner })
		await h.endow(holderB, tenMillion, { from: owner })

		let expectedBalance = new BigNumber(toUnit(Math.pow(10, 7)))
		let hbalA = await h.balanceOf(holderA)
		assert(hbalA.cmp(expectedBalance) == 0, `Havven Balance Expected: ${expectedBalance}; Got: ${hbalA}`)

		// Whitelist the accounts
		await h.setWhitelisted(holderA, true, { from: owner })
		await h.setWhitelisted(holderB, true, { from: owner })

		// Issue all the nomins
		await h.issueNominsToMax({ from: holderA })
		await h.issueNominsToMax({ from: holderB })

		let havUsd = await h.HAVtoUSD(expectedBalance)
		let nomBalance = await n.balanceOf(holderA)

		expectedBalance = new BigNumber('0.05').times(havUsd)

		assert(expectedBalance.cmp(nomBalance) == 0,
			`Nomin Balance Expected: ${expectedBalance.toString()};
			Got: ${nomBalance}`
		)
	})

	it('should transfer the defined amount of havven to nomin', async () => {
		const rig = await deployer.setupTestRig(accounts)

		const owner = rig.accounts.owner
		const n = rig.proxies.nomin
		const h = rig.proxies.havven
		const e = rig.escrow

		const holderA = accounts[4]
		const holderB = accounts[5]

		// Endow havvens
		const tenMillion = toUnit(Math.pow(10, 7))
		await h.endow(holderA, tenMillion, { from: owner })
		await h.endow(holderB, tenMillion, { from: owner })

		// Whitelist the accounts
		await h.setWhitelisted(holderA, true, { from: owner })
		await h.setWhitelisted(holderB, true, { from: owner })

		// Issue the nomins
		await h.issueNomins(toUnit(Math.pow(10, 7)), { from: holderA })
		await h.issueNomins(toUnit(Math.pow(10, 6)), { from: holderB })

		let expectedBalanceA = toUnit(Math.pow(10, 7))
		let expectedBalanceB = toUnit(Math.pow(10, 6))

		let nomBalanceA = await n.balanceOf(holderA)
		let nomBalanceB = await n.balanceOf(holderB)

		assert(expectedBalanceA.cmp(nomBalanceA) == 0,
			`Nomin Balance A Expected: ${expectedBalanceA.toString()};
			Got: ${nomBalanceA}`
		)

		assert(expectedBalanceB.cmp(nomBalanceB) == 0,
			`Nomin Balance B Expected: ${expectedBalanceB.toString()};
			Got: ${nomBalanceB}`
		)

		// Make sure the correct number of Havven are locked
		let expectedLockedA = await h.USDtoHAV(nomBalanceA.dividedBy(
			new BigNumber('0.05')))

		let lockedA = await h.lockedHavvens(holderA)

		let expectedLockedB = await h.USDtoHAV(nomBalanceB.dividedBy(
			new BigNumber('0.05')))

		let lockedB = await h.lockedHavvens(holderB)

		assert(expectedLockedA.cmp(lockedA) == 0,
			`Expected: ${expectedLockedA}; Got: ${lockedA}`)

		assert(expectedLockedB.cmp(lockedB) == 0,
			`Expected: ${expectedLockedB}; Got: ${lockedB}`)
	})


	it('should distribute fees evenly', async () => {
		const rig = await deployer.setupTestRig(accounts)

		const owner = rig.accounts.owner
		const n = rig.proxies.nomin
		const h = rig.proxies.havven
		const e = rig.escrow

		const holderA = accounts[4]
		const holderB = accounts[5]
		const holderC = accounts[6]
		const holderD = accounts[7]

		// Endow havvens
		const tenMillion = toUnit(Math.pow(10, 7))
		await h.endow(holderC, tenMillion, { from: owner })
		await h.endow(holderD, tenMillion, { from: owner })

		// Whitelist the accounts
		await h.setWhitelisted(holderA, true, { from: owner })
		await h.setWhitelisted(holderB, true, { from: owner })
		await h.setWhitelisted(holderC, true, { from: owner })
		await h.setWhitelisted(holderD, true, { from: owner })

		// Issue the nomins
		await h.issueNomins(toUnit(Math.pow(10, 7)), { from: holderC })
		await h.issueNomins(toUnit(Math.pow(10, 6)), { from: holderD })

		// do a bunch of transactions between accounts[0] and accounts[6]
		const rounds = 1
		const nominsSent = await n.transferPlusFee(toUnit(1))
		const nominsReturned = await n.transferPlusFee(toUnit(0.5))
		for (var i = 0; i < rounds; ++i) {
			await n.transfer(holderC, nominsSent, { from: holderD })
			await n.transfer(holderD, nominsReturned, { from: holderC })
		}


		const transferVolume = toUnit(1).plus(toUnit(0.5)).times(rounds)
		const fees = bpFee(transferVolume, 15)
		// assert our expectation is reality
		assert(fees.equals(new BigNumber(await n.feePool.call())), `feePool expected: ${fees}; Got: ${new BigNumber(await n.feePool.call())}`)

		// assign the havvens equally
		const havvens = tenMillion .dividedBy(2)
		await h.endow(holderA, havvens, { from: owner })
		await h.endow(holderB, havvens, { from: owner })
		assert(havvens.equals(await h.balanceOf(holderA)), `holderA havven allocation is incorrect`)
		assert(havvens.equals(await h.balanceOf(holderB)), `holderB havven allocation is incorrect`)

		// Issue the nomins to the holders
		await h.issueNominsToMax({ from: holderA })
		await h.issueNominsToMax({ from: holderB })

		// push havven into the next fee period
		await jumpToNextFeePeriod(h)

		// Check that the fees can be withdrawn.
		let balanceA = await n.balanceOf(holderA)
		let balanceB = await n.balanceOf(holderB)
		await h.withdrawFeeEntitlement({ from: holderA })
		await h.withdrawFeeEntitlement({ from: holderB })

		// Console logs to check internal variable states
		// console.log(`Frozen ${await n.frozen.call(holderA)}`)
		// console.log(`Total Issued Balance ${await h.totalIssuedNominBalanceData.call()}`)
		// console.log(`Nomin Issued Balance ${await h.issuedNominBalanceData.call(holderA)}`)
		// console.log(`LastFees ${await h.lastFeesCollected.call()}`)
		// console.log(`BalanceA ${await n.balanceOf(holderA)}`)

		// assert the fees are as expected
		const halfOfFees = fees.dividedBy(2)
		assertWithinMargin(await n.balanceOf(holderA), halfOfFees.plus(balanceA), 'holderA should have half the fees collected')
		assertWithinMargin(await n.balanceOf(holderB), halfOfFees.plus(balanceB), 'holderB should have half the fees collected')
	})

	it('should not allow double fee withdrawal', async () => {
		const rig = await deployer.setupTestRig(accounts)

		const owner = rig.accounts.owner
		const n = rig.proxies.nomin
		const h = rig.proxies.havven
		const e = rig.escrow

		const holderA = accounts[4]
		const holderC = accounts[6]
		const holderD = accounts[7]

		// Endow havvens
		const tenMillion = toUnit(Math.pow(10, 7))
		await h.endow(holderC, tenMillion, { from: owner })
		await h.endow(holderD, tenMillion, { from: owner })

		// Whitelist the accounts
		await h.setWhitelisted(holderA, true, { from: owner })
		await h.setWhitelisted(holderC, true, { from: owner })
		await h.setWhitelisted(holderD, true, { from: owner })

		// Issue the nomins
		await h.issueNomins(toUnit(Math.pow(10, 7)), { from: holderC })
		await h.issueNomins(toUnit(Math.pow(10, 6)), { from: holderD })

		// do a bunch of transactions between accounts[0] and accounts[6]
		const rounds = 1
		const nominsSent = await n.transferPlusFee(toUnit(1))
		const nominsReturned = await n.transferPlusFee(toUnit(0.5))
		for (var i = 0; i < rounds; ++i) {
			await n.transfer(holderC, nominsSent, { from: holderD })
			await n.transfer(holderD, nominsReturned, { from: holderC })
		}

		const transferVolume = toUnit(1).plus(toUnit(0.5)).times(rounds)
		const fees = bpFee(transferVolume, 15)
		// assert our expectation is reality
		assert(fees.equals(new BigNumber(await n.feePool.call())), `feePool expected: ${fees}; Got: ${new BigNumber(await n.feePool.call())}`)

		// assign the havvens equally
		const havvens = tenMillion .dividedBy(2)
		await h.endow(holderA, havvens, { from: owner })
		assert(havvens.equals(await h.balanceOf(holderA)), `holderA havven allocation is incorrect`)
		// Issue the nomins to the holders
		await h.issueNominsToMax({ from: holderA })

		// push havven into the next fee period
		await jumpToNextFeePeriod(h)
		await h.withdrawFeeEntitlement({ from: holderA })
		await helpers.assertRevert(h.withdrawFeeEntitlement({ from: holderA }))
	})

	it('should be able to burn nomins', async () => {
		const rig = await deployer.setupTestRig(accounts)

		const owner = rig.accounts.owner
		const n = rig.proxies.nomin
		const h = rig.proxies.havven
		const e = rig.escrow

		const holderA = accounts[4]
		const holderB = accounts[5]

		// Endow havvens
		const tenMillion = toUnit(Math.pow(10, 7))
		await h.endow(holderA, tenMillion, { from: owner })
		await h.endow(holderB, tenMillion, { from: owner })

		// Whitelist the accounts
		await h.setWhitelisted(holderA, true, { from: owner })
		await h.setWhitelisted(holderB, true, { from: owner })

		// Issue the nomins
		await h.issueNomins(toUnit(Math.pow(10, 7)), { from: holderA })
		await h.issueNomins(toUnit(Math.pow(10, 6)), { from: holderB })

		let lockedA = await h.lockedHavvens(holderA)
		let lockedB = await h.lockedHavvens(holderB)

		let balanceA = await h.balanceOf(holderA)
		let balanceB = await h.balanceOf(holderB)

		let nominA = await n.balanceOf(holderA)
		let nominB = await n.balanceOf(holderB)

		// lets burn some nomins
		await h.burnNomins(nominA.dividedBy(2), { from: holderA })
		await h.burnNomins(nominB, { from: holderB })

		assert(new BigNumber(nominA.dividedBy(2)).equals(await n.balanceOf(holderA)), `Nomin Contract: Expected nomins to be burnt`)
		assert(new BigNumber(0).equals(await n.balanceOf(holderB)), `Nomin Contract: Expected nomins to be burnt`)
		assertWithinMargin(new BigNumber(nominA.dividedBy(2)), await h.nominsIssued.call(holderA), `Havven Contract: Expected nomins to be burnt`)
		assert(new BigNumber(0).cmp(await h.nominsIssued.call(holderB)) == 0, `Havven Contract: Expected nomins to be burnt`)

		// Previously locked should be more than current
		assert(lockedA.cmp(await h.lockedHavvens(holderA)) == 1, `Expected locked to be less`)
		assert(lockedB.cmp(await h.lockedHavvens(holderB)) == 1, `Expected locked to be less`)
	})

	it('should not be able to burn nomins if none issued', async () => {
		const rig = await deployer.setupTestRig(accounts)

		const owner = rig.accounts.owner
		const n = rig.proxies.nomin
		const h = rig.proxies.havven
		const e = rig.escrow

		const holderA = accounts[4]

		// Endow havvens
		const tenMillion = toUnit(Math.pow(10, 7))
		await h.endow(holderA, tenMillion, { from: owner })

		// Whitelist the accounts
		await h.setWhitelisted(holderA, true, { from: owner })

		// lets burn some nomins
		await assertRevert(h.burnNomins(toUnit(100), { from: holderA }))
	})

	it('should lock extra tokens with lower Havven price changes', async () => {
		const rig = await deployer.setupTestRig(accounts)

		const owner = rig.accounts.owner
		const oracle = rig.accounts.oracle
		const n = rig.proxies.nomin
		const h = rig.proxies.havven
    const hd = rig.havven
		const e = rig.escrow

		const holderA = accounts[4]

		// Endow havvens
		const tenMillion = toUnit(Math.pow(10, 7))
		await h.endow(holderA, tenMillion, { from: owner })

		// Whitelist the accounts
		await h.setWhitelisted(holderA, true, { from: owner })

		// Issue the nomins
		await h.issueNomins(toUnit(Math.pow(10, 6)), { from: holderA })

    let lockedHavvens = await h.lockedHavvens.call(holderA)

		// push havven into the next fee period
		// helpers.setDate(timestamp().plus(hours(1)))

		helpers.setDate(timestamp().plus(hours(1)))

		helpers.mineOne()

		// change price
		await hd.updatePrice(toUnit(1000), timestamp().plus(4), { from: oracle })

    let newLockedHavvens = await h.lockedHavvens.call(holderA)

    // Expect more locked tokens. 
    assert(lockedHavvens < newLockedHavvens, "there should me more Havvens locked"); 
    assert(newLockedHavvens.equals(new BigNumber(2e22)), "there should be 2e22 locked Havvens");
	})
})

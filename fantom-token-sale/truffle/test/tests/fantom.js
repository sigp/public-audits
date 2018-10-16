const deployer = require('../utils/deployer.js')
const helpers = require('../utils/testHelpers.js')
const BigNumber = require('bignumber.js')

const Fantom = artifacts.require('./FantomToken.sol')

/*
 * Return the amount of seconds in x days
 */
const days = (x) => x * 60 * 60 * 24
assert(days(2) === 172800, 'days() is wrong')

const hours = (x) => x * 60 * 60
assert(hours(2) == 7200, `hours() is wrong`)

const minutes = (x) => x * 60

const dateBySeconds = (x) => new BigNumber(Math.floor(x/1000))
assert(dateBySeconds(new Date(Date.UTC(2018, 00, 01, 10, 10, 10))).cmp((new BigNumber(1514801410))) == 0, 'dateBySeconds() is wrong')

/*
 * Return the timestamp of the current block
 */
const timestamp = () => new BigNumber(web3.eth.getBlock(web3.eth.blockNumber).timestamp)

contract('LockSlots', (accounts) => {

	it('[isAvailableLockSlot] should return true for account no locked slot', async () => {
		const rig = await deployer.setupContract(accounts)
		const holder = accounts[2]

		let slotStatus = await rig.fantom.isAvailableLockSlot(holder, 
			dateBySeconds(new Date(2018, 04, 23, 23, 01, 01)))

		assert(slotStatus == true, `Lock Status, expected true; got ${slotStatus}`)

		// Check in the past
		slotStatus = await rig.fantom.isAvailableLockSlot(holder, 
			dateBySeconds(new Date(2017, 04, 23, 23, 01, 01)))

		assert(slotStatus == true, `Lock Status, expected true; got ${slotStatus}`)
	})

	it('[mintTokensLocked] should lock correct number of tokens', async () => {
		const rig = await deployer.setupContract(accounts)
		const owner = rig.owner
		const fantom = rig.fantom
		const lockedHolder = accounts[2]

		// whitelist the account
		await fantom.addToWhitelist(lockedHolder, {from: owner})

		assert(true == await fantom.whitelist.call(lockedHolder), 'Whitelist status incorrect')

		// mint locked tokens for account
    let dateToLock = rig.ICOStartTime + days(5)
		await fantom.mintTokensLocked(1, lockedHolder, 10, dateToLock, {from: owner})

		// check the number of locked tokens
		let lockedTokens = await fantom.lockedTokens(lockedHolder)

		assert(lockedTokens.cmp(new BigNumber(10)) == 0, `Number of minted tokens locked; expected 10; Got: ${lockedTokens}`)
	})

	it('[mintTokensLockedMultiple] mint the correct amount of locked tokens', async () => {
		const rig = await deployer.setupContract(accounts)
		const owner = rig.owner
		const fantom = rig.fantom
    const startDate = rig.ICOStartTime
		const lockedHolder = accounts[2]

		// whitelist the account
		await fantom.addToWhitelist(lockedHolder, {from: owner})

		let initialDate = new BigNumber(startDate + days(1))

		tokensToMint = [5,4,3,2,1]
		terms = [
			initialDate.plus(days(1)),
			initialDate.plus(days(2)),
			initialDate.plus(days(3)),
			initialDate.plus(days(4)),
			initialDate.plus(days(5))
		]

		accounts = [
			lockedHolder,
			lockedHolder,
			lockedHolder,
			lockedHolder,
			lockedHolder
		]

		await fantom.mintTokensLockedMultiple(1, accounts, tokensToMint, terms, {from: owner})

		let lockedTokens = await fantom.lockedTokens(lockedHolder)

		assert(lockedTokens.cmp(new BigNumber(15)) == 0, `Number of minted tokens locked; expected 15; Got: ${lockedTokens}`)
	})

	it('[mintTokensLockedMultiple] number of lockslots fill correctly', async () => {
		const rig = await deployer.setupContract(accounts)
		const owner = rig.owner
		const fantom = rig.fantom
    const startDate = rig.ICOStartTime
		const lockedHolder = accounts[2]

		// whitelist the account
		await fantom.addToWhitelist(lockedHolder, {from: owner})

		let initialDate = new BigNumber(startDate + days(1))
		tokensToMint = [5,4,3,2,1]
		terms = [
			initialDate.plus(days(1)),
			initialDate.plus(days(2)),
			initialDate.plus(days(3)),
			initialDate.plus(days(4)),
			initialDate.plus(days(5))
		]

		accounts = [
			lockedHolder,
			lockedHolder,
			lockedHolder,
			lockedHolder,
			lockedHolder
		]

		await fantom.mintTokensLockedMultiple(1, accounts, tokensToMint, terms, {from: owner})

		let lockedTokens = await fantom.lockedTokens(lockedHolder)

		assert(lockedTokens.cmp(new BigNumber(15)) == 0, `Number of minted tokens locked; expected 15; Got: ${lockedTokens}`)

		// Available Lock Slots
		let slotStatus = await rig.fantom.isAvailableLockSlot(lockedHolder, 
			initialDate.plus(days(2)))
		
		assert(true == slotStatus, "Lock slot available for same term")

		slotStatus = await rig.fantom.isAvailableLockSlot(lockedHolder, 
			initialDate.plus(days(6)))

		assert(false == slotStatus, "Lock slot not available for extra term")
		
	})


	it('[mintTokens] should not lock the tokens', async () => {
		const rig = await deployer.setupContract(accounts)
		const owner = rig.owner
		const fantom = rig.fantom
		const holder = accounts[2]

		// whitelist the account
		await fantom.addToWhitelist(holder, {from: owner})

		await fantom.mintTokens(1, holder, 10, {from: owner})

		let lockedTokens = await fantom.lockedTokens(holder)

		assert(lockedTokens.cmp(new BigNumber(0)) == 0, `Number of minted tokens locked; expected 0; Got: ${lockedTokens}`)

		let unlockedTokens = await fantom.unlockedTokens(holder)
		assert(unlockedTokens.cmp(new BigNumber(10)) == 0, `Number of minted tokens unlocked; expected 10; Got: ${lockedTokens}`)
	})
})


contract('FantomICODates', (accounts) => {


	it('should not allow public to change dates', async () => {
		const rig = await deployer.setupContract(accounts)
    const icoStartTime = rig.ICOStartTime

		let newD = icoStartTime - 10 // Must be before the current start date. 

		await helpers.assertRevert(rig.fantom.setDateMainStart(newD, {from: accounts[1]}))
	})

	it('should allow owner to change the dates', async () => {

		const rig = await deployer.setupContract(accounts)
    const icoStartTime = rig.ICOStartTime

		let newD = new BigNumber(icoStartTime - 10) // Must be before the current start date. 

		await rig.fantom.setDateMainEnd(newD.plus(days(10)), {from: rig.owner})
		await rig.fantom.setDateMainStart(newD, {from: rig.owner})

		assert(newD.cmp(await rig.fantom.dateMainStart.call()) == 0, 'start date set')
		assert(newD.plus(days(10)).cmp(await rig.fantom.dateMainEnd.call()) == 0, 'end date set')
	})

	it('should not allow owner to change dates into past', async() => {
		const rig = await deployer.setupContract(accounts)
    const icoStartTime = rig.ICOStartTime

		let pastD = new BigNumber(icoStartTime - days(360)) // Must be before the current start date. 

		await helpers.assertRevert(rig.fantom.setDateMainEnd(pastD, {from: rig.owner}))
	})

	it('should not allow owner to set start date after or equal to end date', async () => {

		const rig = await deployer.setupContract(accounts)
    const icoStartTime = rig.ICOStartTime

		let newD = new BigNumber(icoStartTime) // Must be before the current start date. 


		await rig.fantom.setDateMainEnd(newD.plus(days(10)), {from: rig.owner})
		await helpers.assertRevert(rig.fantom.setDateMainStart(newD.plus(days(11)), {from: rig.owner}))
		await helpers.assertRevert(rig.fantom.setDateMainStart(newD.plus(days(10)), {from: rig.owner}))
		await rig.fantom.setDateMainStart(newD.plus(days(10)).minus(1), {from: rig.owner})


		assert(newD.plus(days(10)).cmp(await rig.fantom.dateMainEnd.call()) == 0, 'end date set')
		assert(newD.plus(days(10)).minus(1).cmp(await rig.fantom.dateMainStart.call()) == 0, 'start date set')
	})

	it('[mainsale] should detect main period', async () => {

		const rig = await deployer.setupContract(accounts)
    const icoStartTime = rig.icoStartTime

		assert(false == (await rig.fantom.isMainFirstDay()), 'Main should not have started')

		helpers.setDate(timestamp().plus(1000))

		assert(true == (await rig.fantom.isMainFirstDay()), 'Can detect first day of main')
		assert(true == (await rig.fantom.isMain()), 'Can detect main')

		helpers.setDate(timestamp().plus(days(2)))

		assert(false == (await rig.fantom.isMainFirstDay()), 'first day of main finished')
		assert(true == (await rig.fantom.isMain()), 'Can detect main')

		helpers.setDate(timestamp().plus(days(14)))

		assert(false == (await rig.fantom.isMainFirstDay()), 'Can detect first day of main')
		assert(false == (await rig.fantom.isMain()), 'Can detect main')
	})

})


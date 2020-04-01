const deployer = require('../deployer.js')
const BigNumber = require('bignumber.js')
const synthetixHelpers = require('../synthetixHelpers.js')
const helpers = require('../testHelpers.js')
const toBN = web3.utils.toBN

const zeroAddress = '0x0000000000000000000000000000000000000000'

const assertRevert = helpers.assertRevert
const toUnit = synthetixHelpers.toUnit

const xdrCurrencyKey = 0x58445200;

contract('synthetix', (accounts) => {
	describe('constructor', function () {
		it('sets public variables', async function () {
			let rig = await deployer.deployTestRig(accounts.slice(0, 6))

			assert(
				await rig.synthetix.owner() === rig.accounts.owner,
				'Owner is not as expected'
			)
			assert(
				await rig.synthetix.selfDestructBeneficiary() === rig.accounts.owner,
				'selfDestructBeneficiary is not owner, as expected.'
			)
			// TODO: Check that beneficiary is not supposed to be owner.
			assert(await rig.synthetix.name() === 'Synthetix Network Token', 'Incorrect name')
			assert(await rig.synthetix.symbol() === 'SNX', 'Incorrect symbol')

			let decimals = await rig.synthetix.decimals()
			assert(new BigNumber(decimals).eq(18), 'Incorrect decimals')

			let supply = await rig.synthetix.totalSupply()
			assert(new BigNumber(supply).eq(toUnit(1e8)), 'Incorrect supply')
		})
	})

	describe('add/remove synth contract', function () {
		it('can add a synth contract only once and then remove it only once', async function () {
			let rig = await deployer.deployTestRig(accounts.slice(0, 6))

			// Create a new synth contract with a new currency key.
			let newCurrencyKey = web3.utils.asciiToHex('nNEW')
			// eslint-disable-next-line no-unused-vars
			const [newSynth, _a, _b] = await deployer.deploySynth(
				rig.accounts.owner,
				rig.synthetix,
				rig.feePool,
				newCurrencyKey
			)

			// Ensure that the new currency key does not exist yet.
			const initialSynthCount = await rig.synthetix.availableSynthCount()
			for (var i in initialSynthCount.toNumber()) {
				const iterKey = await rig.synthetix.availableSynths(i)
				assert(iterKey !== newCurrencyKey)
			}

			// Add the new synth contract to the Havven contract.
			await rig.synthetix.addSynth(newSynth.address, { from: rig.accounts.owner })

			// Check that the availableSynths array expanded
			const newSynthCount = await rig.synthetix.availableSynthCount()
			assert(newSynthCount.eq(initialSynthCount.add(toBN(1))), 'there should be an additional synth')

			// Check the synth address was added correctly
			assert(await rig.synthetix.availableSynths(newSynthCount.sub(toBN(1))), 'the additional synth should be correct')
			assert((await rig.synthetix.synths(newCurrencyKey) === newSynth.address), 'the added synth address should be correct')

			// It should fail second time around.
			await assertRevert(rig.synthetix.addSynth(newSynth.address, { from: rig.accounts.owner }))

			// Remove the newly added synth and ensure it is gone
			await rig.synthetix.removeSynth(newCurrencyKey, { from: rig.accounts.owner })
			assert((await rig.synthetix.availableSynthCount()).eq(initialSynthCount), 'there should be one less synth')
			assert((await rig.synthetix.synths(newCurrencyKey) === zeroAddress), 'the added synth address should be removed')

			// It shoud fail if it is removed again
			await assertRevert(rig.synthetix.removeSynth(newCurrencyKey, { from: rig.accounts.owner }))
		})

		it('can have all synths deleted in forward order', async function () {
			let rig = await deployer.deployTestRig(accounts.slice(0, 6))

			// Loop through the synths and delete them all
			for (var i in rig.currencyKeys.slice(0, rig.currencyKeys.length - 1)) {
				let currencyKey = rig.currencyKeys[i]
        if (currencyKey != xdrCurrencyKey) {
				  await rig.synthetix.removeSynth(currencyKey, { from: rig.accounts.owner })
        }
			}

			assert((await rig.synthetix.availableSynthCount()).eq(toBN(1)), 'there should be only one synth left')
		})

		it('can have all synths deleted in reverse order', async function () {
			let rig = await deployer.deployTestRig(accounts.slice(0, 6))

			// Loop through the synths in reverse order and delete them all
			for (var i = rig.currencyKeys.length - 2; i >= 0; i--) {
				let currencyKey = rig.currencyKeys[i];;
        if (currencyKey != xdrCurrencyKey) {
				  await rig.synthetix.removeSynth(currencyKey, { from: rig.accounts.owner })
        }
			}

			assert((await rig.synthetix.availableSynthCount()).eq(toBN(1)), 'there should be only one synth left')
		})

		it('does not permit deleteing the XDR nomin', async function () {
			let rig = await deployer.deployTestRig(accounts.slice(0, 6))
      assertRevert(rig.synthetix.removeSynth(xdrCurrencyKey, { from: rig.accounts.owner }))
		})
	})
})

const TokenReenterer = artifacts.require('TokenReenterer.sol')
const FallbackRecipient = artifacts.require('FallbackRecipient.sol')
const toBN = web3.utils.toBN;

const deployer = require('../deployer.js')
const synthetixHelpers = require('../synthetixHelpers.js')

const toUnit = synthetixHelpers.toUnit

contract('synth', (accounts) => {
	describe('token fallback', function () {
		it('calls token fallback', async function () {
			const rig = await deployer.deployTestRig(accounts.slice(0, 6))

			const fr = await FallbackRecipient.new()

			assert((await fr.triggered()) === false, 'the fallback should not have been triggered')

			const currencyKey = 'sUSD'
			const synth = rig.synths[currencyKey]

			const userA = accounts[7]
			const userB = fr.address

			// Allocate some synths to userA
			await synthetixHelpers.allocateSynthsTo(rig, currencyKey, userA, toUnit(10))
			assert((await synth.balanceOf(userA)).eq(toUnit(10)), 'userA balance incorrect')
			assert((await synth.balanceOf(userB)).eq(toUnit(0)), 'userB balance incorrect')

			const tx = await synth.transfer(userB, toUnit(5), { from: userA })

			assert((await fr.triggered()) === true, 'the fallback should have been triggered')
		})

		it('does not allow reentrancy from token fallback', async function () {
			const rig = await deployer.deployTestRig(accounts.slice(0, 6))

			// Deploy a contract that will attempt to re-enter on a tokenFallback
			// call.
			const te = await TokenReenterer.new()

			assert((await te.enterCount()).eq(toBN(0)), 'enterCount should be 0')

			const currencyKey = 'sUSD'
			const synth = rig.synths[currencyKey]

			const userA = accounts[7]
			const userB = te.address

			// Allocate some synths to userA
			await synthetixHelpers.allocateSynthsTo(rig, currencyKey, userA, toUnit(10))
			assert((await synth.balanceOf(userA)).eq(toUnit(10)), 'userA balance incorrect')
			assert((await synth.balanceOf(userB)).eq(toUnit(0)), 'userB balance incorrect')

			const tx = await synth.transfer(userB, toUnit(5), { from: userA })

			assert((await te.enterCount()).eq(toBN(1)), 'enterCount should be 0')
		})
	})
})

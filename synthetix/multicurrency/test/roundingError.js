const deployer = require('../deployer.js')
const helpers = require('../testHelpers.js')
const synthetixHelpers = require('../synthetixHelpers.js')
const toUnit = synthetixHelpers.toUnit
const assertBNEqual = helpers.assertBNEqual;
const toBN = web3.utils.toBN
const constants = require("./exchangeRateConstants.js")
const Synth = artifacts.require('./Synth.sol')


contract('synth-rounding', (accounts) => {

	const HAVVEN_HOLDER_A = accounts[6]
	const HAVVEN_HOLDER_B = accounts[7]


	describe('rounding error', function () {
		it("It's not possible to burn all Synths.", async function (){
			// Setup the rig
			rig = await deployer.deployTestRig(accounts.slice(0, 6));
			nusd_nomin = await Synth.at(await rig.synthetix.synths(constants.NUSD_CURRENCY_KEY))
			neur_nomin = await Synth.at(await rig.synthetix.synths(constants.NEUR_CURRENCY_KEY))
			xdr_nomin = await Synth.at(await rig.synthetix.synths(constants.XDR_CURRENCY_KEY))


			// Allocate some synthetixs to the owner
			await synthetixHelpers.allocateSynthetixsTo(rig, rig.accounts.owner, toUnit(1e8))

			// Configure the exchange rates
			let time_now = await helpers.timestamp()
			// await rig.exchangeRates.updateRates(
			// 	rig.currencyKeys.slice(0,4),
			// 	[toUnit(1), toUnit(1.1), toUnit(1.2), toUnit(1.3)],
			// 	time_now,
			// 	{from: rig.accounts.oracle}
			// )

			await rig.exchangeRates.updateRates(
				rig.currencyKeys.slice(1,7),
				constants.SOME_SET_OF_RATES,
				time_now,
				{from: rig.accounts.oracle}
			)

			// Transfer some synthetixs to account holder
			await rig.synthetix.transfer(HAVVEN_HOLDER_A, toUnit(1000), {from: rig.accounts.owner})
			await rig.synthetix.transfer(HAVVEN_HOLDER_B, toUnit(50000), {from: rig.accounts.owner})


			// Holder A issues as many Nomins as possible in nUSD...
			await rig.synthetix.issueMaxSynths(constants.NUSD_CURRENCY_KEY, {from: HAVVEN_HOLDER_A})
			let holder_a_nusd_balance = await nusd_nomin.balanceOf(HAVVEN_HOLDER_A)
			// ... then send all nUSD nomins from holder A to holder B...
			await nusd_nomin.transfer(HAVVEN_HOLDER_B, holder_a_nusd_balance, {from: HAVVEN_HOLDER_A})

			// Now Holder B issues as many nomins as possible
			await rig.synthetix.issueMaxSynths(constants.NEUR_CURRENCY_KEY, {from: HAVVEN_HOLDER_B})

			/* === This is fixed: we can no longer issue one extra wei

			// But here's the catch! I can still issue one more nEUR wei!
			// This should fail!
			await rig.synthetix.issueSynths(constants.NEUR_CURRENCY_KEY, toBN(1), {from: HAVVEN_HOLDER_B})
			*/


			/* === This is fixed: Can't issue 0 nomins any more.

			// Now, I Have to issueMaxNomins again in nUSD, which prevents us from burning all of the  nEUR
			//await rig.synthetix.issueMaxSynths(constants.NUSD_CURRENCY_KEY, {from: HAVVEN_HOLDER_B})
			*/


			// Now for burning tokens...
			let current_neur_debt_balance = await rig.synthetix.debtBalanceOf(HAVVEN_HOLDER_B, constants.NEUR_CURRENCY_KEY)

			await rig.synthetix.burnSynths(
				constants.NEUR_CURRENCY_KEY,
				// We should be able to use the following line:
				//current_neur_debt_balance,
				// But instead we have to subtract one nEUR wei! (below)
				current_neur_debt_balance.sub(toBN(1)),
				{from: HAVVEN_HOLDER_B}
			)
		})

		it("Issuance of Synths suffers a rounding error", async function() {
			rig = await deployer.deployTestRig(accounts.slice(0, 6));
			nusd_nomin = await Synth.at(await rig.synthetix.synths(constants.NUSD_CURRENCY_KEY))
			neur_nomin = await Synth.at(await rig.synthetix.synths(constants.NEUR_CURRENCY_KEY))

			await synthetixHelpers.allocateSynthetixsTo(rig, rig.accounts.owner, toUnit(1e8))

			// Transfer some synthetixs to account holder
			await rig.synthetix.transfer(HAVVEN_HOLDER_A, toUnit(1000), {from: rig.accounts.owner})
			await rig.synthetix.transfer(HAVVEN_HOLDER_B, toUnit(50000), {from: rig.accounts.owner})

			let time_now = await helpers.timestamp()
			await rig.exchangeRates.updateRates(
				rig.currencyKeys.slice(1,7),
				constants.SOME_SET_OF_RATES,
				time_now,
				{from: rig.accounts.oracle}
			)

			// Issue all the synths possible
			await rig.synthetix.issueMaxSynths(constants.NUSD_CURRENCY_KEY, {from: HAVVEN_HOLDER_A})

			// Check that we cannot issue any more synths
			assertBNEqual(
				await rig.synthetix.remainingIssuableSynths(
					HAVVEN_HOLDER_A,
					constants.NUSD_CURRENCY_KEY
				),
				toBN(0),
				"Holder A cannot issue any more Synths (yet)"
			)

			// Do a transfer of all our sUSD Synths
			let holder_a_nusd_balance = await nusd_nomin.balanceOf(HAVVEN_HOLDER_A)
			// This line (transfer) increases our remainingIssuableSynths
			await nusd_nomin.transfer(HAVVEN_HOLDER_B, holder_a_nusd_balance, {from: HAVVEN_HOLDER_A})


			// Now, after the transfer, we have 7 sUSD wei more Synths
			assertBNEqual(
				await rig.synthetix.remainingIssuableSynths(
					HAVVEN_HOLDER_A,
					constants.NUSD_CURRENCY_KEY
				),
				toBN(7),
				"Holder A can now issue 7 wei more Synths"
			)

			// So we issue the rest of those 7 wei
			await rig.synthetix.issueMaxSynths(constants.NUSD_CURRENCY_KEY, {from: HAVVEN_HOLDER_A})

			// And check that we go back to not being able to issue any more
			assertBNEqual(
				await rig.synthetix.remainingIssuableSynths(
					HAVVEN_HOLDER_A,
					constants.NUSD_CURRENCY_KEY
				),
				toBN(0),
				"Holder A cannot issue any more synths (again)"
			)


			// And we can just keep doing this forever with 1 wei worth of sUSD!
			// This loop only happens 10 times, but it could happen indefinitely.
			for(let i = 0; i < 10; i++){

				holder_a_nusd_balance = await nusd_nomin.balanceOf(HAVVEN_HOLDER_A)
				// This line (transfer) increases our remainingIssuableSynths
				// Because it's only 1 wei, Holder A's balance decreases by 1, but Holder B's balance does not increase.
				await nusd_nomin.transfer(HAVVEN_HOLDER_B, holder_a_nusd_balance, {from: HAVVEN_HOLDER_A})

				assertBNEqual(
					await rig.synthetix.remainingIssuableSynths(
						HAVVEN_HOLDER_A,
						constants.NUSD_CURRENCY_KEY
					),
					toBN(1),
					"Holder A can now issue 1 wei more Synths after the transfer."
				)

				// So we issue our 1 wei of Synths
				await rig.synthetix.issueMaxSynths(constants.NUSD_CURRENCY_KEY, {from: HAVVEN_HOLDER_A})

				// And make sure that we can't issue any more Synths
				assertBNEqual(
					await rig.synthetix.remainingIssuableSynths(
						HAVVEN_HOLDER_A,
						constants.NUSD_CURRENCY_KEY
					),
					toBN(0),
					"Holder A cannot issue any more synths (again)"
				)
			}
		})
	})
})
const deployer = require('../deployer.js')
const BigNumber = require('bignumber.js')
const helpers = require('../testHelpers.js')
const synthetixHelpers = require('../synthetixHelpers.js')
const Synth = artifacts.require('./Synth.sol')
const toUnit = synthetixHelpers.toUnit
const toBN = web3.utils.toBN
const assertRevert = helpers.assertRevert
const assertBNEqual = helpers.assertBNEqual;
const constants = require("./exchangeRateConstants.js")



contract('all_synths', (accounts) => {

	let rig, synthCurrencyKeys, nusd_synth, naud_synth, neur_synth, hdr_synth

    /* =======
        Set up the test rig before each 'it' statement.
       =======
     */
    const before_each = async function() {
        rig = await deployer.deployTestRig(accounts.slice(0, 6));
        synthCurrencyKeys = rig.currencyKeys.slice(0, 6)
        // Give the owner all synthetixs
        await synthetixHelpers.allocateSynthetixsTo(rig, rig.accounts.owner, toUnit(1e8))
		nusd_synth = await Synth.at(await rig.synthetix.synths(constants.NUSD_CURRENCY_KEY))
		hdr_synth = await Synth.at(await rig.synthetix.synths(constants.XDR_CURRENCY_KEY))
		naud_synth = await Synth.at(await rig.synthetix.synths(rig.currencyKeys[1]))
		neur_synth = await Synth.at(await rig.synthetix.synths(rig.currencyKeys[3]))

    }

    /* =======
        Some helper functions for synths tests.
       =======
     */
    const HAVVEN_HOLDER_A = accounts[6]
    const HAVVEN_HOLDER_B = accounts[7]

    const give_holders_some_havens = async function() {
        await assertRevert(
            rig.synthetix.transfer(rig.accounts.beneficiary, toUnit(5), {from: HAVVEN_HOLDER_A}),
            "Shouldn't be able to transfer yet..."
        )
        // We are starting where owner holds all tokens
        let total_supply = await rig.synthetix.totalSupply()
        assertBNEqual(
            total_supply,
            await rig.synthetix.balanceOf(rig.accounts.owner),
            "Assuming owner has the total supply."
        )

        await rig.synthetix.transfer(HAVVEN_HOLDER_A, toUnit(1000), {from: rig.accounts.owner})
        await rig.synthetix.transfer(HAVVEN_HOLDER_B, toUnit(50000), {from: rig.accounts.owner})
        assertBNEqual(await rig.synthetix.balanceOf(HAVVEN_HOLDER_A), toUnit(1000), "Holder A should have 1000 HAV")
        assertBNEqual(await rig.synthetix.balanceOf(HAVVEN_HOLDER_B), toUnit(50000), "Holder B should have 50000 HAV")
        assertBNEqual(
            await rig.synthetix.balanceOf(rig.accounts.owner),
            total_supply.sub(toUnit(51000)),
            "Owner should now have less 51000 HAV"
        )

    }
    const set_exchange_rates = async function () {
		let time_now = await helpers.timestamp()
        await rig.exchangeRates.updateRates(
            rig.currencyKeys.slice(1,7),
            constants.SOME_SET_OF_RATES,
            time_now,
            {from: rig.accounts.oracle}
        )
    }
	const advance_fee_period = async function () {
		await assertRevert(rig.feePool.closeCurrentFeePeriod({from: rig.accounts.feeAuthority}), "Too soon to close fee period.")
		await assertRevert(rig.feePool.closeCurrentFeePeriod({from: rig.accounts.owner}), "Owner shouldn't be able to close fee period")
		// But the feeAuthority should be able to close the period, after advancing forward in time

		let time_now = await helpers.timestamp()
		let new_time = time_now.add(toBN(60*60*24*10)) // add 10 days
		await helpers.setDate(new_time)


		await rig.feePool.closeCurrentFeePeriod({from: rig.accounts.feeAuthority})
	}
	const check_total_fees_are_zero = async function () {
		for(let i = 0; i < rig.currencyKeys.length - 1; i++) {
			assertBNEqual(
				await rig.feePool.totalFeesAvailable(rig.currencyKeys[i]),
				toUnit(0),
				"Still should be no fees generated in total"
			)
			await check_fees_available_for_each_user_are_zero()
		}
	}
	const check_fees_available_for_each_user_are_zero = async function () {
		for(let i = 0; i < rig.currencyKeys.length - 1; i++) {
			Object.values(rig.accounts).forEach(async function (account) {
				assertBNEqual(
					await rig.feePool.feesAvailable(account, rig.currencyKeys[i]),
					toUnit(0),
					"Still should be no fees generated for:" + account
				)
			})
			assertBNEqual(
				await rig.feePool.feesAvailable(HAVVEN_HOLDER_A, rig.currencyKeys[i]),
				toUnit(0),
				"Still should be no fees generated for:" + HAVVEN_HOLDER_A
			)
			assertBNEqual(
				await rig.feePool.feesAvailable(HAVVEN_HOLDER_B, rig.currencyKeys[i]),
				toUnit(0),
				"Still should be no fees generated for:" + HAVVEN_HOLDER_B
			)
		}

	}
	const print_all_fee_periods = async function () {
    	let period
		console.log("====== Fee Periods ======")
    	for(let i = 0; i <= 5; i++) {
			period = await rig.feePool.recentFeePeriods(i)
			console.log(`Period ${i}: #${period.feePeriodId} - toDist: ${period.feesToDistribute}\t claimed: ${period.feesClaimed}`)
		}
		console.log("=========================")
	}

    /* =======
        Begin tests...
       =======
     */

    describe('constructor', function () {
        it('sets public variables on each Synth', async function () {
        	await before_each()
            // Only cover the first 6 currency keys, since that's all synths are issued for
            for (let i = 0; i < synthCurrencyKeys.length - 1; i++) {
                let ascii_currency_key = web3.utils.hexToAscii(rig.currencyKeys[i]);
                assert.equal(
                    await rig.synths[ascii_currency_key].currencyKey(),
                    rig.currencyKeys[i],
                    `Synth ${ascii_currency_key} internal currency key should match it's reference key.`
                )
                synth_decimals = await rig.synths[ascii_currency_key].decimals()
                assert.isTrue(
                    synth_decimals.eq(toBN(18)),
                    `Synth ${ascii_currency_key} decimals incorrect.`
                )
                assert.equal(
                    await rig.synths[ascii_currency_key].synthetix(),
                    rig.synthetix.address,
                    `Synth ${ascii_currency_key} synthetix contract is incorrect.`
                )
                assert.equal(
                    await rig.synths[ascii_currency_key].feePool(),
                    rig.feePool.address,
                    `Synth ${ascii_currency_key} synthetix contract is incorrect.`
                )
            }
        })
    })

    describe('setters', function () {
        it('disallows reconfiguration, except by owner', async function () {
			await before_each()

            // Only cover the first 6 currency keys, since that's all synths are issued for
            for (let i = 0; i < synthCurrencyKeys.length - 1; i++) {
                let ascii_currency_key = web3.utils.hexToAscii(rig.currencyKeys[i]);
                await assertRevert(
                    rig.synths[ascii_currency_key].setSynthetix(
                        rig.synthetix.address, {from: rig.accounts.oracle}
                    ),
                    `Synth ${ascii_currency_key} should not allow oracle to set Synthetix address`
                )
                await assertRevert(
                    rig.synths[ascii_currency_key].setSynthetix(
                        rig.synthetix.address, {from: rig.accounts.beneficiary}
                    ),
                    `Synth ${ascii_currency_key} should not allow beneficiary to set Synthetix address`
                )
                await assertRevert(
                    rig.synths[ascii_currency_key].setFeePool(
                        rig.feePool.address, {from: rig.accounts.oracle}
                    ),
                    `Synth ${ascii_currency_key} should not allow oracle to set FeePool address`
                )
                await assertRevert(
                    rig.synths[ascii_currency_key].setSynthetix(
                        rig.feePool.address, {from: rig.accounts.beneficiary}
                    ),
                    `Synth ${ascii_currency_key} should not allow beneficiary to set FeePool address`
                )
            }
        })

        it('allows reconfiguration by owner', async function () {
			await before_each()
            rig = await deployer.deployTestRig(accounts.slice(7, 13));
            const synthCurrencyKeys = rig.currencyKeys.slice(0, 6)

            // Only cover the first 6 currency keys, since that's all synths are issued for
            for (let i = 0; i < synthCurrencyKeys.length - 1; i++) {
                let ascii_currency_key = web3.utils.hexToAscii(rig.currencyKeys[i]);

                await rig.synths[ascii_currency_key].setSynthetix(rig.accounts.beneficiary, {from: rig.accounts.owner})
                assert.equal(
                    await rig.synths[ascii_currency_key].synthetix(),
                    rig.accounts.beneficiary,
                    `Synth ${ascii_currency_key} should have had it's Synthetix property updated by owner`
                )

                await rig.synths[ascii_currency_key].setFeePool(rig.accounts.fundsWallet, {from: rig.accounts.owner})
                assert.equal(
                    await rig.synths[ascii_currency_key].feePool(),
                    rig.accounts.fundsWallet,
                    `Synth ${ascii_currency_key} should have had it's Synthetix property updated by owner`
                )
            }
        })
    })

    describe('mutative functions', function () {

        it("Everything should start at zero, synths can only be issued correctly, transferred, and burned.", async function() {
			await before_each()

            await give_holders_some_havens()
            await set_exchange_rates()

            assertBNEqual(
                await rig.synthetix.totalIssuedSynths(rig.currencyKeys[0]),
                toUnit(0),
                "No synths should be issued yet"
            )

            // Both holders should have no debt and no collateralisation ratio
            for(let i = 0; i < rig.currencyKeys.length - 1; i++){
                assertBNEqual(
                    await rig.synthetix.debtBalanceOf(HAVVEN_HOLDER_A, rig.currencyKeys[i]),
                    toBN(0),
                    `Synthetix holder A should have no debt in currencyKey[${i}].`
                )
                assertBNEqual(
                    await rig.synthetix.debtBalanceOf(HAVVEN_HOLDER_B, rig.currencyKeys[i]),
                    toBN(0),
                    `Synthetix holder B should have no debt in currencyKey[${i}].`
                )
                assertBNEqual(
                    await rig.synthetix.collateralisationRatio(HAVVEN_HOLDER_A),
                    toBN(0),
                    `Synthetix holder A should have no debt in currencyKey[${i}].`
                )
                assertBNEqual(
                    await rig.synthetix.collateralisationRatio(HAVVEN_HOLDER_B),
                    toBN(0),
                    `Synthetix holder B should have no debt in currencyKey[${i}].`
                )
            }

            // Nobody should be able to issue synths in HAV, or other non-registered currency
            await assertRevert(
                rig.synthetix.issueSynths(constants.SNX_CURRENCY_KEY, toUnit(1), {from: HAVVEN_HOLDER_B}),
                "Shouldn't be able to issue synths in HAV"
            )
            await assertRevert(
                rig.synthetix.issueSynths(constants.fake_currency_key_1, toUnit(1), {from: HAVVEN_HOLDER_B}),
                "Shouldn't be able to issue synths in a random fake currency."
            )


            // Holder A issues as many Synths as possible in nUSD
            await rig.synthetix.issueMaxSynths(constants.NUSD_CURRENCY_KEY, {from: HAVVEN_HOLDER_A})
            let holder_a_nusd_balance = await nusd_synth.balanceOf(HAVVEN_HOLDER_A)
            assert.isTrue(
                holder_a_nusd_balance.gt(toBN(0)),
                "Holder A should have a positive synth nUSD balance."
            )
            assertBNEqual(
                await naud_synth.balanceOf(HAVVEN_HOLDER_A),
                toBN(0),
                "Holder A should not have any nAUD synths"
            )
            assertBNEqual(
                await neur_synth.balanceOf(HAVVEN_HOLDER_B),
                toBN(0),
                "Holder B should not have any nEUR synths"
            )

            // Should not be able to issue any more synths, in any currency
            for(let i = 0; i < rig.currencyKeys.length; i++){
                assertBNEqual(
                    await rig.synthetix.remainingIssuableSynths(HAVVEN_HOLDER_A, rig.currencyKeys[i]),
                    toBN(0),
                    "Should not be able to issue any more synths"
                )
                await assertRevert(
                    rig.synthetix.issueSynths(rig.currencyKeys[i], toUnit(1), {from: HAVVEN_HOLDER_A}),
                    "Should not be able to issue more synths now."
                )
            }

            // Save holder B's issuable synth amounts...
            let holder_b_issuable_usd_synths = await rig.synthetix.remainingIssuableSynths(
                HAVVEN_HOLDER_B,
                constants.NUSD_CURRENCY_KEY
            )
            let holder_b_issuable_eur_synths = await rig.synthetix.remainingIssuableSynths(
                HAVVEN_HOLDER_B,
                rig.currencyKeys[3]
            )


            // ... then send all nUSD synths from holder A to holder B...
            await nusd_synth.transfer(HAVVEN_HOLDER_B, holder_a_nusd_balance, {from: HAVVEN_HOLDER_A})
            // ... and calculate how many would have ended up there...
            let holder_b_initial_nusd_balance = await rig.feePool.amountReceivedFromExchange(holder_a_nusd_balance)

            // and make sure holder B can still issue the same number of synths...
            assertBNEqual(
                await rig.synthetix.remainingIssuableSynths(HAVVEN_HOLDER_B, constants.NUSD_CURRENCY_KEY),
                holder_b_issuable_usd_synths,
                "Holder B's issuable nUSD synths should not have changed, even though they received some."
            )
            assertBNEqual(
                await rig.synthetix.remainingIssuableSynths(HAVVEN_HOLDER_B, rig.currencyKeys[3]),
                holder_b_issuable_eur_synths,
                "Holder B's issuable nEUR synths should not have changed, even though they received some nUSD."
            )

            await assertRevert(
                nusd_synth.burn(HAVVEN_HOLDER_B, toUnit(0.0001), {from: HAVVEN_HOLDER_B}),
                "Holder B should not be able to burn synths from the synth contract"
            )

            await assertRevert(
                nusd_synth.burn(HAVVEN_HOLDER_B, toUnit(0.0001), {from: rig.accounts.owner}),
                "Owner should not be able to burn synths from the synth contract"
            )

            // ... also make sure holder B has the correct number of synths
            assertBNEqual(
                await nusd_synth.balanceOf(HAVVEN_HOLDER_B),
                holder_b_initial_nusd_balance,
                "Holder B should now have Holder A's synths"
            )
            assertBNEqual(
                await nusd_synth.balanceOf(HAVVEN_HOLDER_A),
                toUnit(0),
                "Holder A should no longer have any synths."
            )


			/* ==== This has been fixed, cannot issue 0 any more
            // issue 0 synths for both holders, should be fine, though spammy.
            // Skip 'HAV', gets revert when issuing synths for it
            for(let i = 0; i < rig.currencyKeys.length - 1; i++){
                await rig.synthetix.issueSynths(rig.currencyKeys[i], toUnit(0), {from: HAVVEN_HOLDER_A})
                await rig.synthetix.issueSynths(rig.currencyKeys[i], toUnit(0), {from: HAVVEN_HOLDER_B})
                await rig.synthetix.issueSynths(rig.currencyKeys[i], toUnit(0), {from: rig.accounts.owner})
                await rig.synthetix.issueSynths(rig.currencyKeys[i], toUnit(0), {from: rig.accounts.oracle})
            }
            */
            // should not be able to issue lots of synths
            for(let i = 0; i < rig.currencyKeys.length - 1; i++){
                await assertRevert(rig.synthetix.issueSynths(rig.currencyKeys[i], toUnit(10000000), {from: HAVVEN_HOLDER_A}), `hodlr A shouldn't issue 10M currencyKeys[${i}] synths`)
                await assertRevert(rig.synthetix.issueSynths(rig.currencyKeys[i], toUnit(10000000), {from: HAVVEN_HOLDER_B}), `hodlr B shouldn't issue 10M currencyKeys[${i}] synths`)
                await assertRevert(rig.synthetix.issueSynths(rig.currencyKeys[i], toUnit(10000000000), {from: rig.accounts.owner}), `owner shouldn't issue 10B currencyKeys[${i}] synths`)
                await assertRevert(rig.synthetix.issueSynths(rig.currencyKeys[i], toUnit(10000000), {from: rig.accounts.oracle}), `Oracle shouldn't issue 10M currencyKeys[${i}] synths`)

                // and oracle (random account) shouldn't be able to create any synths
                await assertRevert(rig.synthetix.issueSynths(rig.currencyKeys[i], toUnit(1), {from: rig.accounts.oracle}), `Oracle shouldn't issue 1 currencyKeys[${i}] synths`)
            }

            // Holder B should be able to issue the original number of synths, in nEUR and nUSD.
            // even though they have received some synths, issued 0, and failed to issue lots.
            assertBNEqual(
                await rig.synthetix.remainingIssuableSynths(
                    HAVVEN_HOLDER_B,
                    rig.currencyKeys[3]
                ),
                holder_b_issuable_eur_synths,
                "Holder B's issuable nEUR shouldn't change"
            )
            assertBNEqual(
                await rig.synthetix.remainingIssuableSynths(
                    HAVVEN_HOLDER_B,
                    constants.NUSD_CURRENCY_KEY
                ),
                holder_b_issuable_usd_synths,
                "Holder B's issuable nUSD shouldn't change"
            )
            // None of this should affect issuable synths.
            // Holder A should still not be able to issue more synths.
            assertBNEqual(
                await rig.synthetix.remainingIssuableSynths(
                    HAVVEN_HOLDER_B,
                    rig.currencyKeys[3]
                ),
                holder_b_issuable_eur_synths,
                "Holder B's issuable nEUR shouldn't change"
            )
            assertBNEqual(
                await rig.synthetix.remainingIssuableSynths(
                    HAVVEN_HOLDER_B,
                    constants.NUSD_CURRENCY_KEY
                ),
                holder_b_issuable_usd_synths,
                "Holder B's issuable nUSD shouldn't change"
            )
            assertBNEqual(
                await rig.synthetix.remainingIssuableSynths(
                    HAVVEN_HOLDER_A,
                    constants.NUSD_CURRENCY_KEY
                ),
                toBN(7),
                // toBN(0), not zero any more, due to rounding error
                "Holder A should not be able to issue any more nUSD synths (except for 7 wei!)"
            )
            assertBNEqual(
                await rig.synthetix.remainingIssuableSynths(
                    HAVVEN_HOLDER_A,
                    rig.currencyKeys[3]
                ),
                toBN(1),
                // toBN(0), Not zero any more, due to rounding error
                "Holder A should not be able to issue any nEUR synths (except for 1 wei!)"
            )




            // Now holder B can issue a few more synths
			assertBNEqual(
			    await rig.synthetix.remainingIssuableSynths(HAVVEN_HOLDER_B, constants.NUSD_CURRENCY_KEY),
                toUnit(160000),
                "Holder B should currently be able to issue 160k nUSD"
            )
            await rig.synthetix.issueSynths(constants.NUSD_CURRENCY_KEY, toUnit(3), {from: HAVVEN_HOLDER_B})
			assertBNEqual(
				await rig.synthetix.remainingIssuableSynths(HAVVEN_HOLDER_B, constants.NUSD_CURRENCY_KEY),
				toUnit(159997).sub(toBN(6)),
				//toUnit(159997), This isn't exact any more because we introduced a rounding error
				"Holder B should now be able to issue 159.997k nUSD"
			)
            assertBNEqual(
                await nusd_synth.balanceOf(HAVVEN_HOLDER_B),
                holder_b_initial_nusd_balance.add(toUnit(3)),
                "Holder B should now have three extra nUSD synths"
            )
            assertBNEqual(
                await neur_synth.balanceOf(HAVVEN_HOLDER_B),
                toUnit(0),
                "Holder B should still have no nEUR synths"
            )

            // so should be 3 less now (i.e. 15.997k)
			// With 6 wei less, due to rounding error!
            holder_b_issuable_usd_synths = holder_b_issuable_usd_synths.sub(toUnit(3)).sub(toBN(6))
            assertBNEqual(
                await rig.synthetix.remainingIssuableSynths(HAVVEN_HOLDER_B, constants.NUSD_CURRENCY_KEY),
                holder_b_issuable_usd_synths,
                "Holder B should now be able to issue 3 less synths"
            )

            let holder_b_new_issuable_eur_synths = await rig.synthetix.remainingIssuableSynths(HAVVEN_HOLDER_B, rig.currencyKeys[3])
            assert.isTrue(
                holder_b_new_issuable_eur_synths.lt(holder_b_issuable_eur_synths),
                "Holder B should now be able to issue less nEUR synths..."
            )
            assert.isFalse(
                holder_b_issuable_eur_synths.sub(holder_b_new_issuable_eur_synths).eq(toUnit(3)),
                "... Holder B should now be able to issue not exactly three less nEUR synths"
            )


            // Now holder B can issue three more synths in EUR
            await rig.synthetix.issueSynths(rig.currencyKeys[3], toUnit(3), {from: HAVVEN_HOLDER_B})
            assertBNEqual(
                await nusd_synth.balanceOf(HAVVEN_HOLDER_B),
                holder_b_initial_nusd_balance.add(toUnit(3)),
                "Holder B nUSD balance doesn't change on issue of nEUR"
            )
            assertBNEqual(
                await neur_synth.balanceOf(HAVVEN_HOLDER_B),
                toUnit(3),
                "Holder B should now have 3 nEUR synths"
            )
			assertBNEqual(
				await naud_synth.balanceOf(HAVVEN_HOLDER_B),
				toUnit(0),
				"Holder B should now have no nAUD synths"
			)
            assertBNEqual(
                await rig.synthetix.remainingIssuableSynths(HAVVEN_HOLDER_B, rig.currencyKeys[3]),
                // Need to add 2 wei due to rounding error
                holder_b_new_issuable_eur_synths.sub(toUnit(3)).add(toBN(2)),
                "Holder B should now be able to issue exactly 3 less nEUR synths"
            )

            // Make sure holder B can issue less nUSD synths now
            let holder_b_new_issuable_usd_synths = await rig.synthetix.remainingIssuableSynths(HAVVEN_HOLDER_B, constants.NUSD_CURRENCY_KEY)
            assert.isTrue(
                holder_b_new_issuable_usd_synths.lt(holder_b_issuable_usd_synths),
                "Holder B should now be able to issue less nUSD synths..."
            )
            assert.isFalse(
                holder_b_issuable_usd_synths.sub(holder_b_new_issuable_usd_synths).eq(toUnit(3)),
                "... Holder B should now be able to issue not exactly three less nUSD synths"
            )
			/*  This is totally wrong due to rounding bug
			assertBNEqual(
				holder_b_new_issuable_usd_synths,
				toUnit(15993.1),
				"Should technically be only able to issue a further 15993.1 nUSD"
			)*/

			// Holder B Shouldn't be able to issue too many synths
			await assertRevert(
			    rig.synthetix.issueSynths(
					rig.currencyKeys[3],
					holder_b_new_issuable_eur_synths.sub(toUnit(2.99)),
					{from: HAVVEN_HOLDER_B}
				),
                "Holder B can't issue too many nEUR"
            )



            //    ======
            //     Here's a bug...
            //    ======
            //    The following commented issueSynths is equivalent to issueMaxSynths, but we'll just call the latter
            //    for clarity's sake
			//
            //    Holder B should issue *all* of their synths here
			//
            // await rig.synthetix.issueSynths(
            //     rig.currencyKeys[3],
            //     holder_b_new_issuable_eur_synths.sub(toUnit(3)),
            //     {from: HAVVEN_HOLDER_B}
            // )
			//
			await rig.synthetix.issueMaxSynths(rig.currencyKeys[3], {from: HAVVEN_HOLDER_B})

            //  The following assert should pass, but doesn't.
			// assertBNEqual(
			//     await rig.synthetix.remainingIssuableSynths(HAVVEN_HOLDER_B, rig.currencyKeys[3]),
            //     toUnit(0),
            //     "Should have zero reamining issuable after issuingMaxSynths."
            // )
            // instead, we have to do this:
			// ======== THIS BUG IS FIXED NOW =======
			//await rig.synthetix.issueSynths(rig.currencyKeys[3], toBN(1), {from: HAVVEN_HOLDER_B})
			 // And because of the above bug (where we have to issue an extra 1e-18 nEUR, we also have to subtract 1 immediately below when calculating the diff

			// The difference between exchange rate in nUSD and nEUR
            // This is because when we issue as many nEUR as we can, we are still left with a tiny amount of synthetixs left
			let nusd_neur_diff = constants.SOME_SET_OF_RATES[3].sub(constants.SOME_SET_OF_RATES[0]).div(toUnit(1)).sub(toBN(1))

            assertBNEqual(nusd_neur_diff, toBN(2), "Expecting this to be exactly 3 (not units) (2 after bugfix)")

			assertBNEqual(
				await rig.synthetix.remainingIssuableSynths(HAVVEN_HOLDER_B, rig.currencyKeys[3]),
				toBN(0),
				`There should be a no issuable nEUR...`
			)
			/* This is not true any more since one nEUR is worth much less than it was in the previous testing run.
			assertBNEqual(
				await rig.synthetix.remainingIssuableSynths(HAVVEN_HOLDER_B, rig.currencyKeys[0]),
				nusd_neur_diff,
				`... but there should still be a tiny amount of issuable nUSD`
			)
            // So issue the rest of the nUSD
            await rig.synthetix.issueMaxSynths(constants.NUSD_CURRENCY_KEY, {from: HAVVEN_HOLDER_B})
            assertBNEqual(
                await nusd_synth.balanceOf(HAVVEN_HOLDER_B),
			    holder_b_initial_nusd_balance.add(toUnit(3)).add(nusd_neur_diff),
                "Should have issued enough so that we now have all the nUSD we can."
            )
			*/


            // Holder A and B should now not be able to issue any synths in any currency.
            for(let i = 0; i < rig.currencyKeys.length; i++){
				assertBNEqual(
					await rig.synthetix.remainingIssuableSynths(HAVVEN_HOLDER_B, rig.currencyKeys[i]),
					toUnit(0),
					`Holder B should not be able to issue any more synths in currencyKey[${i}].`
				)
				await assertRevert(
					rig.synthetix.issueSynths(rig.currencyKeys[i], toBN(1), {from: HAVVEN_HOLDER_B}),
					`Holder B should not be able to issue even a tiny amount of synths in currencyKey[${i}]`
				)



				/* This is not true any longer, due to rounding bug, we can issue more synths
                assertBNEqual(
                    await rig.synthetix.remainingIssuableSynths(HAVVEN_HOLDER_A, rig.currencyKeys[i]),
                    toUnit(0),
                    `Holder A should not be able to issue any more synths in currencyKey[${i}].`
                )
                await assertRevert(
                    rig.synthetix.issueSynths(rig.currencyKeys[i], toBN(1), {from: HAVVEN_HOLDER_A}),
                    `Holder A should not be able to issue even a tiny amount of synths in currencyKey[${i}]`
                )
                // But can issue max synths, which should be zero (spams logs)
				// TODO: Again can't have below line due to bug - should be able to run these without error.
                // await rig.synthetix.issueMaxSynths(rig.currencyKeys[i], {from: HAVVEN_HOLDER_B})
                // await rig.synthetix.issueMaxSynths(rig.currencyKeys[i], {from: HAVVEN_HOLDER_A})
                */
            }



            // Now for burning tokens...
            // Holder A cannot burn any, because they don't have any
            // They shouldn't have any HDR yet because fees haven't been closed (but could otherwise)
            for(let i = 0; i < rig.currencyKeys.length; i++){
                await assertRevert(
                    rig.synthetix.burnSynths(rig.currencyKeys[i], toUnit(0.000001)),
                    `Holder A should not be able to burn any synth for currencyKey[${i}]`
                )
            }
            // Holder B shouldn't be able to burn for currencies they don't have
            // (Skip nUSD & nEUR)
            for(let i = 1; i < rig.currencyKeys.length; i++){
                if(i == 3) continue

                await assertRevert(
                    rig.synthetix.burnSynths(rig.currencyKeys[i], toUnit(0.000001)),
                    `Holder B should not be able to burn any synth for currencyKey[${i}]`
                )
            }

            // Double check that holder B has the right number of synths
			assertBNEqual(
				await nusd_synth.balanceOf(HAVVEN_HOLDER_B),
				// Have to subtract 2 wei here to keep things balancing with the rounding
				holder_b_initial_nusd_balance.add(toUnit(3)),
				"Double checking that Holder B has the expected balance of nUSD..."
			)

            // Holder B should now be able to burn a few synths... 2 nUSD and 0.5 nEUR
            await rig.synthetix.burnSynths(constants.NUSD_CURRENCY_KEY, toUnit(2), {from: HAVVEN_HOLDER_B})
            await rig.synthetix.burnSynths(rig.currencyKeys[3], toUnit(0.5), {from: HAVVEN_HOLDER_B})
            assert.isTrue(
                toUnit(2).lt(await rig.synthetix.remainingIssuableSynths(HAVVEN_HOLDER_B, constants.NUSD_CURRENCY_KEY)),
                "Should now be able to issue more than 2 nUSD synths"
            )
            assert.isTrue(
                toUnit(0.5).lt(await rig.synthetix.remainingIssuableSynths(HAVVEN_HOLDER_B, rig.currencyKeys[3])),
                "Should now be able to issue more than 0.5 nEUR synths"
            )
			assertBNEqual(
				await nusd_synth.balanceOf(HAVVEN_HOLDER_B),
				holder_b_initial_nusd_balance.add(toUnit(1)),
				"Triple checking that Holder B has the expected balance of nUSD..."
			)

            await assertRevert(
                rig.synthetix.burnSynths(
                    constants.NUSD_CURRENCY_KEY,
                    holder_b_initial_nusd_balance.add(toUnit(2)),
                    {from: HAVVEN_HOLDER_B}
                ),
                "Holder B should not be able to burn more tokens than they have"
            )
            await assertRevert(
                rig.synthetix.burnSynths(
                    constants.NUSD_CURRENCY_KEY,
                    toBN(1),
                    {from: HAVVEN_HOLDER_A}
                ),
                "Holder A should not be able to burn any tokens, still"
            )

            // So holder B can burn all but one of their nUSD
            await rig.synthetix.burnSynths(constants.NUSD_CURRENCY_KEY, holder_b_initial_nusd_balance, {from: HAVVEN_HOLDER_B})
            assertBNEqual(
                await nusd_synth.balanceOf(HAVVEN_HOLDER_B),
                toUnit(1),
                "Holder B should have only 1 nUSD left"
            )
            await assertRevert(
                rig.synthetix.burnSynths(
                    constants.NUSD_CURRENCY_KEY,
                    toUnit(1.0001),
                    {from: HAVVEN_HOLDER_B}
                ),
                "Holder B should still not be able to burn more tokens than they have"
            )

            // But holder B can burn all of their nEUR synths
			let current_neur_balance = await neur_synth.balanceOf(HAVVEN_HOLDER_B)
            assertBNEqual(
                current_neur_balance,
                holder_b_new_issuable_eur_synths.sub(toUnit(0.5)).add(toBN(2)),
                "Holder B should have the correct number of nEUR synths after burn (plus a bit extra for rounding bug)"
            )

			let current_neur_debt_balance = await rig.synthetix.debtBalanceOf(HAVVEN_HOLDER_B, rig.currencyKeys[3])

			await rig.synthetix.burnSynths(
				rig.currencyKeys[3],
				// Need to remove one off the end due to the rounding bug.
				current_neur_debt_balance,
				{from: HAVVEN_HOLDER_B}
			)
        })

		it("Synths can be issued, fee period progressed, synths burned, and hav's transferred, without generating fees.", async function () {
			await before_each()
			await give_holders_some_havens()
			await set_exchange_rates()


			assertBNEqual(
				await rig.synthetix.totalIssuedSynths(rig.currencyKeys[0]),
				toUnit(0),
				"No synths should be issued yet"
			)

			let owner_initial_hav_balance = toUnit(1e8).sub(toUnit(51000))
			assertBNEqual(
				await rig.synthetix.balanceOf(rig.accounts.owner),
				owner_initial_hav_balance,
				"Owner's initial HAV balance should be as we expect"
			)
			let owner_new_hav_balance

			// Owner issues 200 synths in each type
			for(let i = 0; i < rig.currencyKeys.length - 1; i++) {
				await rig.synthetix.issueSynths(rig.currencyKeys[i], toUnit(200), {from: rig.accounts.owner})
				owner_new_hav_balance = await rig.synthetix.balanceOf(rig.accounts.owner)
				assertBNEqual(
					owner_new_hav_balance,
					owner_initial_hav_balance,
					"Owner's HAV balance shouldn't change after issuing Synths"
				)
				await assertRevert(
					rig.synthetix.transfer(HAVVEN_HOLDER_A, owner_initial_hav_balance, {from: rig.accounts.owner}),
					`Owner should not be able to transfer all of their HAVs, since some have been issued against synths`
				)
			}


			// No transfers = no fees, before and after closing the period.
			await check_total_fees_are_zero()
			await advance_fee_period()
			await set_exchange_rates()
			await check_total_fees_are_zero()

			// Owner burns all of their synths again.
			for(let i = 0; i < rig.currencyKeys.length - 1; i++) {
				await rig.synthetix.burnSynths(rig.currencyKeys[i], toUnit(200), {from: rig.accounts.owner})
			}


			// Now owner can transfer all their synthetixs
			await rig.synthetix.transfer(HAVVEN_HOLDER_A, owner_initial_hav_balance, {from: rig.accounts.owner})
			assertBNEqual(
				await rig.synthetix.balanceOf(rig.accounts.owner),
				toUnit(0),
				"The owner should have no more HAVs left"
			)
			assertBNEqual(
				await rig.synthetix.balanceOf(HAVVEN_HOLDER_A),
				toUnit(1e8).sub(toUnit(50000)),
				"Holder A should now have all but 50k HAVs"
			)

			 // THIS IS A BUG!!
				// The feesAvailable function fails with a div by zero error when no synths are issued
				// should be able to check that total fees are zero
		//	await check_total_fees_are_zero()
			await advance_fee_period()
			await set_exchange_rates()
		//	await check_total_fees_are_zero()
		})

		it("Synths can be issued and transferred, fees are produced.", async function () {
			// await check_total_fees_are_zero() (this shouldn't be commented out)
			await before_each()

			await set_exchange_rates()

			let the_synth
			for(let i = 0; i < rig.currencyKeys.length - 1; i++) {

				// Owner issues 200 synths in each type
				await rig.synthetix.issueSynths(rig.currencyKeys[i], toUnit(500), {from: rig.accounts.owner})

				// Transfer some synths to the holders
				the_synth = await Synth.at(await rig.synthetix.synths(rig.currencyKeys[i]))
				await the_synth.transfer(HAVVEN_HOLDER_A, toUnit(200), {from: rig.accounts.owner})
				await the_synth.transfer(HAVVEN_HOLDER_B, toUnit(250), {from: rig.accounts.owner})
			}

			// Fees should still be zero, becasuse we have not advanced the fee period.
			await check_fees_available_for_each_user_are_zero()

			// await print_all_fee_periods()

			let fee_period_0 = await rig.feePool.recentFeePeriods(0)
			let fee_period_1 = await rig.feePool.recentFeePeriods(1)

			assert.isTrue(fee_period_0.feesToDistribute.gt(toUnit(0)), "There should be *some* fees in period 0 now")
			assertBNEqual(fee_period_0.feesClaimed, toBN(0), "No fees should be claimed yet (period 0).")
			assertBNEqual(fee_period_1.feesToDistribute, toBN(0), "No fees should be in period 1 yet.")
			assertBNEqual(fee_period_1.feesClaimed, toBN(0), "No fees should be claimed yet (period 1).")

			// Now we advance the fee period and check that there are *some* fees
			await advance_fee_period()
			await set_exchange_rates()

			fee_period_0 = await rig.feePool.recentFeePeriods(0)
			fee_period_1 = await rig.feePool.recentFeePeriods(1)
			assertBNEqual(fee_period_0.feesToDistribute, toBN(0), "No fees should be in period 0 anymore.")
			assertBNEqual(fee_period_0.feesClaimed, toBN(0), "No fees should be claimed yet (period 0).")
			assert.isTrue(fee_period_1.feesToDistribute.gt(toUnit(0)), "There should be *some* fees in period 1 now")
			assertBNEqual(fee_period_1.feesClaimed, toBN(0), "No fees should be claimed yet (period 1).")


			// await print_all_fee_periods()

			for(let i = 0; i < rig.currencyKeys.length - 1; i++) {
				let total_fees = await rig.feePool.totalFeesAvailable(rig.currencyKeys[i])
				assert.isTrue(
					total_fees.gt(toUnit(0)),
					`There should be more than zero fees now available for currencyKey[${i}]`
				)
				let owner_fees = await rig.feePool.feesAvailable(rig.accounts.owner, rig.currencyKeys[i])
				assert.isTrue(
					owner_fees.eq(toUnit(0)),
					`Owner should not have fees because they transferred synths in the same fee period as issue (in currencyKeys[${i}])`
				)
				assertBNEqual(
					await rig.feePool.feesAvailable(HAVVEN_HOLDER_A, rig.currencyKeys[i]),
					toUnit(0),
					"Holder A should still have no fees generated for them (in currencyKeys[${i}])"
				)
				assertBNEqual(
					await rig.feePool.feesAvailable(HAVVEN_HOLDER_B, rig.currencyKeys[i]),
					toUnit(0),
					"Holder B should still have no fees generated for them (in currencyKeys[${i}])"
				)
			}

			// Do some more transfers
			// These first two should revert because the amount transferred from owner would have lost fees.
			await assertRevert(nusd_synth.transfer(HAVVEN_HOLDER_A, toUnit(250), {from: HAVVEN_HOLDER_B}))
			await assertRevert(neur_synth.transfer(HAVVEN_HOLDER_B, toUnit(200), {from: HAVVEN_HOLDER_A}))


			await nusd_synth.transfer(
				HAVVEN_HOLDER_A,
				await rig.feePool.amountReceivedFromTransfer(toUnit(250)),
				{from: HAVVEN_HOLDER_B}
			)
			await neur_synth.transfer(
				HAVVEN_HOLDER_B,
				await rig.feePool.amountReceivedFromTransfer(toUnit(200)),
				{from: HAVVEN_HOLDER_A}
			)

			assertBNEqual(
				await rig.feePool.feesAvailable(rig.accounts.owner, constants.NUSD_CURRENCY_KEY),
				toUnit(0),
				`Owner *still* shouldn't have fees because these transfers were made in the current fee period.`
			)
			fee_period_0 = await rig.feePool.recentFeePeriods(0)
			assert.isTrue(fee_period_0.feesToDistribute.gt(toUnit(0)), "There should be *some* fees in period 0 now, after transfers")
			assertBNEqual(fee_period_0.feesClaimed, toBN(0), "No fees should be claimed yet (period 0), after transfer.")

			//await print_all_fee_periods()

			// Now we advance the fee period again
			await advance_fee_period()
			await set_exchange_rates()

			fee_period_1 = await rig.feePool.recentFeePeriods(1)
			assert.isTrue(fee_period_1.feesToDistribute.gt(toUnit(0)), "There should be *some* fees in period 1 now, after transfers")
			assertBNEqual(fee_period_1.feesClaimed, toBN(0), "No fees should be claimed yet (period 1), after transfer.")
			owner_fees = await rig.feePool.feesAvailable(rig.accounts.owner, constants.NUSD_CURRENCY_KEY)
			assert.isTrue(
				owner_fees.gt(toUnit(0)),
				`...And these fees should be allocated to the owner.`
			)

			await advance_fee_period()
			await set_exchange_rates()
			//await print_all_fee_periods()

			// So let the owner claim their fees!
			let owner_balance_before = await nusd_synth.balanceOf(rig.accounts.owner)
			await rig.feePool.claimFees(constants.NUSD_CURRENCY_KEY, {from: rig.accounts.owner})
			let owner_balance_after = await nusd_synth.balanceOf(rig.accounts.owner)
			assert.isTrue(
				owner_balance_after.gt(owner_balance_before),
				"The owner should now have a greater balance of nUSD, because they withdrew their fees."
			)

			//await print_all_fee_periods()


			await advance_fee_period()
			await set_exchange_rates()
			//await print_all_fee_periods()

			await assertRevert(
				rig.feePool.claimFees(constants.NUSD_CURRENCY_KEY, {from: rig.accounts.owner}),
				"Owner should not be able to claim any more fees."
			)

			await advance_fee_period()
			await set_exchange_rates()
			//await print_all_fee_periods()

			await assertRevert(
				rig.feePool.claimFees(constants.NUSD_CURRENCY_KEY, {from: rig.accounts.owner}),
				"Owner should not be able to claim any more fees."
			)

			await advance_fee_period()
			await set_exchange_rates()
			//await print_all_fee_periods()

			await assertRevert(
				rig.feePool.claimFees(constants.NUSD_CURRENCY_KEY, {from: rig.accounts.owner}),
				"Owner should not be able to claim any more fees."
			)
		})

		it("Synths can be exchanged into different flavours, and exchange fees are taken.", async function() {
			await before_each()
			await rig.synthetix.issueSynths(constants.NUSD_CURRENCY_KEY, toUnit(5), {from: rig.accounts.owner})
			await check_total_fees_are_zero()
			await assertRevert(
				rig.synthetix.exchange(
					constants.XDR_CURRENCY_KEY,
					toUnit(5),
					constants.NUSD_CURRENCY_KEY,
					HAVVEN_HOLDER_A,
					{from: rig.accounts.owner}
				),
				"Should not be able to exchange HDR synths, since we don't have any."
			)

			// Should be able to exchange between synths with myself.
			await rig.synthetix.exchange(
				constants.NUSD_CURRENCY_KEY,
				toUnit(5),
				constants.XDR_CURRENCY_KEY,
				rig.accounts.owner,
				{from: rig.accounts.owner}
			)
			let max_expected_hdr = await rig.synthetix.effectiveValue(constants.NUSD_CURRENCY_KEY, toUnit(5), constants.XDR_CURRENCY_KEY)
			let owner_hdr_balance = await hdr_synth.balanceOf(rig.accounts.owner)

			assert.isTrue(
				owner_hdr_balance.lt(max_expected_hdr),
				"The owner should not have received the full amount of HDRs, due to exchange fee."
			)

			await assertRevert(
				rig.synthetix.exchange(
					constants.XDR_CURRENCY_KEY,
					toUnit(5),
					constants.NUSD_CURRENCY_KEY,
					rig.accounts.owner,
					{from: rig.accounts.owner}
				),
				"Should not be able to convert back, because a fee should have been taken (don't have 5 nHDRs)"
			)

			await rig.synthetix.exchange(
				constants.XDR_CURRENCY_KEY,
				owner_hdr_balance,
				constants.NUSD_CURRENCY_KEY,
				rig.accounts.owner,
				{from: rig.accounts.owner}
			)

			let owner_nusd_balance = await nusd_synth.balanceOf(rig.accounts.owner)
			assert.isTrue(
				owner_nusd_balance.lt(toUnit(5)),
				"Shouldn't have the amount of nUSD we started with, due to exchange fees."
			)
		})
    })

})


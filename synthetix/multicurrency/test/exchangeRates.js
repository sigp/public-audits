const deployer = require('../deployer.js');
const BigNumber = require('bignumber.js')
const helpers = require('../testHelpers.js')
const synthetixHelpers = require('../synthetixHelpers.js')
const toUnit = synthetixHelpers.toUnit;
const assertRevert = helpers.assertRevert;
const toBN = web3.utils.toBN
const constants = require("./exchangeRateConstants.js")



contract('exchangerates', (accounts) => {

    describe('constructor', function () {

        it('sets public variables', async function () {
            rig = await deployer.deployTestRig(accounts.slice(7, 13));

            assert(await rig.exchangeRates.oracle() === rig.accounts.oracle, "Incorrect oracle");

            let stale_period = await rig.exchangeRates.rateStalePeriod();
            assert(new BigNumber(stale_period).eq(constants.DEFAULT_STALE_RATE_PERIOD), "Incorrect rateStalePeriod");

            assert.equal(rig.currencyKeys.length, 7, "There should be 7 currency keys (in our rig)");

            // There are only 5 xdrParticipants
            for (let i = 0; i < 5; i++) {
                let xdr_participant = await rig.exchangeRates.xdrParticipants(i);
                assert.equal(rig.currencyKeys[i], xdr_participant, `xdrParticipant[${i}] should be: ${rig.currencyKeys[i]}`);
            }
            rig.exchangeRates.xdrParticipants(5)
                .then(function (val) {
                    assert(false, "Should not have found a 5th xdrParticipant");
                }).catch(function (error) {
                assert.include(error.message, "invalid opcode", "Expected to get an 'invalid opcode' error");
            })

        })
        it('initial updateRates are correct', async function () {
            let deploy_grace_period = 2; //seconds
            rig = await deployer.deployTestRig(accounts.slice(0, 6));
            let deploy_timestamp = await helpers.timestamp()

            /* =======
             * Exchange rates should start at 1 (except XDR), update times should be 'now' according to deployment.
             * =======
             */
            for (let i = 0; i < rig.currencyKeys.length; i++) {
                let currency_rate = await rig.exchangeRates.rates(rig.currencyKeys[i]);
                if (rig.currencyKeys[i] == constants.XDR_CURRENCY_KEY) {
                    // "XDR" is a special case, because it gets recalculated.
                    assert(
                        new BigNumber(currency_rate).eq(toUnit(5)),
                        `Exchange rates for XDR should start at 5 (sum of 1, 5 times)`
                    );
                } else {
                    assert(
                        new BigNumber(currency_rate).eq(toUnit(1)),
                        `Exchange rates for currencyKeys[${i}] ${web3.utils.hexToAscii(rig.currencyKeys[i])} should start at 1`
                    );
                }
                let currency_update = await rig.exchangeRates.lastRateUpdateTimes(rig.currencyKeys[i]);
                assert(
                    new BigNumber(currency_update).sub(deploy_timestamp).lte(deploy_grace_period),
                    `Update time for currencyKeys[${i}] should be (within ${deploy_grace_period} seconds of) 'now'.`
                );
            }
        })
    })

    describe('functions', function () {

        it('Testing [updateRates]', async function () {
			rig = await deployer.deployTestRig(accounts.slice(0, 6));
			let deploy_timestamp = await helpers.timestamp()

			let first_rate_updated_timestamp = await rig.exchangeRates.lastRateUpdateTimes(rig.currencyKeys[0])

			/* =======
			 * Make sure oracle can update the rates individually
			 * =======
			 */
			for (let i = 1; i < rig.currencyKeys.length; i++) {
				await rig.exchangeRates.updateRates(
					[rig.currencyKeys[i]],
					[toUnit(i + 2.4)],
					deploy_timestamp.add(toBN(1)),
					{from: rig.accounts.oracle}
				);
				let new_currency_rate = await rig.exchangeRates.rates(rig.currencyKeys[i]);
				if (rig.currencyKeys[i] === constants.XDR_CURRENCY_KEY) {
					assert(
						new BigNumber(new_currency_rate).eq(toUnit(20.6)),
						"Exchange rate for XDR" +
						` should be updated (individually), but it's still ${new_currency_rate}.`
					);

				} else {
					assert(
						new BigNumber(new_currency_rate).eq(toUnit(i + 2.4)),
						`Exchange rate for rig.currencyKeys[${i}] should be updated (individually), but it's still ${new_currency_rate}.`
					);
				}
			}

			/* =======
			 * Make sure oracle can update all the rates at once.
			 * =======
			 */
			await rig.exchangeRates.updateRates(
				rig.currencyKeys.slice(1, 7),
				constants.SOME_SET_OF_RATES,
				deploy_timestamp.add(toBN(2)),
				{from: rig.accounts.oracle}
			);
			for (let i = 1; i < rig.currencyKeys.length; i++) {
				let new_currency_rate = await rig.exchangeRates.rates(rig.currencyKeys[i]);
				if (rig.currencyKeys[i] === constants.XDR_CURRENCY_KEY) {
					assert.isTrue(
						new BigNumber(new_currency_rate).eq(constants.TOTAL_SUM_OF_XDR_RATES),
						"Exchange rate for XDR should be updated (from array)."
					);
				} else {
					assert.isTrue(
						new BigNumber(new_currency_rate).eq(toUnit(i + 10)),
						"Exchange rate should be updated (from array)."
					);
				}
			}
			let xdr_currency_rate = await rig.exchangeRates.rates(constants.XDR_CURRENCY_KEY)
			assert.isTrue(
				new BigNumber(xdr_currency_rate).eq(constants.TOTAL_SUM_OF_XDR_RATES)
			)

			/* =======
			 * Make sure nobody else can update the rates
			 * =======
			 */
			await assertRevert(
				rig.exchangeRates.updateRates(
					rig.currencyKeys.slice(1, 7),
					constants.SOME_SET_OF_RATES,
					deploy_timestamp.add(toBN(3)),
					{from: rig.accounts.owner}
				),
				"Exchange rate should not be updatable by owner."
			);
			await assertRevert(
				rig.exchangeRates.updateRates(
					rig.currencyKeys.slice(1, 7),
					constants.SOME_SET_OF_RATES,
					deploy_timestamp.add(toBN(4)),
					{from: rig.accounts.beneficiary}
				),
				"Exchange rate should not be updatable by beneficiary."
			);
			await assertRevert(
				rig.exchangeRates.updateRates(
					rig.currencyKeys.slice(1, 7),
					constants.SOME_SET_OF_RATES,
					deploy_timestamp.add(toBN(5)),
					{from: rig.accounts.fundsWallet}
				),
				"Exchange rate should not be updatable by fundsWallet."
			);

			/* =======
			 * Make sure it reverts if we have inconsistent length limits
			 * =======
			 */
			await assertRevert(
				rig.exchangeRates.updateRates(
					[rig.currencyKeys[1]],
					[toUnit(7), toUnit(8)],
					deploy_timestamp.add(toBN(6)),
					{from: rig.accounts.oracle}
				),
				"When array lengths are different, it should revert."
			);
			await assertRevert(
				rig.exchangeRates.updateRates(
					[rig.currencyKeys[1], rig.currencyKeys[0]],
					[toUnit(7)],
					deploy_timestamp.add(toBN(7)),
					{from: rig.accounts.oracle}
				),
				"When array lengths are different, it should revert."
			);

			/* =======
			 * Make sure we can't update the rates too far in the future.
			 * =======
			 */

			await assertRevert(
				rig.exchangeRates.updateRates(
					[rig.currencyKeys[1]],
					[toUnit(7)],
					deploy_timestamp.mul(toBN(2)),
					{from: rig.accounts.oracle}
				),
				"Should not be able to update the exchange rate very far into the future."
			);

			await assertRevert(
				rig.exchangeRates.updateRates(
					[rig.currencyKeys[1]],
					[toUnit(7)],
					deploy_timestamp.add(toBN(constants.ORACLE_FUTURE_LIMIT + 2)),
					{from: rig.accounts.oracle}
				),
				"Should not be able to update the exchange rate slightly too far into the future."
			);

			await rig.exchangeRates.updateRates(
				[rig.currencyKeys[3]],
				[toUnit(8.8)],
				deploy_timestamp.add(toBN(3)),
				{from: rig.accounts.oracle}
			);
			new_currency_rate = await rig.exchangeRates.rates(rig.currencyKeys[3]);
			assert(
				new BigNumber(new_currency_rate).eq(toUnit(8.8)),
				"Should be able to update the rate for the current time (nEUR)."
			);

			await rig.exchangeRates.updateRates(
				[rig.currencyKeys[2]],
				[toUnit(7.7)],
				deploy_timestamp.add(toBN(constants.ORACLE_FUTURE_LIMIT - 1)),
				{from: rig.accounts.oracle}
			);
			new_currency_rate = await rig.exchangeRates.rates(rig.currencyKeys[2]);
			assert(
				new BigNumber(new_currency_rate).eq(toUnit(7.7)),
				"Should be able to update the rate in the future, within the limit."
			);

			await rig.exchangeRates.updateRates(
				[rig.currencyKeys[3]],
				[toUnit(88)],
				deploy_timestamp.add(toBN(3)),
				{from: rig.accounts.oracle}
			);
			new_currency_rate = await rig.exchangeRates.rates(rig.currencyKeys[3]);
			assert(
				new BigNumber(new_currency_rate).eq(toUnit(88)),
				"Should be able to update the rate for the current time (XDR)."
			);

			/* =======
			 * Are we correctly updating the lastRateUpdateTimes?
			 * =======
			 */
			// This is calculated by looking at the above tests.
			let expected_currency_update_times = [
				first_rate_updated_timestamp,
				deploy_timestamp.add(toBN(2)),
				deploy_timestamp.add(toBN(constants.ORACLE_FUTURE_LIMIT - 1)),
				deploy_timestamp.add(toBN(3)),
				deploy_timestamp.add(toBN(2)),
				// TODO: XDR is just the most recently updated rate time - i.e. it's the only one that can go backwards
				deploy_timestamp.add(toBN(3)),
				deploy_timestamp.add(toBN(2))
			]
			for (let i = 0; i < rig.currencyKeys.length; i++) {
				let currency_update_time = await rig.exchangeRates.lastRateUpdateTimes(rig.currencyKeys[i]);
				assert(
					new BigNumber(currency_update_time).eq(expected_currency_update_times[i])
					,
					`lastRateUpdateTimes[${i}] is not as expected. expected: ${expected_currency_update_times[i]}, got: ${currency_update_time}`
				);
			}

			// Need to mine some blocks so that we have some more future limit...

			await helpers.increaseTime(120)

			/* =======
			 * Test that we can't update rates to zero
			 * =======
			 */

			for (let i = 0; i < rig.currencyKeys.length; i++) {
				await assertRevert(
					rig.exchangeRates.updateRates([rig.currencyKeys[i]], [0], deploy_timestamp.add(toBN(constants.ORACLE_FUTURE_LIMIT))),
					`Should not be able to update rate ${i} to 0`
				)
			}
			await assertRevert(
				rig.exchangeRates.updateRates(rig.currencyKeys, [0, 0, 0, 0, 0], 10),
				`Should not be able to update any rates to 0`
			)
			await assertRevert(
				rig.exchangeRates.updateRates(
					rig.currencyKeys.slice(1, 7),
					[toUnit(0), toUnit(0), toUnit(0), toUnit(0), toUnit(0)],
					deploy_timestamp.add(toBN(constants.ORACLE_FUTURE_LIMIT + 1))),
				`Should not be able to update any rates to 0 (round 2)`
			)

			await helpers.increaseTime(constants.DEFAULT_STALE_RATE_PERIOD + 120)
			// Should now be stale



			await assertRevert(
				rig.synthetix.effectiveValue(rig.currencyKeys[1], 100, rig.currencyKeys[0]),
				"Should not be able calculate any effectiveValue when it's stale"
			)

        });


        it('Testing [isRateStale], [anyRateIsStale], [setRateStalePeriod], and [effectiveValue]', async function () {

            rig = await deployer.deployTestRig(accounts.slice(0, 6));
            let deploy_timestamp = await helpers.timestamp()

            /* =======
             * All rates should start out as not stale.
             * =======
             */

            for (let i = 0; i < rig.currencyKeys.length; i++) {
                assert.isFalse(
                    await rig.exchangeRates.rateIsStale(rig.currencyKeys[i]),
                    `The rate for currencyKey[${i}] should not be stale.`);
                assert.isFalse(await rig.exchangeRates.anyRateIsStale(rig.currencyKeys.slice(0, i + 1)),
                    `The rates for any currencyKey[] should not be stale.`);
                assert.isFalse(await rig.exchangeRates.anyRateIsStale(rig.currencyKeys.slice(i, rig.currencyKeys.length)),
                    `The rates for any currencyKey[] should not be stale.`);
            }
            // Try some edge cases with fake currencies
            assert.isFalse(await rig.exchangeRates.anyRateIsStale([]),
                "The rate for an empty array should return false.");
            assert(await rig.exchangeRates.anyRateIsStale([constants.fake_currency_key_1]),
                "The rate for an unknown currency 1 (in array) should be stale");
            assert(await rig.exchangeRates.anyRateIsStale([constants.fake_currency_key_2]),
                "The rate for an unknown currency 2 (in array) should be stale");
///			assert(await rig.exchangeRates.anyRateIsStale([constants.fake_currency_key_3]),
//              "The rate for an unknown currency 3 (in array) should be stale");
            assert(await rig.exchangeRates.anyRateIsStale([rig.currencyKeys[1], constants.fake_currency_key_1]),
                "The rate for an unknown currency 1 admidst array should be stale");
            assert(await rig.exchangeRates.rateIsStale(constants.fake_currency_key_1),
                "The rate for an unknown currency 1 should be stale");
            assert(await rig.exchangeRates.rateIsStale(constants.fake_currency_key_2),
                "The rate for an unknown currency 2 should be stale");
///			assert(await rig.exchangeRates.rateIsStale(constants.fake_currency_key_3),
//              "The rate for an unknown currency 3 should be stale");

            //Check that sUSD is not yet stale
            assert.isFalse(await rig.exchangeRates.rateIsStale(constants.NUSD_CURRENCY_KEY),
                "The rate for sUSD should always be false.")
            assert.isFalse(await rig.exchangeRates.anyRateIsStale([constants.NUSD_CURRENCY_KEY]),
                "The rate for sUSD should always be false.")
            assert.isFalse(await rig.exchangeRates.anyRateIsStale([constants.NUSD_CURRENCY_KEY, constants.NUSD_CURRENCY_KEY, rig.currencyKeys[0], rig.currencyKeys[2]]),
                "The rate for sUSD and others should always be false (even if repeated).")
            assert(await rig.exchangeRates.anyRateIsStale([constants.NUSD_CURRENCY_KEY, constants.fake_currency_key_1]),
                "The rate for a fake currency 1 should be stale, even if sUSD is there.")
            assert(await rig.exchangeRates.anyRateIsStale([constants.NUSD_CURRENCY_KEY, constants.fake_currency_key_2]),
                "The rate for a fake currency 2 should be stale, even if sUSD is there.")
///			assert(await rig.exchangeRates.anyRateIsStale([constants.NUSD_CURRENCY_KEY, constants.fake_currency_key_3]),
//              "The rate for a fake currency 3 should be stale, even if sUSD is there.")
            assert(await rig.exchangeRates.anyRateIsStale([constants.fake_currency_key_1, constants.NUSD_CURRENCY_KEY]),
                "The rate for a fake currency 1 should be stale, even if sUSD is there (reversed).")
///			assert(await rig.exchangeRates.anyRateIsStale([constants.fake_currency_key_3, constants.NUSD_CURRENCY_KEY]),
//              "The rate for a fake currency 3 should be stale, even if sUSD is there (reversed).")

            // Check that we can't send it nonsense
            await rig.exchangeRates.rateIsStale(1234).then(assert.fail).catch(function (error) {
                assert.include(error.message, "invalid bytes4", "Should error if we are sending an int to rateIsStale.");
            });
            await rig.exchangeRates.rateIsStale([constants.NUSD_CURRENCY_KEY]).then(assert.fail).catch(function (error) {
                assert.include(error.message, "invalid bytes4", "Should error if we are sending an array to rateIsStale.");
            });
            await rig.exchangeRates.anyRateIsStale(constants.NUSD_CURRENCY_KEY).then(assert.fail).catch(function (error) {
                assert.include(error.message, "expected array value", "Should error if we are sending bytes to anyRateIsStale");
            });
            await rig.exchangeRates.anyRateIsStale(1234).then(assert.fail).catch(function (error) {
                assert.include(error.message, "expected array value", "Should error if we are sending an int to anyRateIsStale")
            });

            /* =======
             * Now all rates (except sUSD) should be stale
             * =======
             */

            await helpers.increaseTime(constants.DEFAULT_STALE_RATE_PERIOD + 1)
            assert.isFalse(
                await rig.exchangeRates.rateIsStale(rig.currencyKeys[0]),
                "Exchange rate of sUSD should never be stale."
            );
            for (let i = 1; i < rig.currencyKeys.length; i++) {
                assert(
                    await rig.exchangeRates.rateIsStale(rig.currencyKeys[i]),
                    `Exchange rate ${i} should now be very stale.`
                );
            }
            for (let i = 0; i < rig.currencyKeys.length; i++) {
                if (i > 0) {
                    assert(
                        await rig.exchangeRates.anyRateIsStale(rig.currencyKeys.slice(0, i + 1)),
                        `Exchange rate ${i} should now be very stale (in array slice 1)`
                    );
                }
                assert(
                    await rig.exchangeRates.anyRateIsStale(rig.currencyKeys.slice(i, rig.currencyKeys.length)),
                    `Exchange rate ${i} should now be very stale (in array slice 2)`
                );
            }

			let xdr_currency_rate = await rig.exchangeRates.rates(constants.XDR_CURRENCY_KEY)
			assert.isTrue(
				new BigNumber(xdr_currency_rate).eq(toUnit(5)),
				`Incorrect XDR rate, expected: ${toUnit(5)}, actual: ${xdr_currency_rate}`
			)

            // Set all rates as slightly stale...
            await rig.exchangeRates.updateRates(
                rig.currencyKeys.slice(1,7),
                constants.SOME_SET_OF_RATES,
                deploy_timestamp.add(toBN(10)),
                {from: rig.accounts.oracle}
            );
            await helpers.increaseTime(constants.DEFAULT_STALE_RATE_PERIOD)

			xdr_currency_rate = await rig.exchangeRates.rates(constants.XDR_CURRENCY_KEY)
			assert.isTrue(
				new BigNumber(xdr_currency_rate).eq(constants.TOTAL_SUM_OF_XDR_RATES),
				`Incorrect XDR rate, expected: ${constants.TOTAL_SUM_OF_XDR_RATES}, actual: ${xdr_currency_rate}`
			)
            assert.isFalse(
                await rig.exchangeRates.rateIsStale(rig.currencyKeys[0]),
                "Exchange rate of sUSD should never be stale."
            );
            for (let i = 1; i < rig.currencyKeys.length; i++) {
                assert.isTrue(
                    await rig.exchangeRates.rateIsStale(rig.currencyKeys[i]),
                    `Exchange rate ${i} should now be slightly stale.`
                );
            }
            for (let i = 0; i < rig.currencyKeys.length; i++) {
                if (i > 0) {
                    assert.isTrue(
                        await rig.exchangeRates.anyRateIsStale(rig.currencyKeys.slice(0, i + 1)),
                        `Exchange rate ${i} should now be slightly stale (in array slice 1)`
                    );
                }
                assert.isTrue(
                    await rig.exchangeRates.anyRateIsStale(rig.currencyKeys.slice(i, rig.currencyKeys.length)),
                    `Exchange rate ${i} should now be slightly stale (in array slice 2)`
                );
            }

            // ... Now change the stale period (after checking it again)...

            let original_stale_period = await rig.exchangeRates.rateStalePeriod();
            assert(new BigNumber(original_stale_period).eq(constants.DEFAULT_STALE_RATE_PERIOD), "Incorrect rateStalePeriod (2)");

            await rig.exchangeRates.setRateStalePeriod(2 * constants.DEFAULT_STALE_RATE_PERIOD, {from: rig.accounts.owner});

            let new_stale_period = await rig.exchangeRates.rateStalePeriod();
            assert(
                new BigNumber(new_stale_period).eq(2 * constants.DEFAULT_STALE_RATE_PERIOD),
                "Incorrect rateStalePeriod after changing it"
            );

            // ... and now the rates should all be not stale any more.
            assert.isFalse(
                await rig.exchangeRates.rateIsStale(rig.currencyKeys[0]),
                "Exchange rate of sUSD should never be stale (still)."
            );
            for (let i = 1; i < rig.currencyKeys.length; i++) {
                assert.isFalse(
                    await rig.exchangeRates.rateIsStale(rig.currencyKeys[i]),
                    `Exchange rate ${i} should not be slightly stale any more.`
                );
            }
            for (let i = 0; i < rig.currencyKeys.length; i++) {
                if (i > 0) {
                    assert.isFalse(
                        await rig.exchangeRates.anyRateIsStale(rig.currencyKeys.slice(0, i + 1)),
                        `Exchange rate ${i} should not be slightly stale any more (in array slice 1)`
                    );
                }
                assert.isFalse(
                    await rig.exchangeRates.anyRateIsStale(rig.currencyKeys.slice(i, rig.currencyKeys.length)),
                    `Exchange rate ${i} should not be slightly stale any more (in array slice 2)`
                );
            }

            // Set the stale rate back to original
            await rig.exchangeRates.setRateStalePeriod(constants.DEFAULT_STALE_RATE_PERIOD, {from: rig.accounts.owner});
            original_stale_period = await rig.exchangeRates.rateStalePeriod();
            assert(new BigNumber(original_stale_period).eq(constants.DEFAULT_STALE_RATE_PERIOD), "Incorrect rateStalePeriod (3)");


            let current_timestamp = await helpers.timestamp()
            // Set all rates as in the future
            await rig.exchangeRates.updateRates(
                rig.currencyKeys.slice(1,7),
                constants.SOME_SET_OF_RATES,
                current_timestamp.add(toBN(constants.ORACLE_FUTURE_LIMIT - 4)), // 4 seconds before the furthest in the future
                {from: rig.accounts.oracle}
            );
            for (let i = 0; i < rig.currencyKeys.length; i++) {
                assert.isFalse(
                    await rig.exchangeRates.rateIsStale(rig.currencyKeys[i]),
                    `Exchange rate ${i} should not be stale (in the future)`
                );
            }
            assert.isFalse(
                await rig.exchangeRates.anyRateIsStale(rig.currencyKeys),
                `None of the exchange rates should be stale`
            );

            // Lets also check that synthetix's effectiveValue is calculated as expected
            for (let i = 0; i < rig.currencyKeys.length; i++) {
                if (rig.currencyKeys[i] === constants.XDR_CURRENCY_KEY) {
                    helpers.assertBNEqual(
                        await rig.synthetix.effectiveValue(rig.currencyKeys[i], 100, rig.currencyKeys[0]),
                        toBN(5100),
                        `Expected 100 sUSD to be ${1000 + (i * 100)} currencyKeys[${i}]`
                    )
                } else if(i === 0) { // sUSD is just 1 to 1
					helpers.assertBNEqual(
						await rig.synthetix.effectiveValue(rig.currencyKeys[i], 100, rig.currencyKeys[0]),
						toBN(100),
						`Expected 100 sUSD to be ${100 + (i * 100)} currencyKeys[${i}]`
					)
				} else {
                    helpers.assertBNEqual(
                        await rig.synthetix.effectiveValue(rig.currencyKeys[i], 100, rig.currencyKeys[0]),
                        toBN(1000 + (i * 100)),
                        `Expected 100 sUSD to be ${1000 + (i * 100)} currencyKeys[${i}]`
                    )
                }
            }


			// Just make sUSD stale
			await helpers.increaseTime(constants.DEFAULT_STALE_RATE_PERIOD)
			current_timestamp = await helpers.timestamp()
            await rig.exchangeRates.updateRates(
                rig.currencyKeys.slice(1,7),
                constants.SOME_SET_OF_RATES,
                current_timestamp.add(toBN(10)),
                {from: rig.accounts.oracle}
            );



            assert.isFalse(
                // Need to ignore XDR and SNX, since XDR gets recalculated with stale key
                await rig.exchangeRates.anyRateIsStale(rig.currencyKeys.slice(0, 5)),
                "anyRateIsStale should be false when only sUSD is made stale (ignoring SNX & XDR)"
            );
            /* === This test is no longer valid

            assert.isTrue(
                // Should be stale if setting sUSD to stale, when we include XDR as a key
                await rig.exchangeRates.anyRateIsStale(rig.currencyKeys),
                "anyRateIsStale should be false when only sUSD is made stale."
            );
             */
            assert.isFalse(
                await rig.exchangeRates.rateIsStale(rig.currencyKeys[0]),
                "Rate 0 should never be stale."
            );
            assert.isFalse(
                await rig.exchangeRates.rateIsStale(rig.currencyKeys[1]),
                "Rate 1 should not yet be stale."
            );


			// Just make the third rate stale
			await helpers.increaseTime(constants.DEFAULT_STALE_RATE_PERIOD + 10)
			current_timestamp = await helpers.timestamp()
            await rig.exchangeRates.updateRates(
                [rig.currencyKeys[1]],
                constants.SOME_SET_OF_RATES.slice(0,1),
				current_timestamp.add(toBN(10)),
                {from: rig.accounts.oracle}
            );
			await rig.exchangeRates.updateRates(
				rig.currencyKeys.slice(3,7),
				constants.SOME_SET_OF_RATES.slice(2,6),
				current_timestamp.add(toBN(10)),
				{from: rig.accounts.oracle}
			);

            assert.isTrue(
                await rig.exchangeRates.anyRateIsStale(rig.currencyKeys),
                "anyRateIsStale should be true when one of the rates is now stale."
            );
            assert.isTrue(
                await rig.exchangeRates.rateIsStale(rig.currencyKeys[2]),
                "Rate 2 should now be stale."
            );
            assert.isFalse(
                await rig.exchangeRates.rateIsStale(rig.currencyKeys[1]),
                "Rate 1 should should not have become stale."
            );
            assert.isFalse(
                await rig.exchangeRates.rateIsStale(rig.currencyKeys[3]),
                "Rate 3 should should not have become stale."
            );
            assert.isFalse(
                await rig.exchangeRates.rateIsStale(rig.currencyKeys[0]),
                "Rate 0 (sUSD) should should not have become stale."
            );


            // Let's just make sure no one else can update the stale rate period.
            await assertRevert(
                rig.exchangeRates.setRateStalePeriod(4 * constants.DEFAULT_STALE_RATE_PERIOD, {from: rig.accounts.oracle}),
                `The oracle should not be able to set the rate stale period.`
            );
            await assertRevert(
                rig.exchangeRates.setRateStalePeriod(5 * constants.DEFAULT_STALE_RATE_PERIOD, {from: rig.accounts.beneficiary}),
                `The beneficiary should not be able to set the rate stale period.`
            );


        });


        it('Testing [deleteRate]', async function () {
            rig = await deployer.deployTestRig(accounts.slice(0, 6));



            for (let i = 0; i < rig.currencyKeys.length; i++) {
                await assertRevert(
                    rig.exchangeRates.deleteRate(rig.currencyKeys[i], {from: rig.accounts.owner}),
                    `Currency key ${i} should not be deletable by contract owner.`
                );
                await assertRevert(
                    rig.exchangeRates.deleteRate(rig.currencyKeys[i], {from: rig.accounts.beneficiary}),
                    `Currency key ${i} should not be deletable by contract beneficiary.`
                );
            }


            // Start by deleting all the rates & checking
            for (let i = 0; i < rig.currencyKeys.length; i++) {
                rig.exchangeRates.deleteRate(rig.currencyKeys[i], {from: rig.accounts.oracle});
                let new_rate = await rig.exchangeRates.rateForCurrency(rig.currencyKeys[i]);
                assert(
                    new BigNumber(new_rate).eq(0),
                    `Currency key ${i} rate should be 0 after being deleted.`
                );
                let new_update_time = await rig.exchangeRates.lastRateUpdateTimeForCurrency(rig.currencyKeys[i]);
                assert(
                    new BigNumber(new_update_time).eq(0),
                    `Currency key ${i} update time should be 0 after being deleted.`
                );
            }

            // Shouldn't be able to delete twice
            for (let i = 0; i < rig.currencyKeys.length; i++) {
                await assertRevert(
                    rig.exchangeRates.deleteRate(rig.currencyKeys[i]),
                    `Should revert when deleting currencyKey[${i}] because all currency keys have already been deleted.`
                )
            }

            // Shouldn't be able to delete fake currencies
            await assertRevert(
                rig.exchangeRates.deleteRate(constants.fake_currency_key_1),
                `Should revert when deleting fake currency keys 1.`
            );
            await assertRevert(
                rig.exchangeRates.deleteRate(constants.fake_currency_key_2),
                `Should revert when deleting fake currency keys 2.`
            );
            await assertRevert(
                rig.exchangeRates.deleteRate(constants.fake_currency_key_3),
                `Should revert when deleting fake currency keys 3 (a.k.a. sAUD).`
            );

        });

        it('Testing [setOracle]', async function () {

            rig = await deployer.deployTestRig(accounts.slice(0, 6));

            await assertRevert(
                rig.exchangeRates.setOracle(rig.accounts.owner, {from: rig.accounts.oracle}),
                "The oracle account should not be able to set the oracle address."
            );
            await assertRevert(
                rig.exchangeRates.setOracle(rig.accounts.owner, {from: rig.accounts.beneficiary}),
                "The beneficiary account should not be able to set the oracle address."
            );
            rig.exchangeRates.setOracle(rig.accounts.beneficiary, {from: rig.accounts.owner});
            assert.equal(
                await rig.exchangeRates.oracle(),
                rig.accounts.beneficiary,
                `The oracle should have been set to the beneficiary account in the previous line.`
            );

            await assertRevert(
                rig.exchangeRates.setOracle(rig.accounts.owner, {from: rig.accounts.oracle}),
                "The oracle account should not be able to set the oracle address. (even after changing)"
            );
            await assertRevert(
                rig.exchangeRates.setOracle(rig.accounts.owner, {from: rig.accounts.beneficiary}),
                "The beneficiary account should not be able to set the oracle address. (even after changing)"
            );


            await assertRevert(
                rig.exchangeRates.deleteRate(rig.currencyKeys[1], {from: rig.accounts.owner}),
                `Testing oracle has changed: Currency key 1 should not be deletable by contract owner.`
            );
            await assertRevert(
                rig.exchangeRates.deleteRate(rig.currencyKeys[1], {from: rig.accounts.oracle}),
                `Testing oracle has changed: Currency key 1 should not be deletable by previous oracle.`
            );

            let old_rate = await rig.exchangeRates.rateForCurrency(rig.currencyKeys[1]);
            assert(
                BigNumber(old_rate).eq(toUnit(1)),
                "The old_rate should still be 1 because we haven't touched it yet."
            );
            rig.exchangeRates.deleteRate(rig.currencyKeys[1], {from: rig.accounts.beneficiary});
            let new_rate = await rig.exchangeRates.rateForCurrency(rig.currencyKeys[1]);
            assert(
                BigNumber(new_rate).eq(0),
                "The new_rate should have been updated to be zero by the new oracle account."
            );
        });

    });
});
			



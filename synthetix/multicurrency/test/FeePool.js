const deployer = require('../deployer.js')
const BigNumber = require('bignumber.js')

const helpers = require('../testHelpers.js')
const synthetixHelpers = require('../synthetixHelpers.js')

const toUnit = synthetixHelpers.toUnit
const assertRevert = helpers.assertRevert
const allocateSynthetixsTo = synthetixHelpers.allocateSynthetixsTo
const toBN = web3.utils.toBN
const getTimestamp = helpers.timestamp
/*
 * Minor Helpers
 */

const days = (x) => x * 60 * 60 * 24
assert(days(2) == 172800 , 'days() is incorect')

const hours = (x) => x * 60 * 60
assert(hours(2) == 7200, 'hours() is incorrect')

const [sUSD, sAUD, sEUR, SNX, XDR, sCHF, sGBP] = ['sUSD', 'sAUD', 'sEUR', 'SNX', 'XDR', 'sCHF', 'sGBP'].map(
	web3.utils.asciiToHex
);


contract('FeePool', (accounts) => {

	describe('FeePool test', async () => {

		it('should allow owner to transfer synthetixs', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const synthetix = rig.synthetix
			const exchangeRate = rig.exchangeRates
			let initialBalance = toUnit(1000)
			let totalSupply = await synthetix.totalSupply()
			let owner = rig.accounts.owner
			let user = accounts[2]
			await allocateSynthetixsTo(rig, owner, initialBalance)
			owner_balance = new BigNumber(await synthetix.balanceOf(rig.accounts.owner))
			assert(owner_balance.eq(initialBalance), "Incorrect owner balance");
			await synthetix.transfer(user, initialBalance.div(toBN(10)), { from: owner })
			assert(await synthetix.balanceOf(user) != 0, 'Transfer not completed')

		})

		it('should allow owner to update exchange fee rate', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const feepool = rig.feePool

			// set the new exchange fee rate to 5%

			newExchangeFeeRate = toUnit(0.05)
			feepool.setExchangeFeeRate(newExchangeFeeRate, { from: rig.accounts.owner,})
			updatedFeeRate = toBN(new BigNumber(await feepool.exchangeFeeRate()))

			assert(newExchangeFeeRate.cmp(updatedFeeRate) == 0, 'Exchange rate was not correctly updated')

		})

		it('should allow owner to update transfer fee rate', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const feepool = rig.feePool

			// set the new exchange fee rate to 8%

			newTransferRate = toUnit(0.08)
			feepool.setTransferFeeRate(newTransferRate, { from: rig.accounts.owner,})
			updatedFeeRate = toBN(new BigNumber(await feepool.transferFeeRate()))

			assert(newTransferRate.cmp(updatedFeeRate) == 0, 'Exchange rate was not correctly updated')

		})

		it('should revert when anyone but the owner tries to update fee rates', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const feepool = rig.feePool

			// set the new exchange fee rate to 8%

			newRate = toUnit(0.08)
			await assertRevert(feepool.setExchangeFeeRate(newRate, { from: accounts[2],}))
			await assertRevert(feepool.setTransferFeeRate(newRate, { from: accounts[2],}))

		})

		it('should revert when owner updates the exchange fee rate to a value > MAX_TRANSFER_FEE_RATE', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const feepool = rig.feePool

			// set the new exchange fee rate to 25%

			newRate = toUnit(0.25)
			await assertRevert(feepool.setExchangeFeeRate(newRate, { from: rig.accounts.owner,}))

		})

		it('should revert when owner updates the transfer fee rate to a value > MAX_EXCHANGE_FEE_RATE', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const feepool = rig.feePool

			// set the new exchange fee rate to 25%

			newRate = toUnit(0.25)
			await assertRevert(feepool.setTransferFeeRate(newRate, { from: rig.accounts.owner,}))

		})

		it('should allow owner to update fee authority', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const feepool = rig.feePool
			// set the new exchange fee rate to 25%
			assert(await feepool.feeAuthority() == accounts[5], 'Accounts[1] is not the present owner')
			await feepool.setFeeAuthority(accounts[10], { from: rig.accounts.owner,})
			assert(await feepool.feeAuthority() == accounts[10], 'FeeAuthority not updated')

		})

		it('should revert when anyone but the owner tries to update the fee authority', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const feepool = rig.feePool
			// set the new exchange fee rate to 25%
			assert(await feepool.feeAuthority() == accounts[5], 'Accounts[5] is not the present owner')
			await assertRevert(feepool.setFeeAuthority(accounts[10], { from: accounts[3],}))

		})

		it('should revert when anyone but the owner tries to update the fee authority', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const feepool = rig.feePool
			// set the new exchange fee rate to 25%
			assert(await feepool.feeAuthority() == accounts[5], 'Accounts[5] is not the present owner')
			await assertRevert(feepool.setFeeAuthority(accounts[10], { from: accounts[3],}))

		})

		it('should allow owner to update the synthetix state variable', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const feepool = rig.feePool
			// set new Synthetix to arbitrary address i.e. accounts[9]
			newSynthetix = accounts[9]
			await feepool.setSynthetix(newSynthetix, { from: rig.accounts.owner,})
			currentSynthetix = feepool.synthetix()
			assert(newSynthetix != currentSynthetix, 'FeeAuthority not updated')

		})

		it('should revert when anyone but the owner tries to update the synthetix state variable', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const feepool = rig.feePool
			// set new Synthetix to arbitrary address i.e. accounts[9]
			newSynthetix = accounts[9]
			await assertRevert(feepool.setSynthetix(newSynthetix, { from: accounts[5],}))
		})

		it('should allow owner to change feePeriodDuration', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const feepool = rig.feePool
			//fetching previous feePeriodDuration
			// defining time constants
			const oneDay = new BigNumber(24 * 60 * 60)
			const oneMonth = 30 * oneDay

			await feepool.setFeePeriodDuration(oneMonth, { from: rig.accounts.owner,})
			currentFeePeriod = await feepool.feePeriodDuration()
			assert(currentFeePeriod == oneMonth, 'Fee Period not updated properly')

		})

		it('should revert when anyone but the owner attempts to update feePeriodDuration', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const feepool = rig.feePool
			//fetching previous feePeriodDuration
			// defining time constants
			const oneDay = new BigNumber(24 * 60 * 60)
			const oneMonth = 30 * oneDay

			await assertRevert(feepool.setFeePeriodDuration(oneMonth, { from: accounts[7],}))
			currentFeePeriod = await feepool.feePeriodDuration()
			assert(currentFeePeriod != oneMonth, 'Fee Period updated incorrectly')

		})

		it('should revert when owner attempts to update feePeriod with value < MIN_FEE_PERIOD_DURATION', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const feepool = rig.feePool
			//fetching previous feePeriodDuration
			// defining time constants
			const oneHour = new BigNumber(60*60)

			await assertRevert(feepool.setFeePeriodDuration(oneHour, { from: rig.accounts.owner,}))
			currentFeePeriod = await feepool.feePeriodDuration()
			assert(currentFeePeriod != oneHour, 'Fee Period updated incorrectly')

		})

		it('should revert when owner attempts to update feePeriod with value > MAX_FEE_PERIOD_DURATION', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const feepool = rig.feePool
			//fetching previous feePeriodDuration
			// defining time constants
			const oneDay = new BigNumber(24 * 60 * 60)
			const oneYear = 365 * oneDay

			await assertRevert(feepool.setFeePeriodDuration(oneYear, { from: rig.accounts.owner,}))
			currentFeePeriod = await feepool.feePeriodDuration()
			assert(currentFeePeriod != oneYear, 'Fee Period updated incorrectly')

		})

		it('should check the amountReceivedFromExchange is correct', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const feepool = rig.feePool
			// calculated as follows: actual_amount = amount_sent / (exchangeFeeRate + 1) and not actual_amount = amount_sent * (1 - exchangeFeeRate)
			amountSent = toUnit(50)
			unit = toUnit(1)

			exchangeFeeRate = await feepool.exchangeFeeRate()
			// compute expected value to compare with output of amountReceivedFromExchange

			expectedValue = amountSent.mul(unit).div(exchangeFeeRate.add(unit))

			actualValue  = await feepool.amountReceivedFromExchange(amountSent)

			assert (expectedValue.cmp(actualValue) == 0)

			// let's change the exchangeFeeRate and verify that the update is reflected in amountReceivedFromExchange

			newRate = toUnit(0.09)
			await feepool.setExchangeFeeRate(newRate, { from: rig.accounts.owner,})

			newExchangeFeeRateFee = await feepool.exchangeFeeRate()
			newExpectedValue = amountSent.mul(unit).div(newExchangeFeeRateFee.add(unit))
			newActualValue  = await feepool.amountReceivedFromExchange(amountSent)

			assert (newExpectedValue.cmp(newActualValue) == 0)

		})

		it('should check the amountReceivedFromTransfer is correct', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const feepool = rig.feePool

			amountSent = toUnit(500)
			unit = toUnit(1)

			transferFeeRate = await feepool.transferFeeRate()
			// compute expected value to compare with output of amountReceivedFromTransfer

			expectedValue = amountSent.mul(unit).div(transferFeeRate.add(unit))

			actualValue  = await feepool.amountReceivedFromTransfer(amountSent)

			assert (expectedValue.cmp(actualValue) == 0)

			// let's change the exchangeFeeRate and verify that the update is reflected in amountReceivedFromExchange

			newRate = toUnit(0.07)
			await feepool.setTransferFeeRate(newRate, { from: rig.accounts.owner,})

			newTransferFeeRateFee = await feepool.transferFeeRate()
			newExpectedValue = amountSent.mul(unit).div(newTransferFeeRateFee.add(unit))
			newActualValue  = await feepool.amountReceivedFromTransfer(amountSent)

			assert (newExpectedValue.cmp(newActualValue) == 0)

		})

		it('should have consistent exchange fee calculation methods', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const feepool = rig.feePool
			const synthetix = rig.synthetix

			amountToBeReceived = toUnit(5000)
			amountToBeSent = await feepool.exchangedAmountToReceive(amountToBeReceived)

			actualValue  = await feepool.amountReceivedFromExchange(amountToBeSent)

			assert (actualValue.cmp(amountToBeReceived) == 0)

		})

		it('should have consistent transfer fee calculation methods', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const feepool = rig.feePool
			const synthetix = rig.synthetix

			amountToBeReceived = toUnit(7000)
			amountToBeSent = await feepool.transferredAmountToReceive(amountToBeReceived)

			actualValue  = await feepool.amountReceivedFromTransfer(amountToBeSent)

			assert (actualValue.cmp(amountToBeReceived) == 0)

		})

		it('should return the correct exchange fee incurred', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const feepool = rig.feePool
			const synthetix = rig.synthetix

			amountToBeReceived = toUnit(100)
			amountToBeSent = await feepool.exchangedAmountToReceive(amountToBeReceived)

			expectedFee = await feepool.exchangeFeeIncurred(amountToBeReceived)
			effectiveFee = amountToBeSent.sub(amountToBeReceived)

			assert (effectiveFee.cmp(expectedFee) == 0, "Test")


		})

		it('should return the correct transfer fee incurred', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const feepool = rig.feePool
			const synthetix = rig.synthetix

			amountToBeReceived = toUnit(1337)
			amountToBeSent = await feepool.transferredAmountToReceive(amountToBeReceived)

			expectedFee = await feepool.transferFeeIncurred(amountToBeReceived)
			effectiveFee = amountToBeSent.sub(amountToBeReceived)


			assert (effectiveFee.cmp(expectedFee) == 0)

		})

		it('should return the correct penalty', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const feepool = rig.feePool
			const synthetix = rig.synthetix
			const exchangeRate = rig.exchangeRates

			let initialBalance = toUnit(10000)
			let owner = rig.accounts.owner
			let oracle = rig.accounts.oracle

			let user = accounts[2]
			await allocateSynthetixsTo(rig, owner, initialBalance)
			owner_balance = new BigNumber(await synthetix.balanceOf(rig.accounts.owner))

			const synthA = rig.synths['sUSD']
			tokenState = await synthA.tokenState()

			synthsAmount = toUnit(1999)
			await synthetix.transfer(user, initialBalance, { from: owner })
			await synthetix.issueSynths(sUSD, synthsAmount, { from: user})

			initialExchangeRate = await exchangeRate.rateForCurrency(SNX)

			collateralisationRatio = await synthetix.collateralisationRatio(user)

			currentPenalty = await feepool.currentPenalty(user)

			// update exchange rate to increase collateralisation ratio

			time = await getTimestamp()
			await exchangeRate.updateRates([SNX], [(toUnit(0.00002))], time, { from: oracle })

			newExchangeRate = await exchangeRate.rateForCurrency(SNX)
			newCollateralisationRatio = await synthetix.collateralisationRatio(user)
			newPenalty = await feepool.currentPenalty(user)

			assert(newCollateralisationRatio.cmp(toUnit(0.5)) == 1)
			assert(newPenalty.cmp(toUnit(0.75)) == 0)

 		})
		it('should return the correct exchange fee incurred', async () => {
			const rig = await deployer.deployTestRig(accounts)
			const feepool = rig.feePool
			const synthetix = rig.synthetix

			amountToBeReceived = toUnit(100)
			amountToBeSent = await feepool.exchangedAmountToReceive(amountToBeReceived)

			expectedFee = await feepool.exchangeFeeIncurred(amountToBeReceived)
			effectiveFee = amountToBeSent.sub(amountToBeReceived)

			assert (effectiveFee.cmp(expectedFee) == 0, "Test")

		})

				it('should not give users fees if they are not entitled to them', async () => {

					const rig = await deployer.deployTestRig(accounts)
					const feepool = rig.feePool
					const synthetix = rig.synthetix
					const exchangeRate = rig.exchangeRates

					let initialOwnerBalance = toUnit(10000000)
					let initialUserBalance = toUnit(5000000)
					let initialSynthTransfer = toUnit(5000)
					let owner = rig.accounts.owner
					let oracle = rig.accounts.oracle
					let feeAuthority = rig.accounts.feeAuthority

					let userA = accounts[2]
					let userB = accounts[3]
					let userC = accounts[4]
					let userD = accounts[5]

					await allocateSynthetixsTo(rig, owner, initialOwnerBalance)
					owner_balance = new BigNumber(await synthetix.balanceOf(rig.accounts.owner))

					const synthA = rig.synths['sUSD']

					await synthetix.transfer(userA, initialUserBalance, { from: owner })
					await synthetix.issueMaxSynths(sUSD, { from: userA})
					await synthA.transfer(userB, initialSynthTransfer, { from:  userA})
					await synthA.transfer(userC, initialSynthTransfer, { from:  userA})
					await synthA.transfer(userD, initialSynthTransfer, { from:  userA})

					let feesAvailable = new BigNumber(await feepool.feesAvailable(userA, sUSD))

					let debtBalance = await synthetix.debtBalanceOf(userA, XDR)

					time = await getTimestamp()

					//set the new time 10 days in the future
					period = time.toNumber() + days(10)

					await helpers.increaseTime(days(10))

					currentTime = period
					await exchangeRate.updateRates([sAUD, sEUR, sCHF, sGBP, SNX], [(toUnit(0.7)), (toUnit(1.1)), (toUnit(0.8)), (toUnit(0.9)), (toUnit(0.1))], currentTime, { from: oracle })

					// close fee period
					await synthA.transfer(userB, initialSynthTransfer, { from: userA})
					await synthA.transfer(userC, initialSynthTransfer, { from: userA})
					await synthA.transfer(userD, initialSynthTransfer, { from: userA})

					await helpers.increaseTime(days(7))
					await feepool.closeCurrentFeePeriod({ from: feeAuthority })

					currentTime = await getTimestamp()

					await exchangeRate.updateRates([sAUD, sEUR, sCHF, sGBP, SNX], [(toUnit(0.7)), (toUnit(1.1)), (toUnit(0.8)), (toUnit(0.9)), (toUnit(0.1))], currentTime.toNumber(), { from: oracle })

					newFees = new BigNumber(await feepool.feesAvailable(userA, sUSD))

					period = currentTime.toNumber() + days(7)

					await helpers.increaseTime(days(7))
					await exchangeRate.updateRates([sAUD, sEUR, sCHF, sGBP, SNX], [(toUnit(0.7)), (toUnit(1.1)), (toUnit(0.8)), (toUnit(0.9)), (toUnit(0.1))], period, { from: oracle })
					await feepool.closeCurrentFeePeriod({ from: feeAuthority })

					newFees = new BigNumber(await feepool.feesAvailable(userA, sUSD))

					assert(newFees.cmp(new BigNumber(0)) == 0)

				})

				it('should roll over the unclaimed fees', async () => {
					const rig = await deployer.deployTestRig(accounts)
					const feepool = rig.feePool
					const synthetix = rig.synthetix
					const exchangeRate = rig.exchangeRates
					let owner = rig.accounts.owner
					let oracle = rig.accounts.oracle
					let feeAuthority = rig.accounts.feeAuthority
					const synthA = rig.synths['sUSD']

					let userA = accounts[2]
					let userB = accounts[3]
					let userC = accounts[4]
					let userD = accounts[5]

					const length = (await feepool.FEE_PERIOD_LENGTH()).toNumber()
					let initialOwnerBalance = toUnit(10000000)
					await allocateSynthetixsTo(rig, owner, initialOwnerBalance)
					await synthetix.transfer(userA, toUnit('1000000'), { from: owner });
					await synthetix.issueSynths(sUSD, toUnit('20000'), { from: owner });
					//await synthetix.issueSynths(sUSD, toUnit('10000'), { from: userA });

					const transfer = toUnit(500)
					await synthA.transfer(userB, transfer, { from: owner });
					await synthA.transfer(userB, transfer, { from: owner });
					await synthA.transfer(userC, transfer, { from: owner });

					totalFees = new BigNumber(await feepool.totalFeesAvailable(sUSD))

					let ownerFees = new BigNumber(await feepool.feesAvailable(owner, sUSD))
					assert (ownerFees.cmp(new BigNumber(0)) == 0)

					for (let i = 0; i <= 5; i++) {

						await helpers.increaseTime(days(7))
						await feepool.closeCurrentFeePeriod({ from: feeAuthority })
						currentTime = await getTimestamp()

						await exchangeRate.updateRates([sAUD, sEUR, sCHF, sGBP, SNX], [(toUnit(0.7)), (toUnit(1.1)), (toUnit(0.8)), (toUnit(0.9)), (toUnit(0.1))], currentTime.toNumber(), { from: oracle })
						newOwnerFees = new BigNumber(await feepool.feesAvailable(owner, sUSD))
						totalFees = new BigNumber(await feepool.totalFeesAvailable(sUSD))


					}
					assert(newOwnerFees.cmp(totalFees) == 0)


				})
				it('should allow users to claim their fees', async () => {
					const rig = await deployer.deployTestRig(accounts)
					const feepool = rig.feePool
					const synthetix = rig.synthetix
					const exchangeRate = rig.exchangeRates
					let owner = rig.accounts.owner
					let oracle = rig.accounts.oracle
					let feeAuthority = rig.accounts.feeAuthority
					const synthA = rig.synths['sUSD']

					let userA = accounts[2]
					let userB = accounts[3]
					let userC = accounts[4]
					let userD = accounts[5]

					const length = (await feepool.FEE_PERIOD_LENGTH()).toNumber()
					let initialOwnerBalance = toUnit(10000000)
					await allocateSynthetixsTo(rig, owner, initialOwnerBalance)
					await synthetix.transfer(userA, toUnit('1000000'), { from: owner });
					await synthetix.issueSynths(sUSD, toUnit('20000'), { from: owner });

					totalFees = new BigNumber(await feepool.totalFeesAvailable(sUSD))

					await helpers.increaseTime(days(7))
					await feepool.closeCurrentFeePeriod({ from: feeAuthority })
					currentTime = await getTimestamp()
					await exchangeRate.updateRates([sAUD, sEUR, sCHF, sGBP, SNX], [(toUnit(0.7)), (toUnit(1.1)), (toUnit(0.8)), (toUnit(0.9)), (toUnit(0.1))], currentTime.toNumber(), { from: oracle })

					const transfer = toUnit(500)

					await synthA.transfer(userB, transfer, { from: owner });
					await synthA.transfer(userB, transfer, { from: owner });
					await synthA.transfer(userC, transfer, { from: owner });

					await helpers.increaseTime(days(7))
					await feepool.closeCurrentFeePeriod({ from: feeAuthority })
					currentTime = await getTimestamp()
					await exchangeRate.updateRates([sAUD, sEUR, sCHF, sGBP, SNX], [(toUnit(0.7)), (toUnit(1.1)), (toUnit(0.8)), (toUnit(0.9)), (toUnit(0.1))], currentTime.toNumber(), { from: oracle })


					totalFees = new BigNumber(await feepool.totalFeesAvailable(sUSD))

					let ownerFees = new BigNumber(await feepool.feesAvailable(owner, sUSD))
					assert (ownerFees.cmp(new BigNumber(0)) == 1)

					oldBalance = new BigNumber(await synthA.balanceOf(owner))
					await feepool.claimFees(sUSD, { from: owner })
					newBalance = new BigNumber(await synthA.balanceOf(owner))
					assert (newBalance.cmp(oldBalance) == 1)


				})


	})
})

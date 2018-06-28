const deployer = require('../deployer.js')
const BigNumber = require("bignumber.js")

const IssuanceController = artifacts.require('./IssuanceController')

const helpers = require('../testHelpers.js')
const assertRevert = helpers.assertRevert


/*
 * Multiply a number by the value of UNIT in the
 * smart contract's safe math.
 */
const toUnit = (x) => new BigNumber(x).times(Math.pow(10, 18))


/*
 * Return the amount of seconds in x hours
 */
const hours = (x) => x * 60 * 60
assert(hours(2) == 7200, `hours() is wrong`)
const days = (x) => x * 60 * 60 * 24
assert(days(2) === 172800, 'days() is wrong')

const addressHasCode = async function(address) {
	// empty code is '0x0'
	return (await web3.eth.getCode(address)).length > 3;
}


/*
 * Return the timestamp of the current block
 */
const timestamp = () => new BigNumber(web3.eth.getBlock(web3.eth.blockNumber).timestamp)


/*
 * Determine that a is within a percentage of b
 */
const withinMarginOfError = (a, b) => helpers.withinPercentageOf(a, b, 0.001)
assert(withinMarginOfError(10.0000999999, 10) === true, 'withinMarginOfError() broken')
assert(withinMarginOfError(10.000100001, 10) === false, 'withinMarginOfError() broken')
const assertWithinMargin = (a, b, msg) => assert(withinMarginOfError(a, b), msg)
assertWithinMargin(10.0000999999, 10, 'assertWithinMargin() broken')

const deployIssuanceControllerRig = async function(accounts, usdToEth, usdToHav) {
	const rig = await deployer.setupTestRig(accounts)

	rig.accounts.icFundsWallet = accounts[5];
	rig.accounts.icOracle = accounts[6];
	rig.accounts.icOwner = accounts[7];
	rig.ic = await IssuanceController.new(
		rig.accounts.icOwner,
		rig.accounts.icFundsWallet,
		rig.havven.address,
		rig.nomin.address,
		rig.accounts.icOracle,
		usdToEth,
		usdToHav,
	);

	return rig;
}

const allocateTokensToIssuanceController = async function(rig, nomins, havvens) {
	await allocateNominsTo(rig, rig.ic.address, nomins);
	await allocateHavvensTo(rig, rig.ic.address, havvens);
}

const allocateHavvensTo = async function(rig, address, havvens) {
	const h = rig.havven;
	const hs = rig.states.havven;
	const owner = rig.accounts.owner;

	// Temporarily hijack the havven state and allocate some tokens
	await hs.setAssociatedContract(owner, { from: owner });
	await hs.setBalanceOf(address, havvens, { from: owner });
	await hs.setAssociatedContract(h.address, { from: owner });
}

const allocateNominsTo = async function(rig, address, nomins) {
	const n = rig.nomin;
	const ns = rig.states.nomin;
	const owner = rig.accounts.owner;

	// Temporarily hijack the nomin state and allocate some tokens
	await ns.setAssociatedContract(owner, { from: owner });
	await ns.setBalanceOf(address, nomins, { from: owner });
	await ns.setAssociatedContract(n.address, { from: owner });
}


contract('IssuanceController', (accounts) => {
	const stalePeriod = hours(3);

	describe('constructor', function() {
		it('sets public variables', async function() {
			usdToEth = toUnit(600);
			usdToHav = toUnit(0.5);

			rig = await deployIssuanceControllerRig(
				accounts,
				usdToEth,
				usdToHav,
			);
			
			assert(await rig.ic.oracle() === rig.accounts.icOracle, 'oracle is not as expected');
			assert(await rig.ic.owner() === rig.accounts.icOwner, 'owner is not as expected');
			assert(await rig.ic.fundsWallet() === rig.accounts.icFundsWallet, 'fundsWallet is not as expected');
			assert(await rig.ic.havven() === rig.havven.address, 'havven is not as expected');
			assert(await rig.ic.nomin() === rig.nomin.address, 'nomin is not as expected');
			assert((await rig.ic.usdToHavPrice()).equals(usdToHav), 'usdToHav is not as expected');
			assert((await rig.ic.usdToEthPrice()).equals(usdToEth), 'usdToEth is not as expected');
			assert((await rig.ic.lastPriceUpdateTime()).equals(timestamp()), 'timestamp is not as expected');
		});
	});
	
	describe('self-destruct', function() {
		it('can destruct from owner', async function() {
			const usdToEth = toUnit(1);
			const usdToHav = toUnit(1);

			rig = await deployIssuanceControllerRig(
				accounts,
				usdToEth,
				usdToHav,
			);
			
			const owner = rig.accounts.icOwner;
			const beneficiary = accounts[9];
			
			assert(
				await addressHasCode(rig.ic.address) === true,
				'address should have code'
			);
			
			await rig.ic.setSelfDestructBeneficiary(beneficiary, { from: owner });
			await rig.ic.initiateSelfDestruct({ from: owner });
			await helpers.setDate(timestamp().plus(days(28)).plus(1));
			await rig.ic.selfDestruct({ from: owner });

			assert(
				await addressHasCode(rig.ic.address) === false,
				'address should no longer have code'
			);
		});
		
		it('wont destruct from non-owner', async function() {
			const usdToEth = toUnit(1);
			const usdToHav = toUnit(1);

			rig = await deployIssuanceControllerRig(
				accounts,
				usdToEth,
				usdToHav,
			);
			
			const owner = rig.accounts.icOwner;
			const notOwner = accounts[9];
			assert(owner != notOwner);
			
			assert(
				await addressHasCode(rig.ic.address) === true,
				'address should have code'
			);
			
			await assertRevert(
				rig.ic.initiateSelfDestruct({ from: notOwner })
			);
			await assertRevert(
				rig.ic.selfDestruct({ from: notOwner })
			);
		});
	});
	
	describe('stale period', function() {
		it('has a default stale period of 3 hours', async function() {
			rig = await deployIssuanceControllerRig(
				accounts, 
				toUnit(600), 
				toUnit(0.5)
			);

			assert(
				(await rig.ic.priceStalePeriod()).equals(stalePeriod),
				'stale period not as expected'
			);
		});
		
		it('will go stale with no price update after 3 hours', async function() {
			rig = await deployIssuanceControllerRig(
				accounts, 
				toUnit(600), 
				toUnit(0.5)
			);
			
			assert(
				await rig.ic.pricesAreStale() === false,
				'price should not be stale'
			);
			
			const staleFuture = timestamp()
				.plus(hours(3))
				.plus(1);
			helpers.setDate(staleFuture);

			assert(
				await rig.ic.pricesAreStale() === true,
				'price should be stale'
			);
		});
		
		it('will go stale given a stale time of 24 hours', async function() {
			rig = await deployIssuanceControllerRig(
				accounts, 
				toUnit(600), 
				toUnit(0.5)
			);
			
			const newStalePeriod = hours(24);

			await rig.ic.setPriceStalePeriod(
				newStalePeriod,
				{ from: rig.accounts.icOwner }
			);
			
			assert(
				await rig.ic.pricesAreStale() === false,
				'price should not be stale'
			);
			
			const staleFuture = timestamp()
				.plus(newStalePeriod)
				.plus(1);
			helpers.setDate(staleFuture);

			assert(
				await rig.ic.pricesAreStale() === true,
				'price should be stale'
			);
		});
	});
	
	describe('token management', function() {

		it('can withdraw nomins and havvens', async function() {
			nomins = toUnit(100);
			havvens = toUnit(99);

			rig = await deployIssuanceControllerRig(
				accounts, 
				toUnit(600), 
				toUnit(0.5)
			);
			const owner = rig.accounts.icOwner;
			assert((await rig.havven.balanceOf(owner)).equals(0), 'test needs owner to have no havvens');

			await allocateTokensToIssuanceController(rig, nomins, havvens);

			assert((await rig.havven.balanceOf(rig.ic.address)).equals(havvens), 'no havvens');
			assert((await rig.nomin.balanceOf(rig.ic.address)).equals(nomins), 'no nomins');

			await rig.ic.withdrawHavvens(havvens, { from: owner });
			assert((await rig.havven.balanceOf(rig.ic.address)).equals(0), 'ic still has havvens');
			assert((await rig.havven.balanceOf(owner)).equals(havvens), 'owner did not get havvens');
			
			await rig.ic.withdrawNomins(nomins, { from: owner });
			assert((await rig.nomin.balanceOf(rig.ic.address)).equals(0), 'ic still has nomins');
			const nominsAfterFee = nomins.minus(
				await rig.nomin.transferFeeIncurred(nomins)
			);
			assertWithinMargin(
				nominsAfterFee,
				await rig.nomin.balanceOf(owner), 
				'owner did not get enough nomin'
			);
		});
	});

	describe('eth to nomins exchange', function() {
		const user = accounts[8];
		const scenarios = [ // usd_eth, eth_in, nomins_out (ignore fee)
			[0, 0, 0],
			[0, 1, 0],
			[0.5, 1, 0.5],
			[100, 1, 100],
			[10000, 1, 10000],
			[100, 0.5, 50],
			[100, 0, 0],
		]
		const nominsForIssuanceController = toUnit(100000);

		it('will exchange at expected rate for various scenarios via fallback', async function() {
			let expectedFundsWalletBalance = web3.eth.getBalance(rig.accounts.icFundsWallet);

			for(var i = 0; i < scenarios.length; i++) {
				const price = toUnit(scenarios[i][0]);
				const eth = scenarios[i][1] * Math.pow(10, 18);
				const nomins = toUnit(scenarios[i][2]);
				expectedFundsWalletBalance = expectedFundsWalletBalance.plus(eth);
				
				const rig = await deployIssuanceControllerRig(
					accounts, 
					price, 
					toUnit(0.5)
				);

				await allocateTokensToIssuanceController(rig, nominsForIssuanceController, 1);

				await rig.ic.sendTransaction({ 
					from: user,
					value: eth,
				});

				const nominsAfterFee = nomins.minus(
					await rig.nomin.transferFeeIncurred(nomins)
				);
				assertWithinMargin(
					nominsAfterFee,
					await rig.nomin.balanceOf(user), 
					'user did not get enough nomin'
				);

				assert(
					web3.eth.getBalance(rig.accounts.icFundsWallet)
						.equals(expectedFundsWalletBalance),
					'funds wallet did not get eth'
				);
			}
		});

		it('will exchange at expected rate for various scenarios via direct method', async function() {
			let expectedFundsWalletBalance = web3.eth.getBalance(rig.accounts.icFundsWallet);

			for(var i = 0; i < scenarios.length; i++) {
				const price = toUnit(scenarios[i][0]);
				const eth = scenarios[i][1] * Math.pow(10, 18);
				const nomins = toUnit(scenarios[i][2]);
				expectedFundsWalletBalance = expectedFundsWalletBalance.plus(eth);
				
				const rig = await deployIssuanceControllerRig(
					accounts, 
					price, 
					toUnit(0.5)
				);

				await allocateTokensToIssuanceController(rig, nominsForIssuanceController, 1);

				await rig.ic.exchangeEtherForNomins({ 
					from: user,
					value: eth,
				});

				const nominsAfterFee = nomins.minus(
					await rig.nomin.transferFeeIncurred(nomins)
				);
				assertWithinMargin(
					nominsAfterFee,
					await rig.nomin.balanceOf(user), 
					'user did not get enough nomin'
				);

				assert(
					web3.eth.getBalance(rig.accounts.icFundsWallet)
						.equals(expectedFundsWalletBalance),
					'funds wallet did not get eth'
				);
			}
		});
	});

	describe('nomins to havvens exchange', function() {
		const user = accounts[8];

		it('will exchange at expected rate for various scenarios', async function() {
			const scenarios = [
				// nomin_per_havven, nomins_in, havvens_out (ignore fee)
				[0.5, 1, 2],
				[100, 50, 0.5],
				[1, 100000, 100000],
				[0.0001, 1, 10000],
				[1, 0.01, 0.01],
			]
			const havvensForIssuanceController = toUnit(10000000);

			for(var i = 0; i < scenarios.length; i++) {
				const price = toUnit(scenarios[i][0]);
				const nomins = toUnit(scenarios[i][1]);
				const havvens = toUnit(scenarios[i][2]);
				
				const rig = await deployIssuanceControllerRig(
					accounts, 
					toUnit(1000), 
					price
				);

				await allocateTokensToIssuanceController(
					rig, 
					1,
					havvensForIssuanceController
				);

				await allocateNominsTo(rig, user, nomins.times(2));
				await rig.nomin.approve(rig.ic.address, nomins, { from: user });

				await rig.ic.exchangeNominsForHavvens(nomins, { from: user });

				const havvensAfterFee = havvens
					.minus(havvens.times(0.0015));

				assertWithinMargin(
					havvensAfterFee,
					await rig.havven.balanceOf(user), 
					'user did not get enough havvens'
				);
			}
		});
		
		it('will exchange at expected rate for various scenarios given shifting prices', async function() {
			const scenarios = [
				// nomin_per_havven, nomins_in, havvens_out (ignore fee)
				[0.5, 1, 2],
				[100, 50, 0.5],
				[1, 100000, 100000],
				[0.0001, 1, 10000],
				[1, 0.01, 0.01],
			]
			const havvensForIssuanceController = toUnit(10000000);
			const usdToEthPrice = toUnit(1000);
			const rig = await deployIssuanceControllerRig(
				accounts, 
				usdToEthPrice, 
				toUnit(100)
			);
			let userHavvenBalance = await rig.havven.balanceOf(user);

			for(var i = 0; i < scenarios.length; i++) {
				const price = toUnit(scenarios[i][0]);
				const nomins = toUnit(scenarios[i][1]);
				const havvens = toUnit(scenarios[i][2]);

				helpers.setDate(timestamp().plus(hours(1)));

				await rig.ic.updatePrices(
					usdToEthPrice,
					price,
					timestamp(),
					{ from: rig.accounts.icOracle }
				)
				assert((await rig.ic.usdToHavPrice()).equals(price), 'price did not update');

				await allocateTokensToIssuanceController(
					rig, 
					1,
					havvensForIssuanceController
				);

				await allocateNominsTo(rig, user, nomins.times(2));
				await rig.nomin.approve(rig.ic.address, nomins, { from: user });

				await rig.ic.exchangeNominsForHavvens(nomins, { from: user });

				const havvensAfterFee = havvens
					.minus(havvens.times(0.0015));
				const expectedUserHavvenBalance = userHavvenBalance.plus(
					havvensAfterFee
				)

				assertWithinMargin(
					expectedUserHavvenBalance,
					await rig.havven.balanceOf(user), 
					'user did not get enough havvens'
				);

				userHavvenBalance = await rig.havven.balanceOf(user);
			}
		});
		
		it('will revert given a zero usd/havven price', async function() {
			const scenarios = [
				// nomin_per_havven, nomins_in, havvens_out (ignore fee)
				[0, 1, 0],
			]
			const havvensForIssuanceController = toUnit(10000000);

			for(var i = 0; i < scenarios.length; i++) {
				const nomins = toUnit(1);
				
				const rig = await deployIssuanceControllerRig(
					accounts, 
					toUnit(1000), 
					toUnit(0)
				);

				await allocateTokensToIssuanceController(
					rig, 
					1,
					toUnit(10000)
				);

				await allocateNominsTo(rig, user, nomins.times(2));
				await rig.nomin.approve(rig.ic.address, nomins, { from: user });

				await assertRevert(
					rig.ic.exchangeNominsForHavvens(nomins, { from: user }),
					'a zero usd/havven price should revert'
				);
			}
		});
	});
});

const BigNumber = require("bignumber.js")

const Court = artifacts.require('./Court.sol')
const Havven = artifacts.require('./Havven.sol')
const Nomin = artifacts.require('./Nomin.sol')
const HavvenEscrow = artifacts.require('./HavvenEscrow.sol')
const TokenState = artifacts.require('./TokenState.sol')
const Proxy = artifacts.require('./Proxy')
const IssuanceController = artifacts.require('./IssuanceController.sol')


/*
 * Multiply a number by the value of UNIT in the
 * smart contract's safe math.
 */
const toUnit = (x) => new BigNumber(x).times(Math.pow(10, 18))
assert(toUnit(3).toString() === "3000000000000000000", 'toUnit() is wrong')

module.exports.setupTestRig = async function (accounts) {
	// define our accounts
	const owner = accounts[1];
	const oracle = accounts[2];
	const beneficiary = accounts[3];
	const fundsWallet = accounts[4];

	// Create the proxy contract
	const proxyForHavven = await Proxy.new(owner);
	const proxyForNomin = await Proxy.new(owner);

	// Create the state contracts
	stateForHavven = await TokenState.new(owner, `0x0`);

	// deploy a Havven contract
	const havven = await Havven.new(
		proxyForHavven.address,		// proxy
		stateForHavven.address,		// state
		owner,						// owner,
		oracle,						// oracle,
		toUnit(10000),				// initalHavPrice
		{from : owner}
	)	

	// deploy a Nomin contract
	const nomin = await Nomin.new(
		proxyForNomin.address,		// proxy
		havven.address,				// havven
		owner,						// owner
		{from: owner}
	)

	// deploy a Court contract
	const court = await Court.new(
		havven.address,
		nomin.address,
		owner,
		{from: owner}
	)
	// deploy a HavvenEscrow contract
	const escrow = await HavvenEscrow.new(
		owner,
		havven.address,
		{from: owner}
	)

	await proxyForHavven.setTarget(havven.address, {from: owner})
	await havven.setProxy(proxyForHavven.address, { from: owner })
	await proxyForNomin.setTarget(nomin.address, {from: owner})
	await nomin.setProxy(proxyForNomin.address, { from: owner })

	// configure the contracts now they're all up
	await havven.setNomin(nomin.address, {from: owner});
	await havven.setEscrow(escrow.address, {from: owner});
	await nomin.setCourt(court.address, {from: owner});
	// make the target contract methods available at the proxy contract 
	const proxiedHavven = await Havven.at(proxyForHavven.address)
	const proxiedNomin = await Nomin.at(proxyForNomin.address)
	// set the assoicated contract for the state
	await stateForHavven.setAssociatedContract(havven.address, { from: owner });

	// Get an instance of the nomin token state
	const stateForNomin = TokenState.at(await nomin.tokenState());


	// return an object with all the useful bits
	return {
		accounts: { owner, oracle, beneficiary, fundsWallet },
		proxies: { havven: proxiedHavven, nomin: proxiedNomin },
		states: { havven: stateForHavven, nomin: stateForNomin },
		havven: havven,
		nomin: nomin,
		court,
		escrow,
	}
}

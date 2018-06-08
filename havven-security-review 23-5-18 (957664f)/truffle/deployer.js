const BigNumber = require("bignumber.js")

const Court = artifacts.require('./Court.sol')
const Havven = artifacts.require('./Havven.sol')
const Nomin = artifacts.require('./Nomin.sol')
const HavvenEscrow = artifacts.require('./HavvenEscrow.sol')
const TokenState = artifacts.require('./TokenState.sol')
const Proxy = artifacts.require('./Proxy')


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

	// deploy a Havven contract
	const havven = await Havven.new(
		'0x0',			// proxy
		'0x0',	// initialState,
		owner,			// owner,
		oracle,			// oracle,
		toUnit(10000)	// initalHavPrice
	)

	// deploy an Nomin contract
	const nomin = await Nomin.new(
		'0x0',			// proxy
		havven.address,	// havven
		owner,			// owner
		'0x0',		// initialState
	)

	// deploy a Court contract
	const court = await Court.new(
		havven.address,
		nomin.address,
		owner
	)
	// deploy a HavvenEscrow contract
	const escrow = await HavvenEscrow.new(
		owner,
		havven.address,
	)
	// configure the contracts now they're all up
	await havven.setNomin(nomin.address, {from: owner});
	await havven.setEscrow(escrow.address, {from: owner});
	await nomin.setCourt(court.address, {from: owner});
	// create proxies for havven and nomin
	const proxyForHavven = await Proxy.new(owner)
	await proxyForHavven.setTarget(havven.address, {from: owner})
	await havven.setProxy(proxyForHavven.address, { from: owner })
	const proxyForNomin = await Proxy.new(owner)
	await proxyForNomin.setTarget(nomin.address, {from: owner})
	await nomin.setProxy(proxyForNomin.address, { from: owner })
	// make the target contract methods available at the proxy contract 
	const proxiedHavven = await Havven.at(proxyForHavven.address)
	const proxiedNomin = await Nomin.at(proxyForNomin.address)
	// return an object with all the useful bits
	return {
		accounts: { owner, oracle, beneficiary },
		proxies: { havven: proxiedHavven, nomin: proxiedNomin },
		havven: havven,
		nomin: nomin,
		court,
		escrow,
	}
}

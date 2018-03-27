const BigNumber = require("bignumber.js")

const Court = artifacts.require('./Court.sol')
const Havven = artifacts.require('./Havven.sol')
const EtherNomin = artifacts.require('./EtherNomin.sol')
const HavvenEscrow = artifacts.require('./HavvenEscrow.sol')


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
		const havven = await Havven.new(owner)
		// deploy an EtherNomin contract
		const nomin = await EtherNomin.new(
			havven.address,
			oracle,
			beneficiary,
			toUnit(10000),
			owner
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
			nomin.address
		)
		// configure the contracts now they're all up
		await havven.setNomin(nomin.address, {from: owner});
		await havven.setEscrow(escrow.address, {from: owner});
		await nomin.setCourt(court.address, {from: owner});
		// return an object with all the useful bits
		return { 
			accounts: { owner, oracle, beneficiary }, 
			havven, 
			nomin, 
			court,
			escrow
		}
	}

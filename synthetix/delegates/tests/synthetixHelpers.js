const BigNumber = require('bignumber.js')
const toBN = web3.utils.toBN
BigNumber.config({ERRORS:false});
/*
 * Multiply a number by the value of UNIT in the
 * smart contract's safe math.
 */
// const toUnit = (x) => new BigNumber(x).times(Math.pow(10, 18))
// const toUnit = (x) => toBN(x).mul(toBN(Math.pow(10, 18)))

// const toUnit = x => toBN(web3.utils.toWei(x, 'ether'))
const toUnit = (x) => toBN(new BigNumber(x).times(Math.pow(10, 18)))

module.exports.toUnit = toUnit

const allocateTokensToDepot = async function (rig, synths, synthetixs) {
	await allocateSynthsTo(rig, rig.depot.address, synths)
	await allocateSynthetixsTo(rig, rig.depot.address, synthetixs)
}
module.exports.allocateTokensToDepot = allocateTokensToDepot

const allocateSynthetixsTo = async function (rig, address, synthetixs) {
	const s = rig.synthetix
	const ss = rig.synthetixTokenState
	const owner = rig.accounts.owner

	// Temporarily hijack the synthetix state and allocate some tokens
	await ss.setAssociatedContract(owner, { from: owner })
	await ss.setBalanceOf(address, synthetixs, { from: owner })
	await ss.setAssociatedContract(s.address, { from: owner })
}
module.exports.allocateSynthetixsTo = allocateSynthetixsTo

const allocateSynthsTo = async function (rig, currencyKey, address, synths) {
	const sn = rig.synths[currencyKey]
	const owner = rig.accounts.owner

	// Change the synthetix contract to be owner, allow it to issue some tokens
	// then switch it back to the real synthetix contract
	await sn.setSynthetix(owner, { from: owner })
	await sn.issue(address, synths, { from: owner })
	await sn.setSynthetix(rig.synthetix.address, { from: owner })
}
module.exports.allocateSynthsTo = allocateSynthsTo

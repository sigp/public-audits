const BigNumber = require('bignumber.js')
const Fantom = artifacts.require('./FantomToken.sol')
const th = require('./testHelpers.js')

const days = 3600*24
const timestamp = () => new BigNumber(web3.eth.getBlock(web3.eth.blockNumber).timestamp)

module.exports.setupContract = async function(accounts) {

		await th.mineOne();	
		let owner = accounts[0]
    ICOStartTime = parseInt(timestamp()) + 100; 
    ICOEndTime = ICOStartTime  + 5 *days
    let fantom = await Fantom.new(ICOStartTime, ICOEndTime, {from: owner})

    return {owner, fantom, ICOStartTime, ICOEndTime}
}

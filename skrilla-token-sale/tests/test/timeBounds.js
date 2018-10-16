const BigNumber = require("bignumber.js");
var SkrillaToken = artifacts.require('./SkrillaToken.sol')
var testHelpers = require("../testHelpers.js");

const day = 3600 * 24		// seconds in a day

contract('SkrillaToken (timeBounds)', function(accounts) {
	
	beforeEach(() => {
		return testHelpers.mineBlocks(1)
	})
	
	it('should permit a whitelisted account before the presale starts', function() {
        let contract = undefined;
		let tokenPrice = undefined;
		const now =  web3.eth.getBlock(web3.eth.blockNumber).timestamp;
		const presaleStart = now + 50 * day
		const saleStart = now + 100 * day
		const targetRate = 8000
		const investment = 10 * Math.pow(10, 18)
		const tokens = (investment / Math.pow(10, 18)) * targetRate * Math.pow(10, 6)

		return SkrillaToken.new(
			presaleStart,
			saleStart,
			accounts[4],
			accounts[5],
			accounts[6]
		)
			.then((result) => contract = result)
			.then(() => contract.addToWhitelist(accounts[1], targetRate))
            .then(() => contract.buyTokens({
                from: accounts[1],
                value: investment
			}))
			.then(() => contract.tokenSaleBalanceOf.call(accounts[1]))
			.then(function(result){
				assert.isTrue(
					result.equals(tokens),
					`${result.toString()} != ${tokens}`
				)
			})
	})
	
	it('should not permit a non-whitelisted account before the presale starts', function() {
        let contract = undefined;
		let tokenPrice = undefined;
		const now =  web3.eth.getBlock(web3.eth.blockNumber).timestamp;
		const targetRate = 8000
		const presaleStart = now + 50 * day
		const saleStart = now + 100 * day
		const investment = 10 * Math.pow(10, 18)

		return SkrillaToken.new(
			presaleStart,
			saleStart,
			accounts[4],
			accounts[5],
			accounts[6]
		)
			.then((result) => contract = result)
            .then(() => contract.buyTokens({
                from: accounts[1],
                value: investment
			}))
			.then(assert.fail)
			.catch((error) => {
				assert.include(
					error.message,
					'invalid opcode',
					'it should throw'
				)
			})
	})
	
	it('should not permit token purchase after the sale ends', function() {
        let contract = undefined;
		let tokenPrice = undefined;
		const now =  web3.eth.getBlock(web3.eth.blockNumber).timestamp;
		const investment = 10 * Math.pow(10, 18)

		return SkrillaToken.new(
			now - 100 * day,
			now - 14.1 * day,
			accounts[4],
			accounts[5],
			accounts[6]
		)
			.then((result) => contract = result)
            .then(() => contract.buyTokens({
                from: accounts[1],
                value: investment
			}))
			.then(assert.fail)
			.catch((error) => {
				assert.include(
					error.message,
					'invalid opcode',
					'it should throw'
				)
			})
	})

})

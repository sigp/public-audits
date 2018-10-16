const BigNumber = require("bignumber.js");
var SkrillaToken = artifacts.require('./SkrillaToken.sol')
var testHelpers = require("../testHelpers.js");

const day = 3600 * 24		// seconds in a day

contract('SkrillaToken (exchangeRates)', function(accounts) {

    const assertExchangeRate = function(presaleStart, saleStart, targetRate) {
        let contract = undefined;
		let tokenPrice = undefined;
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
            .then(() => contract.buyTokens({
                from: accounts[0],
                value: investment
			}))
			.then(() => contract.tokenSaleBalanceOf.call(accounts[0]))
			.then(function(result){
				assert.isTrue(
					result.equals(tokens),
					`${result.toString()} != ${tokens}`
				)
			})
			.then(() => testHelpers.setDate(saleStart + day * 28.1))
            .then(function() {
                return contract.withdraw({from: accounts[0]})
            })
            .then(function() {
                return contract.balanceOf.call(accounts[0]);
            })
            .then(function(result) {
                assert.strictEqual(
					result.toNumber(), 
					tokens,
					`${result.toString()} != ${tokens}`
				);
                return contract
            });
    }
    
	it('should return an exchange rate of 3000 SKR/ETH half a day after presale start', function() {
		const now =  web3.eth.getBlock(web3.eth.blockNumber).timestamp;

		return assertExchangeRate(
			now - 0.5 * day,
			now + 100 * day,
			3000
		)
	})
    
	it('should return an exchange rate of 2500 SKR/ETH one and a half a days after presale start', function() {
		const now =  web3.eth.getBlock(web3.eth.blockNumber).timestamp;

		return assertExchangeRate(
			now - 1.5 * day,
			now + 100 * day,
			2500
		)
	})
    
	it('should return an exchange rate of 2400 SKR/ETH half a day after sale start', function() {
		const now =  web3.eth.getBlock(web3.eth.blockNumber).timestamp;

		return assertExchangeRate(
			now - 100 * day,
			now - 0.5 * day,
			2400
		)
	})
	
	it('should return an exchange rate of 2200 SKR/ETH two days after sale start', function() {
		const now =  web3.eth.getBlock(web3.eth.blockNumber).timestamp;

		return assertExchangeRate(
			now - 100 * day,
			now - 2 * day,
			2200
		)
	})
	
	it('should return an exchange rate of 2000 SKR/ETH 8 days after sale start', function() {
		const now =  web3.eth.getBlock(web3.eth.blockNumber).timestamp;

		return assertExchangeRate(
			now - 100 * day,
			now - 8 * day,
			2000
		)
	})
	
	it('should allow a whitelisted exchange rate of 8000', function() {
        let contract = undefined;
		let tokenPrice = undefined;
		const now =  web3.eth.getBlock(web3.eth.blockNumber).timestamp;
		const presaleStart = now - 0.5 * day
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
			.then(() => testHelpers.setDate(saleStart + day * 28.1))
            .then(function() {
                return contract.withdraw({from: accounts[1]})
            })
            .then(function() {
                return contract.balanceOf.call(accounts[1]);
            })
            .then(function(result) {
                assert.strictEqual(
					result.toNumber(), 
					tokens,
					`${result.toString()} != ${tokens}`
				);
                return contract
            });
	})

})

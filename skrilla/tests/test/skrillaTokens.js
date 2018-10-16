const SkrillaToken = artifacts.require("./SkrillaToken.sol");
var testHelpers = require("../testHelpers.js");

contract('SkrillaToken (skrilla tokens)', function(accounts) {
	
	beforeEach(() => {
		return testHelpers.mineBlocks(1)
	})
    
	const deploy = function() {
        let contract = undefined;
		let tokenPrice = undefined;
		const day = 3600 * 24		// seconds in a day
		const now =  web3.eth.getBlock(web3.eth.blockNumber).timestamp;

		return SkrillaToken.new(
			now - 13 * day,
			now - 9 * day,
			accounts[4],
			accounts[5],
			accounts[6]
		)
			.then((result) => contract = result)
            .then(() => contract.buyTokens({
                from: accounts[1],
                value: (5 * Math.pow(10, 18)) / Math.pow(10, 6)
            }))
			.then(() => contract.tokenSaleBalanceOf.call(accounts[1]))
			.then(function(result){
				assert.isTrue(
					result.equals(10000)
				)
			})
			.then(() => testHelpers.setDate(now + day * 28))
            .then(function() {
                return contract.withdraw({from: accounts[1]})
            })
            .then(function() {
                return contract.balanceOf.call(accounts[1]);
            })
            .then(function(result) {
                assert.strictEqual(result.toNumber(), 10000);
                return contract
            });
    }
    
	it('the team address should receive 100 * Math.pow(10, 12) tokens', function() {
		return deploy()
            .then((contract) => {
				return contract.withdraw({from: accounts[4]})
					.then(() => contract)
			})
            .then((contract) => contract.balanceOf.call(accounts[4]))
            .then((result) => assert.strictEqual(result.toNumber(), 100 * Math.pow(10, 12)))
	})
	
	it('the growth address should receive 300 * Math.pow(10, 12) tokens', function() {
		return deploy()
            .then((contract) => {
				return contract.withdraw({from: accounts[5]})
					.then(() => contract)
			})
            .then((contract) => contract.balanceOf.call(accounts[5]))
            .then((result) => assert.strictEqual(result.toNumber(), 300 * Math.pow(10, 12)))
	})
	
	it('the withdraw address should receive 0 tokens', function() {
		return deploy()
            .then((contract) => {
				return contract.withdraw({from: accounts[6]})
					.then(() => contract)
			})
            .then((contract) => contract.balanceOf.call(accounts[6]))
            .then((result) => assert.strictEqual(result.toNumber(), 0))
	})
	
	it('the withdraw address should be able to retrieve the invested ETH', function() {
		const previousBalance = web3.eth.getBalance(accounts[6], web3.eth.blockNumber)

		return deploy()
            .then((contract) => contract.transferEth({from: accounts[0]}))
			.then(() => {
				const newBalance = web3.eth.getBalance(accounts[6], web3.eth.blockNumber) 
				assert.isTrue(
					newBalance.minus(previousBalance).equals(5 * Math.pow(10, 12))
				)
			})
	})

});

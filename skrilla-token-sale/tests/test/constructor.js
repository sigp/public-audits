const SkrillaToken = artifacts.require("./SkrillaToken.sol");

contract('SkrillaToken (constructor)', function(accounts) {
    
	it('the contract should deploy without errors', function() {
		const day = 3600 * 24		// seconds in a day
		const now =  web3.eth.getBlock(web3.eth.blockNumber).timestamp;

		return SkrillaToken.new(
			now,
			now + 4 * day,
			accounts[4],
			accounts[5],
			accounts[6]
		)
	})
	
	it('the contract should not deploy if saleStart is < 3 days after presaleStart', function() {
		const day = 3600 * 24		// seconds in a day
		const now =  web3.eth.getBlock(web3.eth.blockNumber).timestamp;

		return SkrillaToken.new(
			now,
			now + 3 * day - 1,
			accounts[4],
			accounts[5],
			accounts[6]
		)
			.then(assert.fail)
			.catch((error) => {
				assert.include(
					error.message,
					'invalid opcode',
					'it should throw'
				)
			})
	})


});

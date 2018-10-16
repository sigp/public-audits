const DecisionTokenSale = artifacts.require("./DecisionTokenSale.sol");
const DecisionToken = artifacts.require("./DecisionToken.sol");
var testHelpers = require("../testHelpers.js");

contract('DecisionTokenSale (transferOwnership)', function(accounts) {

	it("should not allow a non-owner to transfer ownership", function() {
		let future =  web3.eth.getBlock(web3.eth.blockNumber).timestamp + 600;

		const owner = accounts[0]
		const wallet = accounts[1]
		const nonOwner = accounts[2]

		assert(owner != nonOwner)

		return DecisionTokenSale.new(future, wallet, {from: owner})
			.then((contract) => contract.transferOwnership.call(wallet, {from: nonOwner}))
			.then(assert.fail)
			.catch((error) => {
				assert.include(
					error.message,
					'invalid opcode',
					'it should throw'
				)
			})
	});

	it("should allow an owner to transfer ownership", function() {
		let contract = undefined
		let future =  web3.eth.getBlock(web3.eth.blockNumber).timestamp + 600;

		const owner = accounts[0]
		const wallet = accounts[1]
		const newOwner = accounts[2]

		assert(owner != newOwner)

		return DecisionTokenSale.new(future, wallet, {from: owner})
			.then((result) => contract = result)
			.then(() => contract.transferOwnership(newOwner, {from: owner}))
			.then(() => contract.pendingOwner.call())
			.then((result) => assert.equal(result, newOwner))
			.then(() => contract.claimOwnership({from: newOwner}))
			.then(() => contract.owner.call())
			.then((result) => assert.equal(result, newOwner))
	});

});

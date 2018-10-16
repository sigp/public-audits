const DecisionTokenSale = artifacts.require("./DecisionTokenSale.sol");
const DecisionToken = artifacts.require("./DecisionToken.sol");
var BigNumber = require("bignumber.js");
var testHelpers = require("../testHelpers.js");


contract('ENTToken (standardToken)', function(accounts) {

    /**
     * Accounts:
     *     accounts[0] should have 7000 tokens
     */
    const deploy = function() {
		const day = 3600 * 24		// seconds in a day
		const blockNumber = web3.eth.blockNumber;
		const now =  web3.eth.getBlock(blockNumber).timestamp;
        
		let contract = undefined;
		let tokenContract = undefined;
		let tokenPrice = undefined;
    
		return DecisionTokenSale.new(now + day, accounts[4], {from: accounts[5]})
			.then((result) => contract = result)
			.then(() => testHelpers.setDate(now + (day * 1.1)))
			.then(() => contract.buyTokens({
				from: accounts[0],
				value: new BigNumber(2)
			}))
			.then(() => contract.token.call())
			.then((address) => tokenContract = DecisionToken.at(address))
			.then(() => tokenContract.balanceOf.call(accounts[0]))
			.then((balance) => {
				assert.equal(
					balance.toString(),
					new BigNumber(7000).toString()
				)
			})
			.then(() => contract.destroy({from: accounts[5]}))
			.then(() => testHelpers.setDate(now + (day * 20)))
			.then(() => tokenContract)
    }

    it('transfers: ether transfer should be reversed.', function() {
        var ctr
        return deploy().then(function(result) {
            ctr = result
            return web3.eth.sendTransaction({
                from: accounts[0],
                to: ctr.address,
                value: web3.toWei('10', 'Ether')
            })
        }).catch(function(result) {
            assert(true)
        }).catch((err) => {
            throw new Error(err)
        })
    })

    it('transfers: should transfer 7000 to accounts[1] with accounts[0] having 7000', function() {
        var ctr
        return deploy().then(function(result) {
            ctr = result
            return ctr.transfer(accounts[1], 7000, {
                from: accounts[0]
            })
        }).then(function(result) {
            return ctr.balanceOf.call(accounts[1])
        }).then(function(result) {
            assert.strictEqual(result.toNumber(), 7000)
        }).catch((err) => {
            throw new Error(err)
        })
    })

    it('transfers: throw when trying to transfer 7001 to accounts[1] with accounts[0] having 7000', function() {
        var ctr
        return deploy().then(function(result) {
            ctr = result
            return ctr.transfer.call(accounts[1], 7001, {
                from: accounts[0]
            })
        })
		.then(assert.fail)
		.catch(function(error) {
			assert.include(
				error.message, 
				'invalid opcode', 
				'it should throw'
			)
		})
    })

    it('transfers: should not allow zero-transfers', function() {
        var ctr
        return deploy().then(function(result) {
            ctr = result
            return ctr.transfer.call(accounts[1], 0, {
                from: accounts[0]
            })
        })
		.then(assert.fail)
		.catch(function(error) {
			assert.include(
				error.message, 
				'invalid opcode', 
				'it should throw'
			)
		})
    })

    // NOTE: testing uint256 wrapping is impossible in this standard token since you can't supply > 2^256 -1.

    // todo: transfer max amounts.

    // APPROVALS

    it('approvals: msg.sender should approve 100 to accounts[1]', function() {
        var ctr = null
        return deploy().then(function(result) {
            ctr = result
            return ctr.approve(accounts[1], 100, {
                from: accounts[0]
            })
        }).then(function(result) {
            return ctr.allowance.call(accounts[0], accounts[1])
        }).then(function(result) {
            assert.strictEqual(result.toNumber(), 100)
        }).catch((err) => {
            throw new Error(err)
        })
    })

    // bit overkill. But is for testing a bug
    it('approvals: msg.sender approves accounts[1] of 100 & withdraws 20 once.', function() {
        var ctr = null
        return deploy().then(function(result) {
            ctr = result
            return ctr.balanceOf.call(accounts[0])
        }).then(function(result) {
            assert.strictEqual(result.toNumber(), 7000)
            return ctr.approve(accounts[1], 100, {
                from: accounts[0]
            })
        }).then(function(result) {
            return ctr.balanceOf.call(accounts[2])
        }).then(function(result) {
            assert.strictEqual(result.toNumber(), 0)
            return ctr.allowance.call(accounts[0], accounts[1])
        }).then(function(result) {
            assert.strictEqual(result.toNumber(), 100)
            return ctr.transferFrom.call(accounts[0], accounts[2], 20, {
                from: accounts[1]
            })
        }).then(function(result) {
            return ctr.transferFrom(accounts[0], accounts[2], 20, {
                from: accounts[1]
            })
        }).then(function(result) {
            return ctr.allowance.call(accounts[0], accounts[1])
        }).then(function(result) {
            assert.strictEqual(result.toNumber(), 80)
            return ctr.balanceOf.call(accounts[2])
        }).then(function(result) {
            assert.strictEqual(result.toNumber(), 20)
            return ctr.balanceOf.call(accounts[0])
        }).then(function(result) {
            assert.strictEqual(result.toNumber(), 6980)
        }).catch((err) => {
            throw new Error(err)
        })
    })

    // should approve 100 of msg.sender & withdraw 50, twice. (should succeed)
    it('approvals: msg.sender approves accounts[1] of 100 & withdraws 20 twice.', function() {
        var ctr = null
        return deploy().then(function(result) {
            ctr = result
            return ctr.approve(accounts[1], 100, {
                from: accounts[0]
            })
        }).then(function(result) {
            return ctr.allowance.call(accounts[0], accounts[1])
        }).then(function(result) {
            assert.strictEqual(result.toNumber(), 100)
            return ctr.transferFrom(accounts[0], accounts[2], 20, {
                from: accounts[1]
            })
        }).then(function(result) {
            return ctr.allowance.call(accounts[0], accounts[1])
        }).then(function(result) {
            assert.strictEqual(result.toNumber(), 80)
            return ctr.balanceOf.call(accounts[2])
        }).then(function(result) {
            assert.strictEqual(result.toNumber(), 20)
            return ctr.balanceOf.call(accounts[0])
        }).then(function(result) {
            assert.strictEqual(result.toNumber(), 6980)
                // FIRST tx done.
                // onto next.
            return ctr.transferFrom(accounts[0], accounts[2], 20, {
                from: accounts[1]
            })
        }).then(function(result) {
            return ctr.allowance.call(accounts[0], accounts[1])
        }).then(function(result) {
            assert.strictEqual(result.toNumber(), 60)
            return ctr.balanceOf.call(accounts[2])
        }).then(function(result) {
            assert.strictEqual(result.toNumber(), 40)
            return ctr.balanceOf.call(accounts[0])
        }).then(function(result) {
            assert.strictEqual(result.toNumber(), 6960)
        }).catch((err) => {
            throw new Error(err)
        })
    })

    // should approve 100 of msg.sender & withdraw 50 & 60 (should fail).
    it('approvals: msg.sender approves accounts[1] of 100 & withdraws 50 & 60 (2nd tx should fail)', function() {
        var ctr = null
        return deploy().then(function(result) {
            ctr = result
            return ctr.approve(accounts[1], 100, {
                from: accounts[0]
            })
        }).then(function(result) {
            return ctr.allowance.call(accounts[0], accounts[1])
        }).then(function(result) {
            assert.strictEqual(result.toNumber(), 100)
            return ctr.transferFrom(accounts[0], accounts[2], 50, {
                from: accounts[1]
            })
        }).then(function(result) {
            return ctr.allowance.call(accounts[0], accounts[1])
        }).then(function(result) {
            assert.strictEqual(result.toNumber(), 50)
            return ctr.balanceOf.call(accounts[2])
        }).then(function(result) {
            assert.strictEqual(result.toNumber(), 50)
            return ctr.balanceOf.call(accounts[0])
        }).then(function(result) {
            assert.strictEqual(result.toNumber(), 6950)
                // FIRST tx done.
                // onto next.
            return ctr.transferFrom.call(accounts[0], accounts[2], 60, {
                from: accounts[1]
            })
        })
		.then(assert.fail)
		.catch(function(error) {
			assert.include(
				error.message, 
				'invalid opcode', 
				'it should throw'
			)
		})
    })

    it('approvals: attempt withdrawal from account with no allowance (should fail)', function() {
        var ctr = null
        return deploy().then(function(result) {
            ctr = result
            return ctr.transferFrom.call(accounts[0], accounts[2], 60, {
                from: accounts[1]
            })
        })
		.then(assert.fail)
		.catch(function(error) {
			assert.include(
				error.message, 
				'invalid opcode', 
				'it should throw'
			)
		})
    })

    it('approvals: allow accounts[1] 100 to withdraw from accounts[0]. Withdraw 60 and then approve 0 & attempt transfer and throw.', function() {
        var ctr = null
        return deploy().then(function(result) {
            ctr = result
            return ctr.approve(accounts[1], 100, {
                from: accounts[0]
            })
        }).then(function(result) {
            return ctr.transferFrom(accounts[0], accounts[2], 60, {
                from: accounts[1]
            })
        }).then(function(result) {
            return ctr.approve(accounts[1], 0, {
                from: accounts[0]
            })
        }).then(function(result) {
            return ctr.transferFrom.call(accounts[0], accounts[2], 10, {
                from: accounts[1]
            })
        })
		.then(assert.fail)
		.catch(function(error) {
			assert.include(
				error.message, 
				'invalid opcode', 
				'it should throw'
			)
		})
    })

    it('approvals: approve max (2^256 - 1)', function() {
        var ctr = null
        return deploy().then(function(result) {
            ctr = result
            return ctr.approve(accounts[1], '115792089237316195423570985008687907853269984665640564039457584007913129639935', {
                from: accounts[0]
            })
        }).then(function(result) {
            return ctr.allowance(accounts[0], accounts[1])
        }).then(function(result) {
            var match = result.equals('1.15792089237316195423570985008687907853269984665640564039457584007913129639935e+77')
            assert.isTrue(match)
        }).catch((err) => {
            throw new Error(err)
        })
    })

    it('events: should fire Transfer event properly', function() {
        var ctr = null
        return deploy()
            .then(function(result) {
                ctr = result
                return ctr.transfer(accounts[1], '2666', {
                    from: accounts[0]
                })
            }).then(function(result) {
                const transferLog = result.logs[0];
                assert.strictEqual(transferLog.args.from, accounts[0])
                assert.strictEqual(transferLog.args.to, accounts[1])
                assert.strictEqual(transferLog.args.value.toString(), '2666')
            }).catch((err) => {
                throw new Error(err)
            })
    })

    it('events: should fire Approval event properly', function() {
        var ctr = null
        return deploy()
            .then(function(result) {
                ctr = result
                return ctr.approve(accounts[1], '2666', {
                    from: accounts[0]
                })
            }).then(function(result) {
                const approvalLog = result.logs[0];
                assert.strictEqual(approvalLog.args.owner, accounts[0])
                assert.strictEqual(approvalLog.args.spender, accounts[1])
                assert.strictEqual(approvalLog.args.value.toString(), '2666')
            }).catch((err) => {
                throw new Error(err)
            })
    })

})

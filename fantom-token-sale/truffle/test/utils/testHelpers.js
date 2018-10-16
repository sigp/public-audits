var BigNumber = require("bignumber.js");

/**
 * Collection of Helper Function for Testing
*/


/**
 * Checks if the given string is an address
 *
 * @method isAddress
 * @param {String} address the given HEX adress
 * @return {Boolean}
*/
var isAddress = function (address) {
      if (!/^(0x)?[0-9a-f]{40}$/i.test(address)) {
          // check if it has the basic requirements of an address
          return false;
      } else if (/^(0x)?[0-9a-f]{40}$/.test(address) || /^(0x)?[0-9A-F]{40}$/.test(address)) {
          // If it's all small caps or all all caps, return true
          return true;
      } else {
          // Otherwise check each case
          return isChecksumAddress(address);
      }
  };

/**
 * Checks if the given string is a checksummed address
 *
 * @method isChecksumAddress
 * @param {String} address the given HEX adress
 * @return {Boolean}
*/
var isChecksumAddress = function (address) {
    // Check each case
    address = address.replace('0x','');
    var addressHash = sha3(address.toLowerCase());
    for (var i = 0; i < 40; i++ ) {
        // the nth letter should be uppercase if the nth digit of casemap is 1
        if ((parseInt(addressHash[i], 16) > 7 && address[i].toUpperCase() !== address[i]) || (parseInt(addressHash[i], 16) <= 7 && address[i].toLowerCase() !== address[i])) {
            return false;
        }
    }
    return true;
};

/* Assertion Helper Functions */
exports.assertVariable = function(contract, variable, value, message) {
        return variable.call()
            .then(function(result) {
                assert(result === value, message);
                return contract;
            });
    };

exports.assertEthAddress = function(contract, variable, variableName) {
        return variable.call()
            .then(function(address) {
                assert(isAddress(address), variableName + " should be an ethereum address");
                return contract;
            });
    };

exports.assertBigNumberVariable = function(contract, variable, value, message) {
        return variable.call()
            .then(function(result) {
                assert(result.equals(value), message + ' ' + result.toString() + ' != ' + value);
                return contract;
            });
    };

exports.assertBalanceOf = function(contract,address, value) {
        return contract.balanceOf.call(address)
            .then(function(result) {
                assert(result.equals(value), "balance of " + address + " should be as expected." + ' ' + result.toString() + ' != ' + value);
                return contract;
            })
          };

exports.assertBigNumberArrayVariable = function(contract, variable, i, value, message) {
        return variable.call(i)
            .then(function(result) {
                assert(result.equals(value), message + ' ' + result.toString() + ' != ' + value);
                return contract;
            });
    };

/*
 * Check for a throw
 */
exports.assertThrow = function(error) {
  assert.include(error.message, 'revert', 'expecting a throw/revert');
}

/*
 * Assert that an async call threw with a revert.
 */
exports.assertRevert = async promise => {
  try {
    await promise;
    assert.fail('Expected revert not received');
  } catch (error) {
    const revertFound = error.message.search('revert') >= 0;
    assert(revertFound, `Expected "revert", got ${error} instead`);
  }
};


/*
 * Check the ETH the sending account gained as a result
 * of the transaction. This is useful for calls which 
 * send the caller ETH, eg a 'sellTokenToEth' function.
 */
exports.ethReturned = async (promise , address) => {
	const balanceBefore = web3.eth.getBalance(address)
	const tx = await promise
	const txEthCost = web3.eth.gasPrice.times(tx.receipt.gasUsed)
		.times(5)		// I have no idea why this 5x is required
	return web3.eth.getBalance(address)
		.minus(balanceBefore.minus(txEthCost))
}

/*
 * Assert that `a` and `b` are equal to each other,
 * allowing for a `margin` of error as a percentage
 * of `b`.
 */
exports.withinPercentageOf = (a, b, percentage) => {
	ba = new BigNumber(a)
	bb = new BigNumber(b)
	bm = new BigNumber(percentage).dividedBy(100)
	return (ba.minus(bb).abs().lessThan(bb.times(bm)))
}


/*
* TestRPC Helper functions
*
* These are a collection of functions to move the date and block number
* of testRPC to verify contracts.
*/

/* Function to emulate block mining
* @param - count - The number of blocks to mine
*/
exports.mineBlocks = function(count) {
    const mine = function(c, callback) {
      web3.currentProvider.send({jsonrpc: "2.0", method: "evm_mine"}) 
      .then(() => {
      if (c > 1) {
        mine(c-1, callback);
      } else {
        callback()
      }
     });
      /*
        request({
            url: "http://localhost:8545",
            method: "POST",
            json: true,   // <--Very important!!!
            body: {
                jsonrpc: "2.0",
                method: "evm_mine"
            }
        }, function (error, response, body){
            if(c > 1) {
                mine(c -1, callback);
            } else {
                callback()
            }
        });
        */
    };
    return new Promise(function(resolve, reject) {
        mine(count, function() {
            resolve();
        })
    })
};

exports.mineOne = function() {
  web3.currentProvider.send({jsonrpc: "2.0", method: "evm_mine"})
}

/* TestRPC Snapshots
*
* Takes a snapshot of the current blockchain
*/
exports.takeSnapShot = async () => {
  let id = await web3.currentProvider.send({jsonrpc: "2.0", method: "evm_snapshot"});
  return id['result']
}

/*
* Reverts to a previous snapshot id.
* @param - snapshotId - The snapshot to revert to.
*/
exports.revertTestRPC = function(snapshotId){
  web3.currentProvider.send({jsonrpc: "2.0", method: "evm_revert", params: [snapshotId]})
}

/* Sets the date of the testRPC instance to a future datetime.
* @param - date - uint variable represenint a future datetime.
*/
exports.setDate = function(date) {
  // Get the current blocknumber.
  blockNumber = web3.eth.blockNumber;
  curTimeStamp  =  web3.eth.getBlock(blockNumber).timestamp;
  assert(date > curTimeStamp, "the modified date must be in the future");
  // Set the new time.
  deltaIncrease = date - curTimeStamp;
  web3.currentProvider.send({jsonrpc: "2.0", method: "evm_increaseTime", params: [deltaIncrease]})
	// mine a block to ensure we get a new timestamp
  web3.currentProvider.send({jsonrpc: "2.0", method: "evm_mine"})
};

exports.sleep = async (sleeptime) => {
  return new Promise((resolve) => {
    setTimeout(resolve, sleeptime)
  })
}

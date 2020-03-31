let BigNumber = require("bignumber.js");
const BN = require('bn.js');
let toBN = web3.utils.toBN;

/**
 * Collection of Helper Function for Testing
 */

/**
 * Sets default properties on the jsonrpc object and promisifies it so we don't have to copy/paste everywhere.
 * from https://github.com/Synthetixio/synthetix/blob/c6d26c1e47e7bede8f30372ee4a28798472de33f/test/utils/testUtils.js
 */
const send = payload => {
  if (!payload.jsonrpc) payload.jsonrpc = "2.0";
  if (!payload.id) payload.id = new Date().getTime();

  return new Promise((resolve, reject) => {
    web3.currentProvider.send(payload, (error, result) => {
      if (error) return reject(error);

      return resolve(result);
    });
  });
};

/*
 * Gets the timestamp of the latest block
 */
const timestamp = async function() {
  const blockNumber = await web3.eth.getBlockNumber();
  const block = await web3.eth.getBlock(blockNumber);
  // NOTE: this breaks for large timestamps as block.timestamp returns a number
  // see https://github.com/ethereum/web3.js/issues/1905
  // https://github.com/ethereum/web3.js/issues/3228
  // https://github.com/ethereum/web3.js/pull/3234
  return toBN(block.timestamp);
};
module.exports.timestamp = timestamp;

/**
 * Checks if the given string is an address
 *
 * @method isAddress
 * @param {String} address the given HEX adress
 * @return {Boolean}
 */
var isAddress = function(address) {
  if (!/^(0x)?[0-9a-f]{40}$/i.test(address)) {
    // check if it has the basic requirements of an address
    return false;
  } else if (
    /^(0x)?[0-9a-f]{40}$/.test(address) ||
    /^(0x)?[0-9A-F]{40}$/.test(address)
  ) {
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
var isChecksumAddress = function(address) {
  // Check each case
  address = address.replace("0x", "");
  var addressHash = web3.utils.sha3(address.toLowerCase());
  for (var i = 0; i < 40; i++) {
    // the nth letter should be uppercase if the nth digit of casemap is 1
    if (
      (parseInt(addressHash[i], 16) > 7 &&
        address[i].toUpperCase() !== address[i]) ||
      (parseInt(addressHash[i], 16) <= 7 &&
        address[i].toLowerCase() !== address[i])
    ) {
      return false;
    }
  }
  return true;
};

/* Assertion Helper Functions */
exports.assertVariable = function(contract, variable, value, message) {
  return variable.call().then(function(result) {
    assert(result === value, message);
    return contract;
  });
};

exports.assertEthAddress = function(contract, variable, variableName) {
  return variable.call().then(function(address) {
    assert(isAddress(address), variableName + " should be an ethereum address");
    return contract;
  });
};

exports.assertBigNumberVariable = function(contract, variable, value, message) {
  return variable.call().then(function(result) {
    assert(
      result.equals(value),
      message + " " + result.toString() + " != " + value
    );
    return contract;
  });
};

exports.assertBalanceOf = function(contract, address, value) {
  return contract.balanceOf.call(address).then(function(result) {
    assert(
      result.equals(value),
      "balance of " +
        address +
        " should be as expected." +
        " " +
        result.toString() +
        " != " +
        value
    );
    return contract;
  });
};

exports.assertBigNumberArrayVariable = function(
  contract,
  variable,
  i,
  value,
  message
) {
  return variable.call(i).then(function(result) {
    assert(
      result.equals(value),
      message + " " + result.toString() + " != " + value
    );
    return contract;
  });
};

/*
 * Check for a throw
 */
exports.assertThrow = function(error) {
  assert.include(error.message, "revert", "expecting a throw/revert");
};

/*
 * Assert that an async call threw with a revert.
 */
exports.assertRevert = async (promise, msg) => {
  try {
    await promise;
    assert.fail(`Expected revert not received: ${msg}`);
  } catch (error) {
    assert.include(
      error.message,
      "revert",
      `Expected "revert", got ${error.message} instead: "${msg}"`
    );
  }
};

/*
 * Check the ETH the sending account gained as a result
 * of the transaction. This is useful for calls which
 * send the caller ETH, eg a 'sellTokenToEth' function.
 */
exports.ethReturned = async (promise, address) => {
  const balanceBefore = web3.eth.getBalance(address);
  const tx = await promise;
  const txEthCost = web3.eth.gasPrice.times(tx.receipt.gasUsed).times(5); // I have no idea why this 5x is required
  return web3.eth.getBalance(address).minus(balanceBefore.minus(txEthCost));
};

/*
 * Assert that `a` and `b` are equal to each other,
 * allowing for a `margin` of error as a percentage
 * of `b`.
 */
exports.withinPercentageOf = (a, b, percentage) => {
  if (a === 0 && b === 0) {
    return true;
  }
  let ba = new BigNumber(a);
  let bb = new BigNumber(b);
  let bm = new BigNumber(percentage).dividedBy(100);
  return ba
    .minus(bb)
    .abs()
    .lessThan(bb.times(bm));
};

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
    web3.currentProvider
      .send({ jsonrpc: "2.0", method: "evm_mine" })
      .then(() => {
        if (c > 1) {
          mine(c - 1, callback);
        } else {
          callback();
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
    });
  });
};

exports.mineOne = () => send({ method: "evm_mine" });

/* TestRPC Snapshots
 *
 * Takes a snapshot of the current blockchain
 */
exports.takeSnapShot = async () => {
  const { result } = await send({ method: "evm_snapshot" });
  await exports.mineOne();
  return result;
};

/*
 * Reverts to a previous snapshot id.
 * @param - snapshotId - The snapshot to revert to.
 */
exports.revertTestRPC = async snapshotId => {
  await send({
    method: "evm_revert",
    params: [snapshotId]
  });
  await exports.mineOne();
};

/* Sets the date of the testRPC instance to a future datetime.
 * @param - date - uint variable represenint a future datetime.
 */
exports.setDate = async function(dateNumber) {
  // Get the current blocknumber.
  let blockNumber = await web3.eth.getBlockNumber();
  let block = await web3.eth.getBlock(blockNumber);
  let curTimeStamp = toBN((await web3.eth.getBlock(blockNumber)).timestamp);

  let date = toBN(dateNumber);
  assert(date.gt(curTimeStamp), "date must be in the future");

  // assert(date > curTimeStamp, 'the modified date must be in the future')
  // Set the new time.
  let deltaIncrease = date.sub(curTimeStamp);
  exports.increaseTime(deltaIncrease.toNumber());
  // mine a block to ensure we get a new timestamp
};

exports.increaseTime = async function(seconds) {
  await send({ method: "evm_increaseTime", params: [seconds] });
  await exports.mineOne();
};

exports.sleep = async sleeptime => {
  return new Promise(resolve => {
    setTimeout(resolve, sleeptime);
  });
};

exports.assertBNEqual = (actualBN, expectedBN, context) => {
  assert.equal(actualBN.toString(), expectedBN.toString(), context);
};

exports.toBigNumber = num => new BigNumber(web3.utils.numberToHex(num), 16);

exports.fastForward = async seconds => {
	// It's handy to be able to be able to pass big numbers in as we can just
	// query them from the contract, then send them back. If not changed to
	// a number, this causes much larger fast forwards than expected without error.
	if (BN.isBN(seconds)) seconds = seconds.toNumber();

	// And same with strings.
	if (typeof seconds === 'string') seconds = parseFloat(seconds);

	await send({
		method: 'evm_increaseTime',
		params: [seconds],
	});

	await mineBlock();
};

const mineBlock = () => send({ method: 'evm_mine' });

const assertBNEqual = (actualBN, expectedBN, context) => {
  assert.equal(actualBN.toString(), expectedBN.toString(), context);
};

exports.assertEventEqual = (actualEventOrTransaction, expectedEvent, expectedArgs) => {
	// If they pass in a whole transaction we need to extract the first log, otherwise we already have what we need
	const event = Array.isArray(actualEventOrTransaction.logs)
		? actualEventOrTransaction.logs[0]
		: actualEventOrTransaction;

	if (!event) {
		assert.fail(new Error('No event was generated from this transaction'));
	}

	// Assert the names are the same.
	assert.equal(event.event, expectedEvent);

	assertDeepEqual(event.args, expectedArgs);
	// Note: this means that if you don't assert args they'll pass regardless.
	// Ensure you pass in all the args you need to assert on.
};

const assertDeepEqual = (actual, expected, context) => {
	// Check if it's a value type we can assert on straight away.
	if (BN.isBN(actual) || BN.isBN(expected)) {
		assertBNEqual(actual, expected, context);
	} else if (
		typeof expected === 'string' ||
		typeof actual === 'string' ||
		typeof expected === 'number' ||
		typeof actual === 'number' ||
		typeof expected === 'boolean' ||
		typeof actual === 'boolean'
	) {
		assert.equal(actual, expected, context);
	}
	// Otherwise dig through the deeper object and recurse
	else if (Array.isArray(expected)) {
		for (let i = 0; i < expected.length; i++) {
			assertDeepEqual(actual[i], expected[i], `(array index: ${i}) `);
		}
	} else {
		for (const key of Object.keys(expected)) {
			assertDeepEqual(actual[key], expected[key], `(key: ${key}) `);
		}
	}
};
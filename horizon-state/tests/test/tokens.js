const DecisionTokenSale = artifacts.require("./DecisionTokenSale.sol");
const DecisionToken = artifacts.require("./DecisionToken.sol");
var BigNumber = require("bignumber.js");
var testHelpers = require("../testHelpers.js");

const decimals = 18;
const days = 3600*24; //seconds in a day

// Convert to the correct integer number of tokens.
const toDec = (x) => new BigNumber(x).times(Math.pow(10,decimals));

const valid = {
  tokenReserve: 4 * Math.pow(10,8) * Math.pow(10, decimals),
  tokenCap: Math.pow(10,9) * Math.pow(10,decimals)
 }

 const exchangeRates = {
    preSale: toDec(3750),
    earlyBird: toDec(3500),
    secondStage: toDec(3250),
    thirdStage: toDec(3000)
 }

 const testDeposits = {
   preSale: testHelpers.toWei(200),
   earlyBird: testHelpers.toWei(32.256),
   secondStage: testHelpers.toWei(0.00045),
   thirdStage: testHelpers.toWei(23),
 }
var weiDeposited  = [testDeposits.preSale, testDeposits.earlyBird, testDeposits.secondStage, testDeposits.thirdStage];
var exchangeRateArray  = [exchangeRates.preSale, exchangeRates.earlyBird, exchangeRates.secondStage, exchangeRates.thirdStage];

// Return the integer number of expected tokens.
var tokens = function(wei, exchangeRate){
  return Math.floor(testHelpers.fromWei(wei)*exchangeRate);
}

var expectedTokens = (x) => tokens(weiDeposited[x], exchangeRateArray[x]);

var purchaseTokens = function(accounts, saleStart, purchaseTime,weiDeposited, expectedTokens, msg) {

    it("should create " + expectedTokens + " from a " + testHelpers.fromWei(weiDeposited)  + " Eth deposit in the " + msg, function() {
    return DecisionTokenSale.new(saleStart,accounts[3])
      .then(function(contract){
          return contract.addWhiteListedAddressesInBatch([accounts[1], accounts[2]]).then(function() { return contract})
      })
      // Change the time
    .then(function(contract)
    {
      testHelpers.setDate(purchaseTime);
      return contract;
    })
      .then(function(contract){
        return contract.buyTokens({from: accounts[1], value: weiDeposited}).then(function(){return contract})
    })
    .then(function(contract)
    {
      return contract.token.call()
    })
    .then(function(address){
        const DT = DecisionToken.at(address);
        return testHelpers.assertBalanceOf(DT, accounts[1],expectedTokens);
    });
  });
}


contract('DecisionTokenSale (Create Tokens)', function(accounts) {

    var blockNumber = web3.eth.blockNumber;
    var curTimeStamp  =  web3.eth.getBlock(blockNumber).timestamp;
    var saleStart = curTimeStamp + 500*days;
    purchaseTokens(accounts, saleStart, saleStart - 0.1*days, weiDeposited[0], expectedTokens(0), "pre-sale");
    purchaseTokens(accounts, saleStart, saleStart + 0.1*days, weiDeposited[1], expectedTokens(1), "first day");
    saleStart = saleStart + 2*days;
    purchaseTokens(accounts, saleStart, saleStart + 1.1*days, weiDeposited[2], expectedTokens(2), "second stage");
    saleStart = saleStart + 2*days;
    purchaseTokens(accounts, saleStart, saleStart + 12*days, weiDeposited[3], expectedTokens(3), "third stage");


    it("should not allow purchases after 14 days", function() {
      let contract = undefined;
      var blockNumber = web3.eth.blockNumber;
      var curTimeStamp  =  web3.eth.getBlock(blockNumber).timestamp;
      var saleStart = curTimeStamp;
      return DecisionTokenSale.new(saleStart,accounts[3])
      .then((result) => contract = result)
      .then(() =>       contract.addWhiteListedAddressesInBatch([accounts[1], accounts[2]]))
      // Change the time
    .then(() =>  testHelpers.setDate(saleStart + 14*days))
    .then(() => contract.buyTokens({from: accounts[1], value: 5000}))
    .catch(function(error) {
            assert.include(
                error.message,
                'invalid opcode',
                'it should throw'
            )
    });
  });

    it("should not allow more than " + valid.tokenCap + " tokens to be produced.", function() {
      let contract = undefined;
      let tokenContract = undefined;
  		let future =  web3.eth.getBlock(web3.eth.blockNumber).timestamp + 600;

      let preSaleInvestment = 5000; // ETH = 3750*5000 = 1,875,000
      let earlyBirdInvestment = 10000; // ETH = 3500*10000 = 35,000,000
      let secondStageInvestment = 20000; // ETH = 3250*200000 = 65,000,000
      let thirdStageInvestment = 160416.666; // ETH = 481,250,000

      let finalNotAllowedInvestment = 0.001; // Already hit the total. This should fail.

      return DecisionTokenSale.new(future,accounts[0])
      .then((result) => contract = result)
			.then(() => contract.token.call())
      .then((result) => tokenContract = DecisionToken.at(result))
      .then(() => contract.addWhiteListedAddressesInBatch([accounts[1], accounts[2]]))
      .then(() => contract.buyTokens({from: accounts[1], value: web3.toWei(preSaleInvestment)}))
      .then(() => testHelpers.setDate(future + 0.2*days))
      .then(() => contract.buyTokens({from: accounts[3], value: web3.toWei(earlyBirdInvestment)}))
      .then(() => testHelpers.setDate(future + 1.2*days))
      .then(() => contract.buyTokens({from: accounts[3], value: web3.toWei(secondStageInvestment)}))
      .then(() => testHelpers.setDate(future + 9*days))
      .then(() => contract.buyTokens({from: accounts[3], value: web3.toWei(thirdStageInvestment)}))
			.then(() => tokenContract.totalSupply.call())
			.then((result) => assert(result.toNumber() > 0.99*valid.tokenCap && result.toNumber() <= valid.tokenCap), "should approach the token cap")
      .then(() => {
        return contract.buyTokens({from: accounts[1], value: web3.toWei(finalNotAllowedInvestment)})
          .catch(() => Promise.reject('intentionalFail'))
      })
      .catch(function(error) {
            assert.equal(
                error,
                'intentionalFail'
            )
    });
  });

});

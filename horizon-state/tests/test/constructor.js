const DecisionTokenSale = artifacts.require("./DecisionTokenSale.sol");
const DecisionToken = artifacts.require("./DecisionToken.sol");

var testHelpers = require("../testHelpers.js");
var blockNumber = web3.eth.blockNumber;
var curTimeStamp  =  web3.eth.getBlock(blockNumber).timestamp;

const decimals = 18;

const valid = {
  saleStart: curTimeStamp + 24*3600*500,
  tokenReserve: 4 * Math.pow(10,8) * Math.pow(10, decimals)
 }

contract('DecisionTokenSale (constructor)', function(accounts) {
    assert(web3.eth.getBlock(web3.eth.blockNumber).timestamp < valid.saleStart, "the time should be before the sale start date.");


    it("should create a new token contract", function() {
      return DecisionTokenSale.new(valid.saleStart,accounts[0])
        .then(function(contract){
            return testHelpers.assertEthAddress(contract, contract.token, "token")
        });
    });

    it("should give reserve tokens to the owner", function() {
      return DecisionTokenSale.new(valid.saleStart,accounts[0])
        .then(function(contract){
            return contract.token.call()
        .then(function(address){
            const DT = DecisionToken.at(address);
            return testHelpers.assertBalanceOf(DT, accounts[0], valid.tokenReserve);
          })
        });
    });


});

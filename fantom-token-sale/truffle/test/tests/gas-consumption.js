const th = require('../utils/testHelpers');
const deployer = require('../utils/deployer.js')
const BigNumber = require('bignumber.js')
const Fantom = artifacts.require('./FantomToken.sol')

// extra global variables
const assertRevert = th.assertRevert;
const blockGasLimit = 8e6;
const days = 3600*24
const timestamp = () => new BigNumber(web3.eth.getBlock(web3.eth.blockNumber).timestamp);

const assignTokens = async function(token, to, amount, owner) {
  await token.addToWhitelist(to, { from: owner });
  await token.mintTokens(1, to, amount, {from: owner});
}

// Setup a function to test gas usage for many Locked Tokens minting
var testMintLockedTokens = function(numberOfAccounts, accounts) { 

  it(`[MintTokensLockedMultiple] should cost less than the block gas limit for ${numberOfAccounts} accounts`, async () => {
    // Use the modified contract as date needs to be dynamic
    let deployedObject = await deployer.setupContract(accounts);
    let deployed = deployedObject.fantom;

    // owner to mint tokens. 
    // set the lock time to the  current time plus 3 days
    let lockTime = timestamp().plus(3 * days)
    let amountOfTokensToLock = 10e5
    let mintType = 1
    let account = deployedObject.owner // this should already be whitelisted
    // white list the owner
    await deployed.addToWhitelist(account, {from: deployedObject.owner})
    
    let accountList = []
    let amounts = []
    let lockTimeList = []

    for (i=0; i< numberOfAccounts; i++) { 
      accountList.push(account);
      amounts.push(amountOfTokensToLock* (i+1)*10e5);
      lockTimeList.push(lockTime);
    }

    let tx = await deployed.mintTokensLockedMultiple(mintType, accountList, amounts, lockTimeList)

    assert.isBelow(tx.receipt.gasUsed, blockGasLimit)
    console.log(`Minting locked tokens for ${numberOfAccounts} accounts.  Gas Estimate: ${tx.receipt.gasUsed}`);

})

}

// Setup a function to test for multiple transfers
var testTransferMultiple = function(numberOfAccounts, accounts) { 

  it(`[TransferMultiple] should cost less than the block gas limit for ${numberOfAccounts} accounts`, async () => {
    // set up balances 
    let contract = await deployer.setupContract(accounts);
		let deployed = contract.fantom;
    let owner = contract.owner
		assert(owner === contract.owner);
		await assignTokens(deployed, owner, 100e7, owner);
		await th.setDate(contract.ICOEndTime + 1);
		await deployed.makeTradeable();

    // build account list
    let accountList = []
    let amounts = []

    for (i=0; i< numberOfAccounts; i++) { 
      accountList.push(accounts[1]);
      amounts.push((i)*1e5);
    }

    let tx = await deployed.transferMultiple(accountList, amounts)

    assert.isBelow(tx.receipt.gasUsed, blockGasLimit)
    console.log(`Multiple transfer to ${numberOfAccounts} accounts.  Gas Estimate: ${tx.receipt.gasUsed}`);

})

  }

contract('Gas Consumption Tests (optimized-runs = 200)', (accounts) => {

  it("Deployment of contract gas estimate", async ()  => { 
    // Use the modified contract as date needs to be dynamic
    let deployedObject = await deployer.setupContract(accounts);
    let deployed = deployedObject.fantom;
    let receipt = await web3.eth.getTransactionReceipt(deployed.transactionHash); 

    it("should cost less than the block gas limit to deploy", () => {
      assert.isBelow(receipt.gasUsed, blockGasLimit)
    })
  console.log("Deployment Gas Estimate: " + receipt.gasUsed);
      
  });

  it("should cost less than the block gas limit to buy tokens (optimize-runs = 200)", async ()  => { 

    let deployedObject = await deployer.setupContract(accounts);
    let deployed = deployedObject.fantom;
    let account = deployedObject.owner // this should already be whitelisted
    // white list the owner
    await deployed.addToWhitelist(account, {from: deployedObject.owner})

    // set the time into the ICO Start time
		await th.setDate(deployedObject.ICOStartTime + 0.2*days);
    
    let tx = await deployed.sendTransaction({from: account, value: web3.toWei(2,"ether")});
    assert.isBelow(tx.receipt.gasUsed, blockGasLimit)
    console.log("Buy Tokens Gas Estimate: " +  tx.receipt.gasUsed);
   });

  it("should cost less than the block gas limit to mint tokens (optimize-runs = 200)", async ()  => { 
    // Use the modified contract as date needs to be dynamic
    let deployedObject = await deployer.setupContract(accounts);
    let deployed = deployedObject.fantom;

    // owner to mint tokens. 
    // set the lock time to the  current time plus 3 days
    let lockTime = timestamp().plus(3 * days)
    let amountOfTokensToLock = 10
    let mintType = 1
    let account = deployedObject.owner // this should already be whitelisted

    // white list the owner
    await deployed.addToWhitelist(account, {from: deployedObject.owner})
    
    let tx = await deployed.mintTokensLocked(mintType, account, amountOfTokensToLock, lockTime)

    assert.isBelow(tx.receipt.gasUsed, blockGasLimit)
    console.log("Minting Locked Tokens Gas Estimate: " +  tx.receipt.gasUsed);
   });
  
   // test the gas costs of minting to mulitple users 
   testMintLockedTokens(2,accounts)  
   testMintLockedTokens(5,accounts)  
   testMintLockedTokens(10,accounts)  
   testMintLockedTokens(15,accounts)  
   testMintLockedTokens(20,accounts)  
   testMintLockedTokens(30,accounts)  
   testMintLockedTokens(50,accounts)  
   
   // test the gas costs of multiple transfers
   testTransferMultiple(2,accounts)  
   testTransferMultiple(5,accounts)  
   testTransferMultiple(10,accounts)  
   testTransferMultiple(15,accounts)  
   testTransferMultiple(20,accounts)  
   testTransferMultiple(30,accounts)  
   testTransferMultiple(50,accounts)  
});

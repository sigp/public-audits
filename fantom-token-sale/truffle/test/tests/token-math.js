const BigNumber = require("bignumber.js")
const helpers = require('../utils/testHelpers.js')
const deployer = require('../utils/deployer.js')

const decimals = 1e18
const timestamp = () => new BigNumber(web3.eth.getBlock(web3.eth.blockNumber).timestamp)
const tokenRate = new BigNumber(15000)
const tokenSupply = new BigNumber(3175000000*decimals)
const minContrib = new BigNumber(0.2*decimals)
const tokenMainCap = new BigNumber(50000000*decimals)
const mainLimit = 100

const sendEther = (contract, account, etherAmount) => { 
    let weiSent = etherAmount*decimals
    return contract.sendTransaction({from:account, value: weiSent}); 
}

contract('[FantomToken - Token Math]', function(accounts) {

  it('should have the correct caps', async function() { 
    let contract = await deployer.setupContract(accounts)
    let fantom = contract.fantom

    let actualTS = await fantom.MAX_TOTAL_TOKEN_SUPPLY.call()
    let actualTMC = await fantom.TOKEN_MAIN_CAP.call()
    let actualMC = await fantom.MINIMUM_CONTRIBUTION.call()

    assert(tokenSupply.cmp(actualTS) == 0, `TS || Expected: ${tokenSupply}; Got: ${actualTS}`)
    assert(minContrib.cmp(actualMC) == 0, `MC || Expected: ${minContrib}; Got: ${actualMC}`)
    assert(tokenMainCap.cmp(actualTMC) == 0, `TMC || Expected: ${tokenMainCap}; Got: ${actualTMC}`)
  })

it('should have a correct token rate for 1 ether', async function() { 
  let contract = await deployer.setupContract(accounts)
  let fantom = contract.fantom
  let owner = contract.owner

  // white list account
  await fantom.addToWhitelist(accounts[1], {from: owner})
  icodate = contract.ICOStartTime + 200 
  await helpers.setDate(icodate)

  let etherSent = 1
  let weiSent = etherSent*decimals
  
  await fantom.sendTransaction({from:accounts[1], value: weiSent}); 
  let expectedTokens = tokenRate*etherSent*decimals

  let actualTokens = await fantom.balanceOf(accounts[1]);
  assert.equal(expectedTokens,actualTokens.toNumber())

})

it('should not give more tokens than allowed during first day', async function() { 
  let contract = await deployer.setupContract(accounts)
  let fantom = contract.fantom
  let owner = contract.owner

  // white list account
  await fantom.addToWhitelist(accounts[1], {from: owner})
  icodate = contract.ICOStartTime + 2000 
  await helpers.setDate(icodate)
  
  let tokenLimit = await fantom.firstDayTokenLimit()
  let ethLimit = tokenLimit/tokenRate/decimals
  let etherSent = ethLimit + 0.001
  let weiSent = etherSent*decimals
  
  await fantom.sendTransaction({from:accounts[1], value: weiSent}); 
  let expectedTokens = new BigNumber(mainLimit*decimals).mul(new BigNumber(15000))

  let actualTokens = await fantom.balanceOf(accounts[1]);
  assert(expectedTokens.cmp(actualTokens) == 0,
          `Expected: ${expectedTokens}; Got: ${actualTokens}`)
})

it('a user should not be able to purchase more than the token limit in the first day', async function() { 
  let contract = await deployer.setupContract(accounts)
  let fantom = contract.fantom
  let owner = contract.owner

  // white list account
  await fantom.addToWhitelist(accounts[1], {from: owner})
  icodate = contract.ICOStartTime + 2000 
  await helpers.setDate(icodate)
  
  let tokenLimit = await fantom.firstDayTokenLimit()
  let ethLimit = tokenLimit/tokenRate/decimals
  let etherSent = ethLimit + 0.001
  let weiSent = etherSent*decimals
 
  // send more than the maximum
  await fantom.sendTransaction({from:accounts[1], value: weiSent}); 
  // then send more 
  helpers.assertRevert(fantom.sendTransaction({from:accounts[1], value: weiSent}))
})

it('should purchase correct amount of tokens if all whitelisted users purchase tokens', async function() { 
  let contract = await deployer.setupContract(accounts)
  let fantom = contract.fantom
  let owner = contract.owner

  // white list account
  await fantom.addToWhitelist(accounts[1], {from: owner})
  await fantom.addToWhitelist(accounts[2], {from: owner})
  await fantom.addToWhitelist(accounts[3], {from: owner})
  await fantom.addToWhitelist(accounts[4], {from: owner})
  await fantom.addToWhitelist(accounts[5], {from: owner})

  icodate = contract.ICOStartTime + 2000 
  await helpers.setDate(icodate)
  
  // let whitelisted = await fantom.numberWhitelisted.call()
  // let tokenLimit = tokenMainCap/whitelisted
  let tokenLimit = await fantom.firstDayTokenLimit()
  let ethLimit = tokenLimit/tokenRate/decimals
  let etherSent = ethLimit + 0.001
  let weiSent = etherSent*decimals
 
  // send more than the maximum
  await fantom.sendTransaction({from:accounts[1], value: weiSent}); 
  await fantom.sendTransaction({from:accounts[2], value: weiSent}); 
  await fantom.sendTransaction({from:accounts[3], value: weiSent}); 
  await fantom.sendTransaction({from:accounts[4], value: weiSent}); 
  await fantom.sendTransaction({from:accounts[5], value: weiSent}); 

  let actualTokens = await fantom.totalSupply();
  let expectedTokens = new BigNumber(mainLimit * decimals).mul(tokenRate).mul(5)

  assert(expectedTokens.cmp(actualTokens) == 0,
        `Expected: ${expectedTokens}; Got: ${actualTokens}`)
})


it('[Scenario.1] should give the correct token amounts for scenario 1', async function() { 

  let contract = await deployer.setupContract(accounts)
  let fantom = contract.fantom
  let owner = contract.owner

  // white list account
  await fantom.addToWhitelist(accounts[1], {from: owner})
  await fantom.addToWhitelist(accounts[2], {from: owner})
  await fantom.addToWhitelist(accounts[3], {from: owner})
  await fantom.addToWhitelist(accounts[4], {from: owner})
  await fantom.addToWhitelist(accounts[5], {from: owner})
  // set start time
  let icodate = contract.ICOStartTime + 2000 
  await helpers.setDate(icodate)

  // list of ether to be sent
  ethSent = [0, 130, 0.3, 0.6,12,2]
  expectedReturns = [0, mainLimit, 0.3, 0.6,12,2]
  // list of tokens we expect as a result
  expectedTokens = expectedReturns.map(x => x*tokenRate*decimals)

  // account 1 spends 30 eth during first day
  await sendEther(fantom, accounts[1], ethSent[1])
  // account 2 spends 176 eth during first day
  await sendEther(fantom, accounts[2], ethSent[2])
  // account 3 spends 1000 eth during first day
  await sendEther(fantom, accounts[3], ethSent[3])

  // Move to after the first day
  await helpers.setDate(contract.ICOStartTime+ 3600*24*2)

  // account 4 spends 12 eth after the first day
  await sendEther(fantom, accounts[4], 12)
  // account 5 spends 2 eth after the first day
  await sendEther(fantom, accounts[5], 2)

  actualTokenBalances = [0] 
  for (i=1; i<=5; i++) { 
    actualTokenBalances.push((await fantom.balanceOf(accounts[i])).toNumber());
  }

  for (i=1; i<=5; i++) { 
    assert(expectedTokens[i] == actualTokenBalances[i],
      `${i}: token balances are not as expected: ` +
      `Expected:${expectedTokens[i]};` + 
      `Got: ${actualTokenBalances[i]}`)
  }
})

it('[Scenario 2] should give the correct token amounts for scenario 1', async function() { 

  let contract = await deployer.setupContract(accounts)
  let fantom = contract.fantom
  let owner = contract.owner

  // white list account
  await fantom.addToWhitelist(accounts[1], {from: owner})
  await fantom.addToWhitelist(accounts[2], {from: owner})
  await fantom.addToWhitelist(accounts[3], {from: owner})
  await fantom.addToWhitelist(accounts[4], {from: owner})
  await fantom.addToWhitelist(accounts[5], {from: owner})
  // set start time
  let icodate = contract.ICOStartTime + 2000 
  await helpers.setDate(icodate)

  // list of ether to be sent
  ethSent = [10e6, 176, 1e3,12,2]
  expectedReturns = [mainLimit, mainLimit, mainLimit, 12, 2]
  // list of tokens we expect as a result
  expectedTokens = expectedReturns.map(x => x*tokenRate*decimals)

  // account 1 spends 10e6 eth during first day
  await sendEther(fantom, accounts[1], ethSent[0])
  // account 2 spends 176 eth during first day
  await sendEther(fantom, accounts[2], ethSent[1])
  // account 3 spends 1000 eth during first day
  await sendEther(fantom, accounts[3], ethSent[2])

  // Move to after the first day
  await helpers.setDate(contract.ICOStartTime+ 3600*24*2)

  // account 4 spends 12 eth after the first day
  await sendEther(fantom, accounts[4], ethSent[3])
  // account 5 spends 2 eth after the first day
  await sendEther(fantom, accounts[5], ethSent[4])

  actualTokenBalances = [] 
  for (i=1; i<=5; i++) { 
    actualTokenBalances.push((await fantom.balanceOf(accounts[i])).toNumber());
  }

  for (i=0; i<5; i++) { 
    assert(expectedTokens[i] == actualTokenBalances[i], `token balance for account ${i+1} is not as expected: expected ${expectedTokens[i]} got: ${actualTokenBalances[i]}`)
  }
})

})


const BigNumber = require("bignumber.js")
const th = require('../utils/testHelpers');
const deployer = require('../utils/deployer.js')
const assertRevert = th.assertRevert;

contract('Token Sale', function (accounts) {
	const ZERO_ADDRESS = '0x0000000000000000000000000000000000000000';
	const owner = accounts[0];
	const recipient = accounts[1];
	const anotherAccount = accounts[2];
	const yetAnotherAccount = accounts[3];
	const evenYetAnotherAccount = accounts[4];

  beforeEach(async function () {
    let contract = await deployer.setupContract(accounts);
		this.token = contract.fantom;
    this.IcoStartDate = contract.ICOStartTime;
		assert(owner === contract.owner);
  });

	describe('when the tokensale gets completed the first day', function () {
        it('reverts when there is no more tokens to buy and total cap is purchased', async function () {
          let tokensPerEth = (await this.token.tokensPerEth.call())
          let maxFirstDay = (await this.token.MAXIMUM_FIRST_DAY_CONTRIBUTION.call())
          let totalTokenCap = await this.token.TOKEN_MAIN_CAP.call()
          let numberOfPeopleRequired = totalTokenCap/tokensPerEth/maxFirstDay;
          await th.setDate(this.IcoStartDate+ 100);
          let weiSent = maxFirstDay*1.1 
          let totalTokens = new BigNumber(0);
          let currentBalance = 0;

          for (i=0; i< numberOfPeopleRequired-1; i++){
            await this.token.addToWhitelist(accounts[i], {from: owner})
            await this.token.sendTransaction({from: accounts[i], value: weiSent});
            currentBalance = await this.token.balanceOf(accounts[i]) 
						assert.equal(currentBalance,tokensPerEth*maxFirstDay);
            totalTokens = totalTokens.add(currentBalance);
          }
          await this.token.addToWhitelist(accounts[i+1], {from: owner})
          await this.token.sendTransaction({from:accounts[i+1], value: maxFirstDay*1.1});
          currentBalance = await this.token.balanceOf(accounts[i+1]) 
          totalTokens = totalTokens.add(currentBalance);

          assert.equal(totalTokens.toNumber(), totalTokenCap.toNumber())
          // Any further should revert
          await this.token.addToWhitelist(accounts[i+1], {from: owner})
          await assertRevert(this.token.sendTransaction({from:accounts[i+1], value: maxFirstDay*1.1}));
        });
      });

	describe('when the tokensale gets completed after the first day', function () {
        it('reverts when there is no more tokens to buy and total cap is purchased', async function () {
          let tokensPerEth = (await this.token.tokensPerEth.call())
          let maxFirstDay = (await this.token.MAXIMUM_FIRST_DAY_CONTRIBUTION.call())
          let totalTokenCap = await this.token.TOKEN_MAIN_CAP.call()
          let weiSent = 100 * 1e18 
          let numberOfPeopleRequired = totalTokenCap/tokensPerEth/weiSent;
          await th.setDate(this.IcoStartDate + 100 + 3600*24*2);
          let totalTokens = new BigNumber(0);
          let currentBalance = 0;

          for (i=0; i< numberOfPeopleRequired-1; i++){
            await this.token.addToWhitelist(accounts[i], {from: owner})
            await this.token.sendTransaction({from: accounts[i], value: weiSent});
            currentBalance = await this.token.balanceOf(accounts[i]) 
						assert.equal(currentBalance,tokensPerEth*weiSent);
            totalTokens = totalTokens.add(currentBalance);
          }
          await this.token.addToWhitelist(accounts[i+1], {from: owner})
          await this.token.sendTransaction({from:accounts[i+1], value: maxFirstDay*1.1});
          currentBalance = await this.token.balanceOf(accounts[i+1]) 
          totalTokens = totalTokens.add(currentBalance);

          assert.equal(totalTokens.toNumber(), totalTokenCap.toNumber())
          // Any further should revert
          await this.token.addToWhitelist(accounts[i+1], {from: owner})
          await assertRevert(this.token.sendTransaction({from:accounts[i+1], value: weiSent}));
        });
      });

});

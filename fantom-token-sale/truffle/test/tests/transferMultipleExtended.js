/*
 * These tests were adapted from the OpenZepplin repository here:
 *
 * https://github.com/OpenZeppelin/openzeppelin-solidity
 */

const th = require('../utils/testHelpers');
const deployer = require('../utils/deployer.js')
const assertRevert = th.assertRevert;

contract('StandardToken TransferMultiple Extended', function (accounts) {
	const ZERO_ADDRESS = '0x0000000000000000000000000000000000000000';
	const owner = accounts[0];
	const recipient = accounts[1];
	const anotherAccount = accounts[2];
	const yetAnotherAccount = accounts[3];
	const evenYetAnotherAccount = accounts[4];
	const mintType = 1;
	const assignTokens = async function(token, to, amount) {
		await token.addToWhitelist(to, { from: owner });
		await token.mintTokens(mintType, to, 100, {from: owner});
	}
	const assignTokensLocked = async function(token, to, amount, lockTime) {
		await token.addToWhitelist(to, { from: owner });
		await token.mintTokensLocked(mintType, to, 100, lockTime, {from: owner});
	}

  beforeEach(async function () {
    let contract = await deployer.setupContract(accounts);
		this.token = contract.fantom;
		assert(owner === contract.owner);
		await assignTokens(this.token, owner, 100);
    await assignTokensLocked(this.token,owner, 100, contract.ICOEndTime + 3600*24*10);
		await th.setDate(contract.ICOEndTime + 1);
  });

    describe('when tokens are not tradeable', function () {
			const to = [recipient, anotherAccount, yetAnotherAccount, evenYetAnotherAccount];
			const amount = [25, 25, 25, 25]

        it('reverts', async function () {
          await assertRevert(this.token.transferMultiple(to, amount, { from: owner }));
      });
    });

    describe('when the sender has enough unlocked balance', function () {
			const to = [recipient, anotherAccount, yetAnotherAccount, evenYetAnotherAccount];
			const amount = [25, 25, 25, 25]

      it('transfers the requested amount', async function () {
        await this.token.makeTradeable();
        await this.token.transferMultiple(to, amount, { from: owner });

        const senderBalance = await this.token.balanceOf(owner);
        assert.equal(senderBalance.toNumber(), 100);

        for(var i = 0; i < to.length; i++) {
          assert.equal(await this.token.balanceOf(to[i]), amount[i]);
        }
      });

      it('emits a transfer event', async function () {
        await this.token.makeTradeable();
        const { logs } = await this.token.transferMultiple(to, amount, { from: owner });
        
        assert.equal(logs.length, to.length);
        for(var i = 0; i < to.length; i++) {
          assert.equal(logs[i].event, 'Transfer');
          assert.equal(logs[i].args._from, owner);
          assert.equal(logs[i].args._to, to[i]);
          assert(logs[i].args._value.eq(amount[i]));
        }
      });
    });

    describe('when the sender doesn\'t have  enough unlocked balance', async function () {
			const to = [recipient, anotherAccount, yetAnotherAccount, evenYetAnotherAccount];
			const tooMuch = [50, 50, 25, 25]

        it('reverts', async function () {
          await this.token.makeTradeable();
          await assertRevert(this.token.transferMultiple(to, tooMuch, { from: owner }));
      });
  });


});

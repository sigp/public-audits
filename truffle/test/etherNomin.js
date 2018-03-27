const deployer = require('../deployer.js')
const BigNumber = require("bignumber.js")

const Court = artifacts.require('./Court.sol')
const Havven = artifacts.require('./Havven.sol')
const EtherNomin = artifacts.require('./EtherNomin.sol')
const HavvenEscrow = artifacts.require('./HavvenEscrow.sol')

const helpers = require('../testHelpers.js')
const assertRevert = helpers.assertRevert

/*
 * Multiply a number by the value of UNIT in the
 * smart contract's safe math.
 */
const toUnit = (x) => new BigNumber(x).times(Math.pow(10, 18))
assert(toUnit(3).toString() === "3000000000000000000", 'toUnit() is wrong')
/*
 * Return the amount of seconds in x days
 */
const days = (x) => x * 60 * 60 * 24
assert(days(2) === 172800, 'days() is wrong')
/*
 * Return the timestamp of the current block
 */
const timestamp = () => new BigNumber(web3.eth.getBlock(web3.eth.blockNumber).timestamp)


/*
 * It is assumed that all integers are to be multipled by the
 * UNIT constant, which is 10**18.
 */
contract('EtherNomin basic functionality', function(accounts) {
  
	/*
	 * constructor
	 */
	it("should use the values supplied in the constructor", async function() {
		const havven = accounts[1]
		const oracle = accounts[2]
		const beneficiary = accounts[3]
		const targetPrice = 1000 
		const owner = accounts[4]
		
		const c = await EtherNomin.new(
			havven,
			oracle,
			beneficiary,
			targetPrice,
			owner
		)
		
		assert(await c.feeAuthority.call() == havven, 'feeAuthority is not as set')
		assert(await c.oracle.call() == oracle, 'oracle is not as set')
		assert(await c.beneficiary.call() == beneficiary, 'beneficiary is not as set') 
		assert(await c.etherPrice.call() == targetPrice, 'price is not as set')
		assert(await c.owner.call() == owner, 'owner is not as set')
  });

	
	/*
	 * fiatValue()
	 */
	it("should return 4500 from a fiatValue(4.5) call if etherPrice is 1000", async function() {
		const price = toUnit(1000)
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			accounts[4]
		) 
		assert(price.eq(await c.etherPrice.call()), 'price is not as expected')
		assert(toUnit(4500).eq(await c.fiatValue(toUnit(4.5))), 'fiatValue() did not return as expected')
  });

	
	/*
	 * fiatBalance()
	 */
	it("should return a fiatBalance of 2000 if etherPrice is 1000 and the contract holds 2 ETH", async function() {
		const price = toUnit(1000)
		const value = new BigNumber(web3.toWei(2, 'ether'))
		const owner = accounts[4]
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)

		await c.issue(toUnit(1), {from: owner, value})


		assert(value.eq(await web3.eth.getBalance(c.address)), 'contract balance is not as expected')
		assert(toUnit(2000).eq(await c.fiatBalance.call()), 'fiatBalance is not correct')
  });

	
	/*
	 * etherValue()
	 */
	it("should return 4.5 from a etherValue(4500) call if etherPrice is 1000", async function() {
		const price = toUnit(1000)
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			accounts[4]
		)
		
		assert(price.eq(await c.etherPrice.call()), 'price is not as expected')
		assert(toUnit(4.5).eq(await c.etherValue(toUnit(4500))), 'etherValue() did not return as expected')
  });

	
	/*
	 * priceIsStale()
	 *
	 * When the price should not be stale
	 */
	it("should return false from priceIsStale() if the price was recently updated", async function() {
		const price = toUnit(1000)
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			accounts[4]
		)

		const time =  web3.eth.getBlock(web3.eth.blockNumber).timestamp;
		assert(await c.lastPriceUpdate.call() <= time + days(2), 'it has been too long since a price update')
		assert(await c.priceIsStale.call() !== true, 'priceIsStale() returned true when it should be false')
  });
	
	
	/*
	 * priceIsStale()
	 *
	 * When the price should be stale
	 */
	it("should return true from priceIsStale() if the price was update more than 2 days ago", async function() {
		const price = toUnit(1000)
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			accounts[4]
		)

		const before =  web3.eth.getBlock(web3.eth.blockNumber).timestamp;
		const after = before + days(2) + 1
		// set testrpc to be in the future
		await helpers.setDate(after)
		// mine a block so we have a new timestamp
		const now =  web3.eth.getBlock(web3.eth.blockNumber).timestamp;
		assert(await c.lastPriceUpdate.call() < now - days(2), 'the price update was too recent for this test')
		assert(await c.priceIsStale.call() === true, 'priceIsStale() did not return true')
  });
	
	
	/*
	 * collateralisationRatio()
	 */
	it("should return a ratio 3000 if there is 3 ETH in the contract, 1 nomin issued and an ETH price of $1500", async function() {
		const lowPrice = toUnit(1000)
		const highPrice = toUnit(1500)
		const value = web3.toWei(2, 'ether')
		const oracle = accounts[2]
		const owner = accounts[4]
		
		const c = await EtherNomin.new(
			accounts[1],
			oracle,
			accounts[3],
			lowPrice,
			owner
		)

		await c.issue(toUnit(1), {from: owner, value})
		await c.updatePrice(highPrice, {from: oracle})
		assert(highPrice.eq(await c.etherPrice.call()), 'the high price was not implemented')
		assert(toUnit(3000).eq(await c.collateralisationRatio()), 'the collat. ratio was not 3000')
  });


	/*
	 * poolFeeIncurred()
	 *
	 * We are assuming a 50 basis point fee, as described in the comments of EtherNomin.sol
	 */
	it("should determine a pool fee of 0.01 nomins on a transfer of 2 nomin", async function() {
		const price = toUnit(1000)
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			accounts[4]
		)
		assert(toUnit(0.01).eq(await c.poolFeeIncurred(toUnit(2))), 'fee was not as expected')
  });
	
	
	/*
	 * purchaseCostFiat()
	 *
	 * We are assuming a 50 basis point fee, as described in the comments of EtherNomin.sol.
	 *
	 * We are assuming that the 'purchaseCost' is the value to be transferred, plus a 50 BP
	 * fee.
	 */
	it("should return a purchase cost of $4.02 to purchase 4 nomins", async function() {
		const price = toUnit(1000)
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			accounts[4]
		)

		assert(toUnit(4.02).eq(await c.purchaseCostFiat(toUnit(4))), 'purchase cost was not as expected')
  });
	
	
	/*
	 * purchaseCostEther()
	 *
	 * We are assuming a 50 basis point fee, as described in the comments of EtherNomin.sol.
	 *
	 * We are assuming that the 'purchaseCost' is the value to be transferred, plus a 50 BP
	 * fee.
	 */
	it("should return a purchase cost of 0.15075 ETH to purchase 300 nomins at an ethPrice of $2000", async function() {
		const price = toUnit(2000)
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			accounts[4]
		)

		assert(toUnit(0.15075).eq(await c.purchaseCostEther(toUnit(300))), 'eth purchase cost was not as expected')
  });
	
	
	/*
	 * saleProceedsFiat()
	 *
	 * We are assuming a 50 basis point fee, as described in the comments of EtherNomin.sol.
	 *
	 * We are assuming that the 'saleProceeds' are the value to be sold, less a 50 BP
	 * fee.
	 */
	it("should return proceeds of $348.25 when selling 350 nomins", async function() {
		const price = toUnit(200)
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			accounts[4]
		)

		assert(toUnit(348.25).eq(await c.saleProceedsFiat(toUnit(350))), 'proceeds were not as expected')
  });
	
	
	/*
	 * saleProceedsEther()
	 *
	 * We are assuming a 50 basis point fee, as described in the comments of EtherNomin.sol.
	 *
	 * We are assuming that the 'saleProceeds' are the value to be sold, less a 50 BP
	 * fee.
	 */
	it("should return proceeds of 70.39625 ETH when selling 283 nomins at an ETH price of $4", async function() {
		const price = toUnit(4)
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			accounts[4]
		)

		assert(toUnit(70.39625).eq(await c.saleProceedsEther(toUnit(283))), 'eth proceeds were not as expected')
  });
	
	
	/*
	 * canSelfDestruct()
	 *
	 * When liquidationTimestamp is in the future.
	 */
	it("should return false to canSelfDestruct() if the liquidationTimestamp is in the future", async function() {
		const price = toUnit(4)
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			accounts[4]
		)

		const time =  new BigNumber(web3.eth.getBlock(web3.eth.blockNumber).timestamp)
		assert(time.lt(await c.liquidationTimestamp.call()), 'the liquidationTimestamp is in the past')
		assert(await c.canSelfDestruct() === false, 'the contract should not be able to self destruct')
	});


	/*
	 * canSelfDestruct()
	 *
	 * When the liquidationPeriod has passed, but all tokens have not been returned
	 * Assuming a default liquidationPeriod of 90 days.
	 */
	it("should return true to canSelfDestruct() if the liquidationPeriod has passed", async function() {
		const highPrice = toUnit(1000)
		const lowPrice = toUnit(1)
		const issueValue = new BigNumber(web3.toWei(0.004, 'ether'))
		const owner = accounts[4]
		const oracle = accounts[2]
		
		const c = await EtherNomin.new(
			accounts[1],
			oracle,
			accounts[3],
			highPrice,
			owner
		)

		// issue two nomins
		await c.issue(toUnit(2), {from: owner, value: issueValue})
		// buy one nomin, removing it from the pool 
		const purchaseCost = await c.purchaseCostEther(toUnit(1))
		await c.buy(toUnit(1), {value: purchaseCost})
		assert(toUnit(1).equals(await c.balanceOf(accounts[0])), 'accounts[0] should have a nomin')
		// drop the price so the collat ration is < 1 and we start liquidating
		await c.updatePrice(lowPrice, {from: oracle})
		// ensure we are liquidating
		assert(await c.isLiquidating() === true, 'the contract should be in liquidation')
		// push the date forward, past the liquidationPeriod
		const future = timestamp().plus(days(90)).plus(1)
		await helpers.setDate(future)
		// check to see we past the liquidationPeriod
		const liquidationTimestamp = await c.liquidationTimestamp.call()
		const liquidationPeriod = await c.liquidationPeriod.call()
		assert(liquidationTimestamp.plus(liquidationPeriod).lt(timestamp()), 'we should be past the liquidation period')
		// check to ensure all tokens have not yet been returned
		const totalSupply = await c.totalSupply.call()
		const nominPool = await c.nominPool.call()
		assert(nominPool.lt(totalSupply), 'there should be more tokens in existance than there is in the pool')

		assert(await c.canSelfDestruct() === true, 'the contract should be able to self destruct')
  });
	
	
	/*
	 * canSelfDestruct()
	 *
	 * When it is 1 week past the liquidation time, all tokens have been returned, 
	 * but the liquidationPeriod has not passed.
	 *
	 * Assuming a default liquidationPeriod of 90 days.
	 */
	it("should return true to canSelfDestruct() if all nomin have been returned to pool and its been 1 week since liquidation", async function() {
		const highPrice = toUnit(1000)
		const lowPrice = toUnit(1)
		const issueValue = new BigNumber(web3.toWei(0.004, 'ether'))
		const owner = accounts[4]
		const oracle = accounts[2]
		
		const c = await EtherNomin.new(
			accounts[1],
			oracle,
			accounts[3],
			highPrice,
			owner
		)

		// issue two nomins
		await c.issue(toUnit(2), {from: owner, value: issueValue})
		// drop the price so the collat ration is < 1 and we start liquidating
		await c.updatePrice(lowPrice, {from: oracle})
		// ensure we are liquidating
		assert(await c.isLiquidating() === true, 'the contract should be in liquidation')
		// ensure we haven't exceeded the liquidation period
		const liquidationTimestamp = await c.liquidationTimestamp.call()
		const liquidationPeriod = await c.liquidationPeriod.call()
		assert(liquidationTimestamp.plus(liquidationPeriod).gt(timestamp()), 'we should be past the liquidation period')
		// check to ensure all tokens have been returned (or, in this case, never bought)
		const totalSupply = await c.totalSupply.call()
		const nominPool = await c.nominPool.call()
		assert(nominPool.equals(totalSupply), 'all nomins should be in the pool')
		// push the date forward, just past 1 week since the liquidation timestamp
		const future = timestamp().plus(days(7)).plus(1)
		await helpers.setDate(future)

		assert(await c.canSelfDestruct() === true, 'the contract should be able to self destruct')
  });


	/*
	 * updatePrice()
	 *
	 * When the caller is not the oracle.
	 */
	it("should revert if the caller of updatePrice is not the oracle", async function() {
		const price = toUnit(1000)
		const oracle = accounts[2]
		const notOracle = accounts[0]
		assert(oracle != notOracle, 'not oracle must not be the oracle (duh)')
		
		const c = await EtherNomin.new(
			accounts[1],
			oracle,
			accounts[3],
			price,
			accounts[4]
		)

		await assertRevert(c.updatePrice(toUnit(1001), {from: notOracle}))
  });
	
	
	/*
	 * updatePrice()
	 *
	 * When the caller is the oracle.
	 */
	it("should set etherPrice to the supplied variable if updatePrice() is called by oracle", async function() {
		const oldPrice = toUnit(1000)
		const newPrice = toUnit(100000)	// moon
		const oracle = accounts[2]
		
		const c = await EtherNomin.new(
			accounts[1],
			oracle,
			accounts[3],
			oldPrice,
			accounts[4]
		)

		await c.updatePrice(newPrice, {from: oracle})
		assert(newPrice.equals(await c.etherPrice.call()), 'the new price should be in effect')
  });
	

	/*
	 * updatePrice()
	 *
	 * Auto liquidation.
	 */
	it("should go into auto liquidation if the price is set so low the contract becomes under-collateralised", async function() {
		const highPrice = toUnit(1000)
		const issueValue = new BigNumber(web3.toWei(0.004, 'ether'))
		const owner = accounts[4]
		const oracle = accounts[2]
		
		const c = await EtherNomin.new(
			accounts[1],
			oracle,
			accounts[3],
			highPrice,
			owner
		)

		// issue two nomins
		await c.issue(toUnit(2), {from: owner, value: issueValue})
		const lowPrice = highPrice.dividedBy(2).minus(1)
		await c.updatePrice(lowPrice, {from: oracle})
		assert(lowPrice.equals(await c.etherPrice.call()), 'the new price should be in effect')

		assert(await c.isLiquidating() === true, 'the contract should be in liquidation')
  });
	

	/*
	 * issue()
	 *
	 * Throws when not from owner
	 */
	it("should throw if issue() called from not owner", async function() {
		const price = toUnit(1000)
		const issueValue = new BigNumber(web3.toWei(0.004, 'ether'))
		const owner = accounts[4]
		const notOwner = accounts[5]
		assert(owner !== notOwner, 'owner and notOwner must be different')
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)

		// issue from the owner (to prove it works)
		await c.issue(toUnit(2), {from: owner, value: issueValue})
		// expect a throw when issuing from notOwner
		await assertRevert(c.issue(toUnit(2), {from: notOwner, value: issueValue}))
  });
	

	/*
	 * issue()
	 *
	 * Throws when contract is liquidating
	 */
	it("should throw if issue() called when contract is liquidating", async function() {
		const highPrice = toUnit(1000)
		const lowPrice = toUnit(1)
		const issueValue = new BigNumber(web3.toWei(0.004, 'ether'))
		const oracle = accounts[2]
		const owner = accounts[4]
		
		const c = await EtherNomin.new(
			accounts[1],
			oracle,
			accounts[3],
			highPrice,
			owner
		)

		// issue two nomins
		await c.issue(toUnit(2), {from: owner, value: issueValue})
		// drop the price so the collat ration is < 1 and we start liquidating
		await c.updatePrice(lowPrice, {from: oracle})
		// ensure we are liquidating
		assert(await c.isLiquidating() === true, 'the contract should be in liquidation')
		// test an issue call
		await assertRevert(c.issue(toUnit(2), {from: owner, value: issueValue}))
  });
	

	/*
	 * issue()
	 *
	 * Throws when ETH is below collat. ratio
	 */
	it("should throw if issue() called without sufficient collateralisation", async function() {
		const price = toUnit(1)
		const issueValue = new BigNumber(web3.toWei(1.99, 'ether'))
		const owner = accounts[4]
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)

		await assertRevert(c.issue(toUnit(1), {from: owner, value: issueValue}))
  });
	
	
	/*
	 * issue()
	 *
	 * Throws when ETH price is stale
	 */
	it("should throw if issue() called when ethPrice is stale", async function() {
		const price = toUnit(1)
		const issueValue = new BigNumber(web3.toWei(2, 'ether'))
		const owner = accounts[4]
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)
		
		// push the date forward so the price goes stale
		helpers.setDate(timestamp().plus(days(2)).plus(1))
		assert(await c.priceIsStale() === true, 'the price should be stale')
		await assertRevert(c.issue(toUnit(1), {from: owner, value: issueValue}))
  });
	

	/*
	 * issue()
	 *
	 * Updates totalSupply
	 */
	it("should update totalSupply after issue()", async function() {
		const price = toUnit(1)
		const issueValue = new BigNumber(web3.toWei(2, 'ether'))
		const owner = accounts[4]
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)
		
		assert(toUnit(0).equals(await c.totalSupply.call()), 'totalSupply should start at zero')
		await c.issue(toUnit(1), {from: owner, value: issueValue})
		assert(toUnit(1).equals(await c.totalSupply.call()), 'totalSupply should be 1')
  });
	

	/*
	 * issue()
	 *
	 * Updates nominPool
	 */
	it("should update nominPool after issue()", async function() {
		const price = toUnit(1)
		const issueValue = new BigNumber(web3.toWei(2, 'ether'))
		const owner = accounts[4]
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)
		
		assert(toUnit(0).equals(await c.nominPool.call()), 'nominPool should start at zero')
		await c.issue(toUnit(1), {from: owner, value: issueValue})
		assert(toUnit(1).equals(await c.nominPool.call()), 'nominPool should be 1')
  });
	

	/*
	 * burn()
	 *
	 * When called from not-the-owner account
	 */
	it("should throw if burn() called from not owner", async function() {
		const price = toUnit(1000)
		const issueValue = new BigNumber(web3.toWei(0.004, 'ether'))
		const owner = accounts[4]
		const notOwner = accounts[5]
		assert(owner !== notOwner, 'owner and notOwner must be different')
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)

		// issue from the owner to get some nomins to burn
		await c.issue(toUnit(2), {from: owner, value: issueValue})
		// burn from owner to check it works
		c.burn(toUnit(0.5), {from: owner})
		// expect a throw when issuing from notOwner
		await assertRevert(c.burn(toUnit(0.5), {from: notOwner}))
  });
	

	/*
	 * burn()
	 *
	 * When burning too many nomins
	 */
	it("should throw if burning more tokens than in the pool", async function() {
		const price = toUnit(1000)
		const issueValue = new BigNumber(web3.toWei(0.004, 'ether'))
		const owner = accounts[4]
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)

		// issue from the owner to get some nomins to burn
		await c.issue(toUnit(2), {from: owner, value: issueValue})
		// check there are two nomins in existance
		assert(toUnit(2).equals(await c.nominPool.call()))
		// test an excessive burn
		await assertRevert(c.burn(toUnit(2.000001), {from: owner}))
  });
	

	/*
	 * burn()
	 *
	 * A successful burn
	 */
	it("should update totalSupply and nominPool after a burn()", async function() {
		const price = toUnit(1000)
		const issueValue = new BigNumber(web3.toWei(0.004, 'ether'))
		const owner = accounts[4]
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)

		// issue from the owner to get some nomins to burn
		await c.issue(toUnit(2), {from: owner, value: issueValue})
		// check nominPool and totalSupply
		assert(toUnit(2).equals(await c.nominPool.call()))
		assert(toUnit(2).equals(await c.totalSupply.call()))
		// burn some tokens
		await c.burn(toUnit(1.5), {from: owner})
		// check nominPool and totalSupply
		assert(toUnit(0.5).equals(await c.nominPool.call()))
		assert(toUnit(0.5).equals(await c.totalSupply.call()))
  });
	
	
	/*
	 * buy()
	 *
	 * Throws when contract is liquidating
	 */
	it("should throw if buy() called when contract is liquidating", async function() {
		const highPrice = toUnit(1000)
		const lowPrice = toUnit(1)
		const issueValue = new BigNumber(web3.toWei(0.004, 'ether'))
		const oracle = accounts[2]
		const owner = accounts[4]
		
		const c = await EtherNomin.new(
			accounts[1],
			oracle,
			accounts[3],
			highPrice,
			owner
		)

		// issue two nomins
		await c.issue(toUnit(2), {from: owner, value: issueValue})
		// drop the price so the collat ration is < 1 and we start liquidating
		await c.updatePrice(lowPrice, {from: oracle})
		// ensure we are liquidating
		assert(await c.isLiquidating() === true, 'the contract should be in liquidation')
		// test a buy call
		const purchaseCost = await c.purchaseCostEther(toUnit(1))
		await assertRevert(c.buy(toUnit(1), {value: purchaseCost}))
  });
	
	
	/*
	 * buy()
	 *
	 * Purchase minimum
	 */
	it("should throw if buy() is less than 1/100th of a nomin", async function() {
		const price = toUnit(1000)
		const issueValue = new BigNumber(web3.toWei(0.004, 'ether'))
		const cheapskate = toUnit(0.0099999)
		const owner = accounts[4]
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)

		// issue two nomins
		await c.issue(toUnit(2), {from: owner, value: issueValue})
		// test an issue call
		const purchaseCost = await c.purchaseCostEther(cheapskate)
		await assertRevert(c.buy(cheapskate, {value: purchaseCost}))
  });
	
	
	/*
	 * buy()
	 *
	 * Stale price
	 */
	it("should throw on buy() if price is stale", async function() {
		const price = toUnit(1000)
		const issueValue = new BigNumber(web3.toWei(0.004, 'ether'))
		const buyValue = toUnit(0.01)
		const owner = accounts[4]
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)

		// issue two nomins
		await c.issue(toUnit(2), {from: owner, value: issueValue})
		const purchaseCost = await c.purchaseCostEther(buyValue)
		// push the date forward so the price goes stale
		helpers.setDate(timestamp().plus(days(2)).plus(1))
		assert(await c.priceIsStale() === true, 'the price should be stale')
		// test an issue call
		await assertRevert(c.buy(buyValue, {value: purchaseCost}))
  });
	
	
	/*
	 * buy()
	 *
	 * When successful
	 */
	it("should update nominPool and balanceOf on successful buy", async function() {
		const price = toUnit(1000)
		const issueValue = new BigNumber(web3.toWei(0.004, 'ether'))
		const owner = accounts[4]
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)

		// issue two nomins
		await c.issue(toUnit(2), {from: owner, value: issueValue})
		// balanceOf and nominPool are at zero
		assert(toUnit(0).equals(await c.balanceOf(accounts[0])), 'accounts[0] should have zero nomins')
		assert(toUnit(2).equals(await c.nominPool.call()), 'nominPool should be at 2')
		// buy one nomin, removing it from the pool 
		const purchaseCost = await c.purchaseCostEther(toUnit(1))
		await c.buy(toUnit(1), {value: purchaseCost})
		assert(toUnit(1).equals(await c.balanceOf(accounts[0])), 'accounts[0] should have a nomin')
		assert(toUnit(1).equals(await c.nominPool.call()), 'nominPool should be at 1')
  });
	
	
	/*
	 * sell()
	 *
	 * Selling some nomins
	 */
	it("should update balanceOf and nominPool after sell()", async function() {
		const price = toUnit(1000)
		const issueValue = new BigNumber(web3.toWei(0.004, 'ether'))
		const owner = accounts[4]
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)

		// issue two nomins
		await c.issue(toUnit(2), {from: owner, value: issueValue})
		// buy one nomin, removing it from the pool 
		const purchaseCost = await c.purchaseCostEther(toUnit(1))
		await c.buy(toUnit(1), {value: purchaseCost})
		// check balanceOf and nominPool
		assert(toUnit(1).equals(await c.balanceOf(accounts[0])), 'accounts[0] should have a nomin')
		assert(toUnit(1).equals(await c.nominPool.call()), 'nominPool should be at 1')
		// sell some nomin
		await c.sell(toUnit(0.75))
		// check balanceOf and nominPool
		assert(toUnit(0.25).equals(await c.balanceOf(accounts[0])), 'accounts[0] should have a quarter nomin')
		assert(toUnit(1.75).equals(await c.nominPool.call()), 'nominPool should be at 1.75')
  });
	
	
	/*
	 * sell()
	 *
	 * Selling some nomins when the ethPrice is stale and the contract is liquidating
	 */
	it("should allow sell() when the ethPrice is stale and contract is liquidating", async function() {
		const highPrice = toUnit(1000)
		const lowPrice = toUnit(100)
		const issueValue = new BigNumber(web3.toWei(0.004, 'ether'))
		const owner = accounts[4]
		const oracle = accounts[2]
		
		const c = await EtherNomin.new(
			accounts[1],
			oracle,
			accounts[3],
			highPrice,
			owner
		)

		// issue two nomins
		await c.issue(toUnit(2), {from: owner, value: issueValue})
		const purchaseCost = await c.purchaseCostEther(toUnit(1))
		await c.buy(toUnit(1), {value: purchaseCost})
		// drop the price so the collat ration is < 1 and we start liquidating
		await c.updatePrice(lowPrice, {from: oracle})
		// push the date forward so the price goes stale
		helpers.setDate(timestamp().plus(days(2)).plus(1))
		// check to ensure we're stale and liquidating
		assert(await c.isLiquidating() === true, 'the contract should be in liquidation')
		assert(await c.priceIsStale() === true, 'the price should be stale')
		// sell some nomin
		await c.sell(toUnit(0.01))
		// check balanceOf
		assert(toUnit(0.99).equals(await c.balanceOf(accounts[0])), 'accounts[0] should have some nomin')
  });
	
	
	/*
	 * sell()
	 *
	 * Selling some nomins when the ethPrice is stale
	 */
	it("should not allow sell() when the ethPrice is stale and contract is not liquidating", async function() {
		const price = toUnit(1000)
		const issueValue = new BigNumber(web3.toWei(0.004, 'ether'))
		const owner = accounts[4]
		const oracle = accounts[2]
		
		const c = await EtherNomin.new(
			accounts[1],
			oracle,
			accounts[3],
			price,
			owner
		)

		// issue two nomins
		await c.issue(toUnit(2), {from: owner, value: issueValue})
		const purchaseCost = await c.purchaseCostEther(toUnit(1))
		await c.buy(toUnit(1), {value: purchaseCost})
		// push the date forward so the price goes stale
		helpers.setDate(timestamp().plus(days(2)).plus(1))
		// check to ensure we're stale and not liquidating
		assert(await c.isLiquidating() === false, 'the contract should not be in liquidation')
		assert(await c.priceIsStale() === true, 'the price should be stale')
		// sell some nomin
		await assertRevert(c.sell(toUnit(0.01)))
  });
	
	
	/*
	 * sell()
	 *
	 * Selling more nomins than is owned
	 */
	it("should throw if selling more nomins than owned", async function() {
		const price = toUnit(1000)
		const issueValue = new BigNumber(web3.toWei(0.004, 'ether'))
		const owner = accounts[4]
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)

		// issue two nomins
		await c.issue(toUnit(2), {from: owner, value: issueValue})
		// buy one nomin, removing it from the pool 
		const purchaseCost = await c.purchaseCostEther(toUnit(1))
		await c.buy(toUnit(1), {value: purchaseCost})
		// sell too many nomin
		await assertRevert(c.sell(toUnit(1.0001)))
  });
	
	
	/*
	 * sell()
	 *
	 * ETH return
	 */
	it("should transfer eth to seller", async function() {
		const price = toUnit(100)
		const issueValue = new BigNumber(web3.toWei(0.04, 'ether'))
		const selling = toUnit(0.75)
		const owner = accounts[4]
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)

		// issue two nomins
		await c.issue(toUnit(2), {from: owner, value: issueValue})
		// buy one nomin, removing it from the pool 
		const purchaseCost = await c.purchaseCostEther(toUnit(1))
		await c.buy(toUnit(1), {value: purchaseCost})
		// check balanceOf and nominPool
		assert(toUnit(1).equals(await c.balanceOf(accounts[0])), 'accounts[0] should have a nomin')
		assert(toUnit(1).equals(await c.nominPool.call()), 'nominPool should be at 1')
		// check our refund amount
		const refundExpected = await c.saleProceedsEther(selling)
		const refund = await helpers.ethReturned(c.sell(selling), accounts[0])
		assert(refund.equals(refundExpected), 'refund was not as expected')
  });
	
	
	/*
	 * forceLiquidation()
	 *
	 * Not from owner
	 */
	it("should not allow a non-owner to call forceLiquidation()", async function() {
		const price = toUnit(1000)
		const owner = accounts[4]
		const notOwner = accounts[5]
		assert(owner !== notOwner, 'owner must be different to notOwner')
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)

		await assertRevert(c.forceLiquidation({ from: notOwner }))
  });
	
	
	/*
	 * forceLiquidation()
	 *
	 * From owner
	 */
	it("should allow a owner to call forceLiquidation()", async function() {
		const price = toUnit(1000)
		const owner = accounts[4]
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)

		await c.forceLiquidation({ from: owner})
		assert(await c.isLiquidating() === true, 'the contract should be in liquidation')
		const liqTime = await c.liquidationTimestamp.call()
		assert(liqTime.equals(timestamp()), 'the liquidation time should be the current block')
  });
	
	
	/*
	 * forceLiquidation()
	 *
	 * When liquidating
	 */
	it("should not allow an owner to call forceLiquidation a second time", async function() {
		const price = toUnit(1000)
		const owner = accounts[4]
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)

		await c.forceLiquidation({ from: owner})
		assert(await c.isLiquidating() === true, 'the contract should be in liquidation')
		await assertRevert(c.forceLiquidation({ from: owner}))
  });
	
	
	/*
	 * extendLiquidationPeriod()
	 *
	 * When not liquidating
	 */
	it("should not allow extendLiquidationPeriod() when not in liquidation", async function() {
		const price = toUnit(1000)
		const owner = accounts[4]
		const extension = days(30)
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)

		assert(await c.isLiquidating() === false, 'the contract should not be in liquidation')
		await assertRevert(c.extendLiquidationPeriod(extension, { from: owner}))
  });
	

	/*
	 * extendLiquidationPeriod()
	 *
	 * 30 days
	 */
	it("should extend liquidation period by 30 days", async function() {
		const price = toUnit(1000)
		const owner = accounts[4]
		const extension = days(30)
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)

		await c.forceLiquidation({ from: owner})
		assert(await c.isLiquidating() === true, 'the contract should be in liquidation')
		const period = await c.liquidationPeriod.call()
		assert(period.equals(days(90)), 'the liquidation period should be 90 days')
		await c.extendLiquidationPeriod(extension, { from: owner })
		const newPeriod = await c.liquidationPeriod.call()
		assert(period.plus(extension).equals(newPeriod), 'liquidation time should have been extended')
  });
	
	
	/*
	 * extendLiquidationPeriod()
	 *
	 * 180.1 days
	 */
	it("should not allow the liquidationPeriod to be extended to 180.1 days", async function() {
		const price = toUnit(1000)
		const owner = accounts[4]
		const extension = days(30)
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)

		await c.forceLiquidation({ from: owner})
		assert(await c.isLiquidating() === true, 'the contract should be in liquidation')
		await c.extendLiquidationPeriod(days(89), { from: owner })
		await assertRevert(c.extendLiquidationPeriod(days(1.1), { from: owner }))
  });
	
	
	/*
	 * terminateLiquidation()
	 *
	 * when not liquidating
	 */
	it("should not allow a terminateLiquidation() call when not liquidating", async function() {
		const price = toUnit(1000)
		const owner = accounts[4]
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)

		assert(await c.isLiquidating() === false, 'the contract should not be liquidating')
		assert(toUnit(0).equals(await c.totalSupply.call()), 'totalSupply should be 0')
		assert(await c.priceIsStale() === false, 'price should not be stale')

		await assertRevert(c.terminateLiquidation({from: owner}))
  });
	
	
	/*
	 * terminateLiquidation()
	 *
	 * when not owner
	 */
	it("should not allow a terminateLiquidation() call when not liquidating", async function() {
		const price = toUnit(1000)
		const owner = accounts[4]
		const notOwner = accounts[5]
		assert(owner !== notOwner, 'owner must not be notOwner')
		
		const c = await EtherNomin.new(
			accounts[1],
			accounts[2],
			accounts[3],
			price,
			owner
		)
		
		c.forceLiquidation({from: owner})
		assert(await c.isLiquidating() === true, 'the contract should be liquidating')
		// expect a revert from a non-owner terminate
		await assertRevert(c.terminateLiquidation({from: notOwner}))
		// check that the owner can terminate
		c.terminateLiquidation({ from: owner })

  });
	
	
	/*
	 * terminateLiquidation()
	 *
	 * When collat ratio is too low
	 */
	it("should not allow liquidation termination when the collat ratio is too low and totalSupply > 0", async function() {
		const highPrice = toUnit(1000)
		const lowPrice = toUnit(1)
		const issueValue = new BigNumber(web3.toWei(0.004, 'ether'))
		const owner = accounts[4]
		const oracle = accounts[2]
		
		const c = await EtherNomin.new(
			accounts[1],
			oracle,
			accounts[3],
			highPrice,
			owner
		)

		// issue two nomins
		await c.issue(toUnit(2), {from: owner, value: issueValue})
		// buy one nomin, removing it from the pool 
		const purchaseCost = await c.purchaseCostEther(toUnit(1))
		await c.buy(toUnit(1), {value: purchaseCost})
		assert(toUnit(1).equals(await c.balanceOf(accounts[0])), 'accounts[0] should have a nomin')
		// drop the price so the collat ration is < 1 and we start liquidating
		await c.updatePrice(lowPrice, {from: oracle})
		// ensure the contract state is as desired
		assert(await c.isLiquidating() === true, 'the contract should be in liquidation')
		assert(toUnit(1).greaterThan(await c.collateralisationRatio()), 'the collateralisation ratio should be < 1')
		assert(toUnit(2).equals(await c.totalSupply.call()), 'totalSupply should be 2')
		// we should not be able to terminate liquidation
		await assertRevert(c.terminateLiquidation({ from: owner }))	
  });
	
	
	/*
	 * terminateLiquidation()
	 *
	 * When collat ratio is too low but totalSupply == 0
	 */
	it("should allow liquidation termination when the collat ratio is too low but totalSupply is 0", async function() {
		const highPrice = toUnit(1000)
		const lowPrice = toUnit(1)
		const issueValue = new BigNumber(web3.toWei(0.004, 'ether'))
		const owner = accounts[4]
		const oracle = accounts[2]
		
		const c = await EtherNomin.new(
			accounts[1],
			oracle,
			accounts[3],
			highPrice,
			owner
		)

		// issue two nomins
		await c.issue(toUnit(2), {from: owner, value: issueValue})
		// drop the price so the collat ration is < 1 and we start liquidating
		await c.updatePrice(lowPrice, {from: oracle})
		// burn the tokens
		await c.burn(toUnit(2), {from: owner})
		// ensure the contract state is as desired
		assert(await c.isLiquidating() === true, 'the contract should be in liquidation')
		assert(toUnit(0).equals(await c.totalSupply.call()), 'totalSupply should be 0')
		assert(await c.priceIsStale() === false, 'price should not be stale')
		// we should be able to terminate liquidation
		await c.terminateLiquidation({ from: owner })
		assert(await c.isLiquidating() === false, 'the contract should no longer be in liquidation')
	});
	
	
	/*
	 * terminateLiquidation()
	 *
	 * When collat ratio is too low
	 */
	it("should allow liquidation termination when totalSupply > 0 but collatRatio is > 1", async function() {
		const highPrice = toUnit(1000)
		const lowPrice = toUnit(1)
		const issueValue = new BigNumber(web3.toWei(0.004, 'ether'))
		const owner = accounts[4]
		const oracle = accounts[2]
		
		const c = await EtherNomin.new(
			accounts[1],
			oracle,
			accounts[3],
			highPrice,
			owner
		)

		// issue two nomins
		await c.issue(toUnit(2), {from: owner, value: issueValue})
		// buy one nomin, removing it from the pool 
		const purchaseCost = await c.purchaseCostEther(toUnit(1))
		await c.buy(toUnit(1), {value: purchaseCost})
		assert(toUnit(1).equals(await c.balanceOf(accounts[0])), 'accounts[0] should have a nomin')
		// force liquidation
		await c.forceLiquidation({from: owner})
		// ensure the contract state is as desired
		assert(await c.isLiquidating() === true, 'the contract should be in liquidation')
		assert(toUnit(1).lessThan(await c.collateralisationRatio()), 'the collateralisation ratio should be > 1')
		assert(toUnit(2).equals(await c.totalSupply.call()), 'totalSupply should be 2')
		// we should be able to terminate liquidation
		await c.terminateLiquidation({ from: owner })
  });


});

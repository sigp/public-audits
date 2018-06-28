const PoorlyCodedOwnable = artifacts.require('./OwnerToZero')


contract('Ownable', function(accounts) {

	it('should set the owner to 0x0 if _setOwner() is called', async function() {
		const p = await PoorlyCodedOwnable.new(accounts[0])
		assert(await p.owner.call() === accounts[0])
		await p.doSomethingStupid()
		const owner = await p.owner()
		assert(owner === "0x0000000000000000000000000000000000000000")
	})


})

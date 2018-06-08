const VariableReturnData = artifacts.require('./VariableReturnData')
const WantsVariableReturnData = artifacts.require('./WantsVariableReturnData')
const Proxy = artifacts.require('./Proxy')


contract('Variable Return Data', function(accounts) {

	it('should allow for variable return data', async function() {
		const owner = accounts[0]

		const v = await VariableReturnData.new()
		const p = await Proxy.new(owner)
    await p.setTarget(v.address)
		const w = await WantsVariableReturnData.new(p.address)
		
		assert(await w.myArray(1) == 0, 'myArray slot 1 should be empty')
		assert(await w.source() === p.address, 'w should seek the data from the proxy')

		await w.getData()

    const two = await w.myArray(1)
    const four = await w.myArray(3)
    assert(two.equals(2), 'the second slot should be two')
    assert(four.equals(4), 'the third slot should be four')
	})
	
	
	it('should allow a call directly to the proxy using the .at() method', async function() {
		const owner = accounts[0]

		const v = await VariableReturnData.new()
		const p = await Proxy.new(owner)
    await p.setTarget(v.address)
		const pv = VariableReturnData.at(p.address)

		assert(await v.callCount() == 0, 'callCount should be 0')

		await pv.returnArray()
		
		assert(await v.callCount() == 1, 'callCount should be 1')
	})

})

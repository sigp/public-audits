const deployer = require('../deployer.js')
const BigNumber = require("bignumber.js")

const helpers = require('../testHelpers.js')
const assertRevert = helpers.assertRevert


contract('Test Rig', function(accounts) {

	it('should build a test rig without throwing', async function() {
		const rig = await deployer.setupTestRig(accounts)
	})
	
	
	it('should allow for the reading of havven price after deployment (contract directly)', async function() {
		const rig = await deployer.setupTestRig(accounts)

		const owner = rig.accounts.owner
		const h = rig.havven

		await h.havvenPrice.call()
	})

	it('should allow for the reading of havven price after deployment (via proxy)', async function() {
		const rig = await deployer.setupTestRig(accounts)

		const owner = rig.accounts.owner
		const h = rig.proxies.havven

		await h.havvenPrice.call()
	})

})

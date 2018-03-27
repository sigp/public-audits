const deployer = require('../deployer.js')
const BigNumber = require("bignumber.js")

const helpers = require('../testHelpers.js')
const assertRevert = helpers.assertRevert


contract('Test Rig', function(accounts) {

	it('should build a test rig without throwing', async function() {
		const rig = await deployer.setupTestRig(accounts)
	})
	
	
	it('should allow for the reading of nomin etherPrice after deployment', async function() {
		const rig = await deployer.setupTestRig(accounts)

		const owner = rig.accounts.owner
		const n = rig.nomin

		await n.etherPrice.call()
	})

})

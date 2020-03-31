const deployer = require('../deployer.js')
const BigNumber = require("bignumber.js")

const helpers = require('../testHelpers.js')
const havvenHelpers = require('../synthetixHelpers.js')

const toUnit = havvenHelpers.toUnit;

contract('deploy', (accounts) => {

	describe('deployment', function() {
		it('can deploy a test rig', async function() {
			rig = await deployer.deployTestRig(accounts.slice(0, 6));
		})
	})
})

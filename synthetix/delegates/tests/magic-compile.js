/*
 * Truffle throws some errors when trying to compile due to
 * to the cyclic imports.
 *
 * This script will do the compile and create the truffle
 * artifacts required for truffle testing.
 */

const fs = require('fs')
const solc = require('solc')
const Artifactor = require('truffle-artifactor')

const SOURCE_DIR = '../havven-repo/contracts/'
const INTERFACE_DIR = '../havven-repo/contracts/interfaces/'
const OUTPUT_BUILD_DIR = './build/contracts/'
const IMPORT_PREFIX = 'contracts/'

const artifactor = new Artifactor(OUTPUT_BUILD_DIR)

let contractsDir = fs.readdirSync(SOURCE_DIR)

let solFiles = []
if (process.argv.length > 2) {
	// If files were supplied as args, compile them.
	solFiles = process.argv.slice(2, process.argv.length)
} else {
	// If there were args, get all the files in the directory.
	solFiles = contractsDir.filter(f => f.endsWith('.sol'))
}

/*
 * Reduce the solFiles array into a dict with keys of import names
 * and values of the source.
 * e.g., {'contracts/lol.sol': 'contract lol { function ha() {} }'}
 */
const input = solFiles.reduce((acc, val, i) => {
	acc[IMPORT_PREFIX + solFiles[i]] = fs.readFileSync(SOURCE_DIR + solFiles[i], 'utf8')
	return acc
}, {})


/*
 * Special for Synthetix:
 *
 * Pull the openzepplin-solidity contract in.
 */
safeMathImport = "openzeppelin-solidity/contracts/math/SafeMath.sol"
safeMathLocation = "./node_modules/" + safeMathImport
input[safeMathImport] = fs.readFileSync(safeMathLocation, 'utf8')

reentrancyImport = "openzeppelin-solidity/contracts/utils/ReentrancyGuard.sol"
reentrancyLocation = "./node_modules/" + reentrancyImport
input[reentrancyImport] = fs.readFileSync(reentrancyLocation, 'utf8')

chainlinkImport = "chainlink/contracts/interfaces/AggregatorInterface.sol"
chainlinkLocation = "./node_modules/" + chainlinkImport
input[chainlinkImport] = fs.readFileSync(chainlinkLocation, 'utf8')

/*
 * Add interfaces manually
 */

 ierc20Import = INTERFACE_DIR + "IERC20.sol"
 input[ierc20Import] = fs.readFileSync(ierc20Import, 'utf8')


/*
 * Setting the second parameter to 1 actives the
 * optimiser
 */
var output = solc.compile({ sources: input }, 1)
console.log(`Finished compile.`)

if (output.errors.length) {
	console.log(output.errors)
}

/*
 * Loop through the compiled data and create the truffle
 * artifacts.
 */
for (var name in output.contracts) {
	let contract = output.contracts[name]
	console.log('Creating artifact for ' + name)
	artifactor.save({
		contractName: name.split(':')[1],
		abi: JSON.parse(contract.interface),
		binary: contract.bytecode
	})
}

console.log('Done.')

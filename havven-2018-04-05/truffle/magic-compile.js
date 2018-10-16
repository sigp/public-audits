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

const SOURCE_DIR = '../../contracts/';
const OUTPUT_BUILD_DIR = './build/contracts/';
const IMPORT_PREFIX = 'contracts/';

const artifactor = new Artifactor(OUTPUT_BUILD_DIR);

let solFiles = [
	'Court.sol',
	'EtherNomin.sol',
	'ExternStateProxyFeeToken.sol',
	'ExternStateProxyToken.sol',
	'Havven.sol',
	'HavvenEscrow.sol',
	'LimitedSetup.sol',
	'Owned.sol',
	'Proxy.sol',
	'SafeDecimalMath.sol',
	'SelfDestructible.sol',
	'TokenState.sol',
]

/*
 * Reduce the solFiles array into a dict with keys of import names 
 * and values of the source.
 * e.g., {'contracts/lol.sol': 'contract lol { function ha() {} }'}
 */
const input = solFiles.reduce((acc, val, i) => {
	acc[IMPORT_PREFIX + solFiles[i]] = fs.readFileSync(SOURCE_DIR + solFiles[i], 'utf8');
	return acc;
}, {})

console.log('Starting compile...')

/*
 * Setting the second parameter to 1 actives the
 * optimser
 */
var output = solc.compile({ sources: input }, 1)

console.log(`Finished compile.`)

/*
 * Loop through the compiled data and create the truffle
 * artifacts.
 */
for (var name in output.contracts) {
	let contract = output.contracts[name];
	console.log('Creating artifact for ' + name)
	artifactor.save({
		contractName: name.split(":")[1],
		abi: JSON.parse(contract.interface),
		binary: contract.bytecode
	})
}

console.log('Done.')

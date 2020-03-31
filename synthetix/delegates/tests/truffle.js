module.exports = {
	contracts_directory: "../havven-repo/synthetix/contracts/**/*.sol", // both our contracts directory ../havven-repo's
	networks: {
		development: {
			host: 'localhost',
			port: 8545,
			network_id: '*',
			gas: 10000000,
		},
		coverage: {
			// Note: coverage currently failing to deploy synthentix as gas limit won't suffice
			host: 'localhost',
			network_id: '*',
			port: 8555,
			gas: 10000000,
			gasPrice: 0x01,
		},
	},
	mocha: {
		useColors: true,
		slow: 3000, // We only consider tests slow when they take more than 3 seconds.
		enableTimeouts: false,
		reporter: 'eth-gas-reporter',
		reporterOptions: {
			showTimeSpent: true,
			currency: 'USD',
			outputFile: 'test-gas-used.log',
		},
	},
	compilers: {
		solc: {
			version: '0.4.25',
			settings: {
				optimizer: {
					enabled: true,
					runs: 200,
				},
			},
		},
	},
};

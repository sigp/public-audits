.PHONY: test

SOLC_FLAGS=--bin --abi
OPT=--optimize --optimize-runs 10000
BUILD_DIR=build

SOURCE_DIR=../code/contracts/solidity/
SOLIDITY_CONTRACTS=MultiSigWallet.sol

TEST_SOURCE_DIR=./contracts/
TEST_CONTRACTS=*.sol

all: clean compile

clean:
	mkdir -p ${BUILD_DIR}
	rm -rf ${BUILD_DIR}/*

compile: ${SOLIDITY_CONTRACTS} ${TEST_CONTRACTS}

$(SOLIDITY_CONTRACTS):
	solc -o ${BUILD_DIR} --overwrite ${OPT} ${SOLC_FLAGS}  ${SOURCE_DIR}$@

${TEST_CONTRACTS}:
	solc -o ${BUILD_DIR} --overwrite ${OPT} ${SOLC_FLAGS}  ${TEST_SOURCE_DIR}$@


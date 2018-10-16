.PHONY: test

SOLC_FLAGS=--bin --abi
OPT=--optimize --optimize-runs 10000
BUILD_DIR=build

SOURCE_DIR=../code/ens-usernames/contracts/**/
TEST_SOURCE_DIR=contracts/

SOLIDITY_CONTRACTS=*.sol

all: clean compile

clean:
	mkdir -p ${BUILD_DIR}
	rm -rf ${BUILD_DIR}/*

compile: $(SOLIDITY_CONTRACTS)

$(SOLIDITY_CONTRACTS):
	solc -o ${BUILD_DIR} --overwrite ${OPT} --allow-paths . ${SOLC_FLAGS}  ${TEST_SOURCE_DIR}$@
	solc -o ${BUILD_DIR} --overwrite ${OPT} --allow-paths . ${SOLC_FLAGS}  ${SOURCE_DIR}$@

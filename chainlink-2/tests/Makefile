.PHONY: test

SOLC_BIN=./solc
SOLC_FLAGS=--bin --abi
OPT=--optimize --optimize-runs 10000
BUILD_DIR=build

SOURCE_DIR=../code/contracts
INTERFACES_DIR=../code/contracts/interfaces/
DEV_DIR=../code/contracts/dev/
EXAMPLES_DIR=../code/contracts/examples/
MATH_DIR=../code/contracts/openzeppelin-solidity/contracts/math/
OWNERSHIP_DIR=../code/contracts/openzeppelin-solidity/contracts/ownership/
CBOR_DIR=../code/contracts/solidity-cborutils/contracts/
TEST_SOURCE_DIR=contracts/


# Dangerous, but useful for testing known contracts
ALLOWED_PATHS=/

SOLIDITY_CONTRACTS=*.sol

all: clean compile

clean:
	mkdir -p ${BUILD_DIR}
	rm -rf ${BUILD_DIR}/*

compile: $(SOLIDITY_CONTRACTS)

$(SOLIDITY_CONTRACTS):
	${SOLC_BIN} -o ${BUILD_DIR} --overwrite ${OPT} --allow-paths . ${SOLC_FLAGS}  ${INTERFACES_DIR}$@
	${SOLC_BIN} -o ${BUILD_DIR} --overwrite ${OPT} --allow-paths . ${SOLC_FLAGS}  ${DEV_DIR}$@
	${SOLC_BIN} -o ${BUILD_DIR} --overwrite ${OPT} --allow-paths . ${SOLC_FLAGS}  ${EXAMPLES_DIR}$@
	${SOLC_BIN} -o ${BUILD_DIR} --overwrite ${OPT} --allow-paths . ${SOLC_FLAGS}  ${SOURCE_DIR}/$@
	${SOLC_BIN} -o ${BUILD_DIR} --overwrite ${OPT} --allow-paths ${ALLOWED_PATHS} sources=${SOURCE_DIR} ${SOLC_FLAGS} ${TEST_SOURCE_DIR}$@

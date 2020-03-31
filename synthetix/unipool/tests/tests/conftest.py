import pytest
import os
from web3 import Web3, HTTPProvider

# allow POA chains, specifically support geth --dev
# from web3.middleware import geth_poa_middleware

pytest_plugins = [
    "utils.asserts",
    "utils.block",
    "utils.receipts",
    "utils.transfers",
    "utils.balances",
    "utils.ganache",
    "utils.times",
    "conftest-unipool"
]

BUILD_PATH = "build/"


# populate accounts for geth --dev
def geth_prepare_accounts(no_accounts, eth_per_account):
    accounts = web3_instance.eth.accounts
    for i in range(no_accounts - len(accounts)):
        acc = web3_instance.personal.newAccount("pass")
        web3_instance.personal.unlockAccount(acc, "pass", duration=int(1e6))
        web3_instance.eth.sendTransaction({'from': accounts[0], 'to': acc,
                                          'value': int(eth_per_account*1e18)})


# if we are using geth --dev inject middleware
if 'TEST_GETH' in os.environ:
    from web3.auto.gethdev import w3 as web3_instance
    geth_prepare_accounts(10, 10000)
elif 'TEST_INTERNAL' in os.environ:
    # Use internal web3 test client
    web3_instance = Web3(TestRPCProvider())
else:
    # Use external client as default
    web3_instance = Web3(HTTPProvider("http://localhost:8545"))
# Get the Web3 Instance up with Ganache
web3_instance = Web3(HTTPProvider("http://localhost:8545"))


@pytest.fixture
def w3():
    return web3_instance


@pytest.fixture
def accounts(w3):
    return w3.eth.accounts


@pytest.fixture
def link():
    """
    Obtains a binary and replaces the stubs with the libraries addresses
    """
    def bin_file(c):
        return BUILD_PATH + c + ".bin"

    def method(contract, strings, addresses):
        """
        Replaces library stubs with addresses
        @param strings - List of strings to replace in the bytecode
        @param addresses - List of addresses to insert
        """
        binary = open(bin_file(contract)).read()
        for idx, string in enumerate(strings):
            # Remove the 0x from addresses
            address = addresses[idx][2:]
            binary = binary.replace(string, address)
        return binary

    return method


@pytest.fixture
def deploy(w3):
    """
    Deploys a contract from binaries. Allows an optional custom binary
    for linking contracts
    """
    def path(f):
        return BUILD_PATH + f

    def abi_file(c):
        return path(c + ".abi")

    def bin_file(c):
        return path(c + ".bin")

    def deploy_contract(contract, transaction, args, bytecode=None):
        """
        bytecode is used if we have to manually link libraries. If not
        supplied, we get the binary from the build directory
        """
        abi = open(abi_file(contract)).read()

        if bytecode is None:  # We don't have a custom binary, get from file
            bytecode = open(bin_file(contract)).read()

        # Load the contract
        f = w3.eth.contract(abi=abi, bytecode=bytecode)
        # Submit a tx to deploy the contract
        tx_hash = f.constructor(**args).transact(transaction)
        # Get the receipt from the tx hash
        tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
        # Create a new contract instance for the newly deployed
        # contract.
        c = w3.eth.contract(
            address=tx_receipt["contractAddress"],
            abi=f.abi
        )
        return (c, tx_receipt)
    return deploy_contract


@pytest.fixture
def instantiate(w3):
    """
    Obtains a binary and replaces the stubs with the libraries addresses
    """

    def method(address, abi):
        """
        Returns an instance of a contract based on an ABI and an address
        """
        c = w3.eth.contract(
            address=address,
            abi=abi
        )
        return c

    return method

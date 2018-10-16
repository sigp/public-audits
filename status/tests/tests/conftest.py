import pytest
import os
from web3 import Web3, HTTPProvider, TestRPCProvider, IPCProvider
# allow POA chains, specifically support geth --dev
#from web3.auto.gethdev import w3 as W3
from web3.middleware import geth_poa_middleware

pytest_plugins = [
    'utils.asserts',
    'utils.block',
    'utils.receipts',
    'utils.transfers',
    'utils.balances',
    'utils.ganache',
    'utils.times',
    #
    'conftest-registrar',
    'conftest-attacks'
]

BUILD_PATH = "build/"
CONTRACTS = [
    "UsernameRegistrar",
    "ENSRegistry",
    "PublicResolver",
    "TestToken",  # Use the test token
    "ReentrancyAttack",
    "DOSAttack"
]

# populate accounts for geth --dev
def geth_prepare_accounts(no_accounts, eth_per_account):
    accounts = web3_instance.eth.accounts
    for i in range(no_accounts - len(accounts)):
        acc = web3_instance.personal.newAccount("pass")
        web3_instance.personal.unlockAccount(acc,"pass",duration=int(1e6))
        web3_instance.eth.sendTransaction({'from': accounts[0], 'to': acc,
            'value': int(eth_per_account*1e18)})


# if we are using geth --dev inject middleware
if 'TEST_GETH' in os.environ:
    from web3.auto.gethdev import w3 as web3_instance
    geth_prepare_accounts(10,10000)

elif 'TEST_INTERNAL' in os.environ:
    # Use internal web3 test client
    web3_instance = Web3(TestRPCProvider())
else:
    # Use external client as default
    web3_instance = Web3(HTTPProvider("http://localhost:8545"))


@pytest.fixture
def w3():
    return web3_instance


@pytest.fixture
def accounts(w3):
    return w3.eth.accounts


@pytest.fixture
def contract_factories(w3):
    """
    Generates a web3.py ContractFactory for each contract in the CONTRACTS
    list.  It is expected that a .abi and .bin file exists in the BUILD_PATH
    for each contract specified.
    """
    output = {}

    def path(f):
        return BUILD_PATH + f

    def abi_file(c):
        return path(c + ".abi")

    def bin_file(c):
        return path(c + ".bin")

    for c in CONTRACTS:
        with open(abi_file(c)) as abi, open(bin_file(c)) as bytecode:
            output[c] = w3.eth.contract(abi=abi.read(),
                                        bytecode=bytecode.read())
    return output


@pytest.fixture
def deploy(w3, contract_factories, accounts):
    """
    Deploys a contract from the contract factory.
    """
    def deploy_contract(contract, transaction, args):
        # Load the contract factory by name (e.g., MyErc20Contract)
        f = contract_factories[contract]
        # Submit a tx to deploy the contract
        tx_hash = f.constructor(**args).transact(transaction)
        # Get the receipt from the tx hash
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
        # Create a new contract instance for the newly deployed
        # contract.
        c = w3.eth.contract(
            address=tx_receipt['contractAddress'],
            abi=f.abi
        )
        return (c, tx_receipt)
    return deploy_contract

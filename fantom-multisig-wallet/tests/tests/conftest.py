import pytest
from web3 import Web3, HTTPProvider

pytest_plugins = [
    'utils.asserts',
    'utils.block',
    'utils.receipts',
    'utils.transfers',
    'utils.balances',
    'utils.ganache',
    #
    'conftest-multisig',
]

BUILD_PATH = "build/"
CONTRACTS = [
    "MultiSigWallet",
    "Contract1",
    "Contract2",
    "Contract3",
    "ERC20"
]


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
        tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
        # Create a new contract instance for the newly deployed
        # contract.
        c = w3.eth.contract(
            address=tx_receipt['contractAddress'],
            abi=f.abi
        )
        return (c, tx_receipt)
    return deploy_contract

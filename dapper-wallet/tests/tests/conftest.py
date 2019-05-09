import pytest
import os
from web3 import Web3, HTTPProvider, TestRPCProvider

# allow POA chains, specifically support geth --dev
# from web3.middleware import geth_poa_middleware

pytest_plugins = [
    "tests.utils.asserts",
    "tests.utils.block",
    "tests.utils.receipts",
    "tests.utils.transfers",
    "tests.utils.balances",
    "tests.utils.ganache",
    "tests.utils.times",
    "tests.utils.functions",
    "tests.dapper_utils",
    "tests.conftest_dapper",
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

ACCOUNTS = web3_instance.eth.accounts


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
def get_abi():

    def abi_file(c):
        return BUILD_PATH + c + ".abi"

    def read_abi(contract):
        with open(abi_file(contract)) as file:
            return file.read()

    return read_abi





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

@pytest.fixture
def accounts_private_keys():
    # These are generated from the standard mnemonic
    # "skirt social flee frog wine stomach dignity fever feed anger puzzle drill"

    addresses = [
        "0xb284e5c17e82c91a62165daf7219e1c9ff607451",
        "0x09eb020174bfd436c0c14a72327206161e53f24d",
        "0xf4b25e4820f4a3329fa41efaf4a116f43a904cb0",
        "0x7e86b58ec91c438c60976d3bdfd24eb6759669d3",
        "0xd183d19825c9c7eec816001cbf4918e98ab6acf6",
        "0x33f496c23f5591bb5f6ff2b7c5d4f57936253f34",
        "0x70f9252e6da61215ac1152fa45e584e48003bb14",
        "0xdcc777f49c2515b04bf1fd7ff397908a2d2899fa",
        "0x7abf906d640f9d129d92fb582cb4d833db15f5e8",
        "0x68290d7eb8cfe0256fb59f0332d7e16880f97418",
        "0x5625b37c5ffe3f2dbcda484cb75898eb906a6c5a",
        "0x159921b897decec9379e5c6190b7d7f9d8db830b",
        "0x391b598a00edb24ce8eef74bcf89c17af2382566",
        "0x5f26f5d97ee7f0303770abc90f247cabcc6104a2",
        "0x7cab8eac71c151706ffa7dc93336fb53d08dd4e3",
        "0xe1771f24aabea4ec62ca70b203bb416fb56afa6f",
        "0xaa106e04225eb317cf3fd0a2f3c968b46ba3ca2d",
        "0x19b736c726d33ed7240c8f2974474907df6cbb01",
        "0xe02516b5aa13781db343cf31fc0b201a222ee95d",
        "0x282b0dbe79c360246bd154f49c31907119ed2129",
        "0x9f95ee8961771fe6f4d1acd983d40bf752a69eff",
        "0x1c977baaf3271adf4ec5a1c70126504ea4d9b984",
        "0x024526c0755473dea160d73c3e2e62535f56d132",
        "0xcd1f2717ede087f67879a20b0ab6b5f5e4603b61",
        "0xd015f6ce695bda91fcd60952351946099b77a234",
        "0x259a45d0f82e151ccfd74c8c73fd47e9838f75b8",
        "0x87332d56616c04fc915e03d285b0213154c2a563",
        "0x9d21ce2fa581a7ba3278d623c88a71704b532d25",
        "0x3773f4a1ba4716db368e22e041796be4a073ee9a",
        "0x7b95b99a69e7560e63a757ab2f1d336b9a36adbd",
        "0xe591a9e0fc264c4344b71c2980d9c2698789da23",
        "0x61a4e4d81f692fe07f31137fc07c0b8a78e1084e",
        "0x27dec793828819c209a33ca60362b97d8be6a20f",
        "0x943a207786650e4397a4780854e2a96ab83f1343",
        "0x7ed121a1e21515cfd63b6c62840349fda0236918",
        "0x3fa143e901ecae578b072f14665e6b9b6059655a",
        "0x3b831183e7245ba6df0a1c1b48e4ff4f0e516556",
        "0x0e2e1bf6fa30745c86580dc580375ebf7d8b33df",
        "0x16fd066405c8035ef437b1b503607b81cabc181f",
        "0xc1a1bdbb572989075390351085b5baeea8aeb36d",
        "0x40aabf2a53b6785d9c3cf51f60af20ba445eb51d",
        "0xfa5aaba3b91e867a1c7f0c304d6dbe47fb597990",
        "0x75d59b871931452974b4d3b0f13dc1b0f31911d4",
        "0xd6a0aee61382b8df8990a3b0779c49b89bd48a68",
        "0x32b8f231edf27734bab8e2d01b1a8a361267536c",
        "0x9e683ae6271c14778da50c5ed6f7d39c4ea2447f",
        "0x06130001f66005483e39c8a2465c66a4fb324726",
        "0x5e38ae7619b6e49f69bd6ba15a38aed9e4d6d216",
        "0x3350355ed5ec296befb0ad42bbeb5a8a95b70959",
        "0x70f5791baad0fc6160bd8b870252c6787e716b28"]

    priv_keys = [
        "0xc4207c128af83edd3a4662536e3e6cab53071d7244973f7f7a9f17ac470f4e69",
        "0x0581fdbce9da7694915eff1d2ae9c2c7efb376a0b153a0b6e75cf7584aeb4a43",
        "0xbb4eefd8877aa7211b9bffff2432af2638ce158cbf74ce1066efc5bf21b64b7f",
        "0xf2ef44f763e0070e122e4ac39caa0d9b0087a77a45af10c588b2ec5b8abf7fd1",
        "0xed53433539d543107e179e778940eaa35e47df0d4ca1093b1b4f0fdb1e5958af",
        "0xd5525c7181219116ef1d49600c5780a07ddb2a11e6693034c7a244fffd14e888",
        "0x71770ba3dc76a8a12b83a4b767ff8a91ea75b90cfd3b29b1957aa17a74adf89a",
        "0xf3bb3f9ada4a35f18a8b190754a3a5ed2839f841a8f050420def60e1cc9555cb",
        "0x0e4e36e446aa5a9d5d476e77aafa87a0ccc763fee7209af2b5c9f9cebca206f2",
        "0x7ae5fb9631b92ebee693c5531fc93f43d2a33e54ecf6177357528dc106de34f8",
        "0xb7bae4e65286f4640a6d4534372cddcabc07d0bc80e4a728413cd0eddbe6c36f",
        "0x2b206c259d2fee5b5806e157a71bb06c42b39e5fb787d688f3d5b7dcc293a139",
        "0xc80071463f93957688a4d10442c287c991b8bedc6538205a0b6b0c5a2a684b37",
        "0x38f2bcede7a23850decd3027876ba675287e42d634a23a2d8380d1e472d05f51",
        "0x5e12f2dd222ad49bbcd2c6f5a50b219b114bba519b0905fbab40c7ce3b88525a",
        "0xcd0ae8a81c6a9a8d62e718d7bcfabc6e6365b9be9616c55db286071b88edce64",
        "0x9726d680238c18d9bc160531369afc8e49192d3e6255f60d3bfa9bd8e055e42f",
        "0x65d671b69bea7d7a201448cb3b362ec39f8e5367c1f68e33eb83fc82daa978f4",
        "0xc9d303e93228a9c05208b4f67628be2d6e19c28ab70368c8a888f271b9493bd8",
        "0xbe725209d9a1b41eee13f7622e725983d4f5839d4e1bb48f2ac535d722a0a5c5",
        "0xea7ae086f41d436d72e2d62f193257d3758c3b5eb6579d40165b4030fd168ee0",
        "0x7af0704e31184ea6bfc5eb13497ddb1a84bf64318903ad734b720ee2856bde46",
        "0x3439b19294fd098d4c7f39ac4d6d4188f9bcfed18170e15ccf18920ad7f9d2d1",
        "0x2ca77ed046a61c4635b8e38e2494d79120259158a4f67c6f190186baa0e81cf4",
        "0x6e0b3151e5c2994c494eb30b9e7b51dd50495e15038489a64bd419edc139cbbd",
        "0x0389f9256da39b8a7399700fa6bcfbaed25e8006b390ff101a26dabd553d8537",
        "0x5f1c073aec907aff7337f13ae81a50d154f57d79bee8e7ea83bb8cd3bddee919",
        "0x45ac9943c1061030670188411702e24be83bb5cc480012284367e7bc6ed6894e",
        "0x8916357b60ba15eac52681a2323031f663aaf1f1ac6c4943b71b4a8ecf95e835",
        "0x0edce4c8874dbf9c9332ac5e87d67dee176db7aab0ae9cfb8995d4041bb551fc",
        "0x202d87cc6f4e913fb1441f06a25f98e5248df7b5a88f21c32bf3fa5af7980513",
        "0xe47e2500c7d31837e2e86c626cf113f3b7a3a8304dc415850eeaa5ec420d11bc",
        "0x25d20bd5ce90b381dfc9e997887dd4f958c211c7a4cf0df74f194455d0d1d71b",
        "0xaefb4cf53b025d58e0dd10570f4abbaa6d7aabf5a11a9b368fd4b3c0669503d5",
        "0xb43b8335cfe4f16085537eabf6c447b185573f5c83bfd85f7539d4c48e50fa94",
        "0x554dfa62e17c16bbacb7bba09b2b841025385302828eccd3b4bdb0061a993cb3",
        "0xac3eb5e13abd6cc4c4a1e4f7db8a317fc28941a15ed88375a0ac19a262e98d60",
        "0x7f266bae32577f65f1450448f74fb9b48cfe87f35401f60757fe7a9a17d3d283",
        "0x658d2968ff0ba810353f46a76e111d2551e34db46bed1e85f8ef5c877c674a2b",
        "0x98f13f19e3bd5a6755008923446b4e0291684e3480fdc4d18f7c0921a339ec24",
        "0x1566152abf3c0127e07b63366c4ff3727965caf48cd1d1e26db52ea92091dbcf",
        "0xb87aaa24a610d4f44454b072bf862e5ef9b65b67eceada22a91824b866caebce",
        "0x40454e5712e2f89b94a06780a561395f90fe3f8c5eb3430bff0dfa005d16f6f7",
        "0x43c7e6eee8d8c622636f6c474aaba0863438cc7fef66ad6e6884d6441ba41f7c",
        "0x40bf511ae393ba5f99e9a889dd07deb55c02000b59a8ec0eaa53d65a1b35a806",
        "0x46eec10b2f8d0e9a1ddc0593fa82122fbf59e5c753089c2e052727c10154fe11",
        "0x7f001a1a5f0b5b6209017087eecb84bc647b5d7bd5b6eb87aab3aaa205ef7a5f",
        "0xd211dafb69b3338a8718f4fa92348db10ea293dfe863142762f62741704ca323",
        "0xed765f17c0930ed68ae04a929548f4386d50236903016c0e01e191670543fab7",
        "0x989dbcbd23972f521370a8b13462bf915489b24e11a1bb724935a19fff036fb5"]

    return {str(addresses[i]): str(priv_keys[i]) for i in range(len(addresses))}

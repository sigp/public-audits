import pytest


@pytest.fixture
def clonefactory_deploy(accounts, deploy):
    """
    Deploy the CloneFactory contract for the wallet.
    """
    def method():
        (c, r) = deploy(
            contract="CloneFactory",
            transaction={
                'from': accounts[0],
            },
            args={}
        )
        return (c, r)
    return method


@pytest.fixture
def cloneable_wallet_deploy(accounts, deploy):
    """
    Deploy the Clone-able Wallet
    """
    def method(deployment_account=accounts[0]):
        (c, r) = deploy(
            contract="CloneableWallet",
            transaction={
                'from': deployment_account,
            },
            args={}
        )

        return (c, r)
    return method


@pytest.fixture
def walletfactory_deploy(accounts, cloneable_wallet_deploy, deploy):
    """
    Create a wallet factory
    """
    def method(deployment_account=accounts[0]):
        (wallet_c, wallet_r) = cloneable_wallet_deploy(deployment_account)
        (factory_c, factory_r) = deploy(
            contract="WalletFactory",
            transaction={
                'from': deployment_account,
            },
            args={
                '_cloneWalletAddress': wallet_c.address
            }
        )

        return (wallet_c, wallet_r, factory_c, factory_r)
    return method


@pytest.fixture
def fullwallet_deploy(accounts, deploy):
    """
    Create and deploy a 'FullWallet'
    """
    def method(authorized=accounts[1], cosigner=accounts[2], recovery=accounts[3]):
        (wallet_c, wallet_r) = deploy(
            contract="FullWallet",
            transaction={
                'from': accounts[0],
            },
            args={
                '_authorized': authorized,
                '_cosigner': int(cosigner, 0),
                '_recoveryAddress': recovery,
            }
        )

        return (
            wallet_c,
            wallet_r,
            {
                'authorized': authorized,
                'cosigner': (cosigner, int(cosigner, 0)),
                'recovery': accounts[3],
            }
        )
    return method


@pytest.fixture
def wallet_from_factory(accounts, get_logs_for_event, assert_tx_failed, w3, get_abi):
    def method(
            factory_wallet,
            full_wallet=False,
            recovery_addr=accounts[0],
            authorized_addr=accounts[1],
            cosigner_addr=accounts[2],
            deployer_addr=accounts[3],
            should_revert=False):

        core_wallet_abi = get_abi('CoreWallet')

        if full_wallet:
            func = factory_wallet.functions.deployFullWallet
        else:
            func = factory_wallet.functions.deployCloneWallet

        if should_revert:
            assert_tx_failed(func(recovery_addr, authorized_addr, int(cosigner_addr, 0)), {'from': deployer_addr})
            return (None, None)

        wallet_tx = func(recovery_addr, authorized_addr, int(cosigner_addr, 0)).transact({'from': deployer_addr})
        cloned_wallet_logs = get_logs_for_event(factory_wallet.events.WalletCreated, wallet_tx)

        assert cloned_wallet_logs[0].args.full == full_wallet, "WalletCreated full property is incorrect."

        return (
            w3.eth.contract(abi=core_wallet_abi, address=cloned_wallet_logs[0].args.wallet),
            w3.eth.getTransactionReceipt(wallet_tx)
        )

    return method


@pytest.fixture
def gascheck_deploy(accounts, deploy):
    def method(wallet_address):
        """
        Create a "CheckGasUse" contract instance
        """
        # Deploy the test contract
        (gas_c, gas_r) = deploy(
            contract="CheckGasUse",
            transaction={
                'from': accounts[0],
            },
            args={
                'wal': wallet_address,
            }
        )

        return (gas_c, gas_r)
    return method

@pytest.fixture
def erc20_deploy(accounts, deploy):
    def method():
        """
        Create a "TestToken" contract instance
        """
        # Deploy the test token contract
        (token_c, token_r) = deploy(
            contract="TestToken",
            transaction={
                'from': accounts[0],
            },
            args={}
        )

        return (token_c, token_r)
    return method

@pytest.fixture
def erc223_deploy(accounts, deploy):
    def method():
        """
        Create a "TestToken" contract instance
        """
        # Deploy the test token contract
        (token_c, token_r) = deploy(
            contract="ERC223Token",
            transaction={
                'from': accounts[0],
            },
            args={}
        )

        return (token_c, token_r)
    return method

@pytest.fixture
def erc721_deploy(accounts, deploy):
    def method():
        """
        Create a "ERC721Mintable" contract instance
        """
        # Deploy the test token contract
        (nft_c, nft_r) = deploy(
            contract="ERC721Mintable",
            transaction={
                'from': accounts[0],
            },
            args={}
        )

        return (nft_c, nft_r)
    return method

@pytest.fixture
def erc165_checker_deploy(accounts, deploy):
    def method():
        """
        Create a "ERC721Mintable" contract instance
        """
        # Deploy the test token contract
        (checker_c, checker_r) = deploy(
            contract="ERC165Query",
            transaction={
                'from': accounts[0],
            },
            args={}
        )

        return (checker_c, checker_r)
    return method

@pytest.fixture
def erc721_mock_deploy(accounts, deploy):
    def method():
        """
        Create a "ERC721TokenMock" contract instance
        """
        # Deploy the test token contract
        (nft_c, nft_r) = deploy(
            contract="ERC721TokenMock",
            transaction={
                'from': accounts[0],
            },
            args={
                'name': "Erroneous ERC721",
                'symbol': "TEST"
                }
        )

        return (nft_c, nft_r)
    return method

import pytest

@pytest.fixture
def zero_address():
    """
    Return the zero address as string
    """
    return '0x' + '00' * 20

@pytest.fixture
def admin_upgradability_deploy(accounts, deploy, instantiate):
    """
    Deploy a AdminUpgradeabilityProxy.
    Args: implementation contract that is delegate called.
    Admin will be set to accounts[10]
    Return: (Proxy instantiated as... , AdminUpgradeabilityProxy)
    """
    def method(implementation):
        (proxy, proxy_r) = deploy(
            contract="AdminUpgradeabilityProxy",
            transaction={
                'from': accounts[10],
            },
            args={
                '_implementation': implementation.address,
            }
        )

        instance = instantiate(proxy.address, implementation.abi)

        return (instance, proxy)
    return method

@pytest.fixture
def address_list_deploy(accounts, deploy):
    """
    Deploy an AddressList (whitelist or blacklist).
    """
    def method():
        (c, r) = deploy(
            contract="AddressList",
            transaction={
                'from': accounts[0],
            },
            args={}
        )
        return (c, r)
    return method

@pytest.fixture
def address_list_initialize_and_deploy(accounts, address_list_deploy, admin_upgradability_deploy):
    """
    Deploy an AddressList (whitelist or blacklist) then initialize it.
    """
    def method(name):
        (address_list, address_list_r) = address_list_deploy()
        (address_list_proxy, admin_proxy) = admin_upgradability_deploy(address_list)

        address_list_proxy.functions.initialize(name).transact({'from': accounts[0]})

        return (address_list_proxy, admin_proxy)
    return method

@pytest.fixture
def token_impl_deploy(accounts, deploy):
    """
    Deploy a TokenImpl.
    Requires deployment of BalanceSheet, AllowanceSheet and 2x AddressList's.
    """
    def method():
        (token_impl, token_impl_r) = deploy(
            contract="TokenImpl",
            transaction={
                'from': accounts[0],
            },
            args={}
        )
        return (token_impl, token_impl_r)
    return method

@pytest.fixture
def token_impl_initialize_and_deploy(accounts, deploy, address_list_initialize_and_deploy):
    """
    Deploy a TokenImpl.
    Also deploys and initializes whitelists and blacklists.
    """
    def method(name, symbol, decimals):
        (blacklist, blacklist_r) = address_list_initialize_and_deploy('Blacklist')
        (whitelist, whitelist_r) = address_list_initialize_and_deploy('Whitelist')

        (token_impl, token_impl_r) = deploy(
            contract="TokenImpl",
            transaction={
                'from': accounts[0],
            },
            args={}
        )

        token_impl.functions.initialize(\
            name,
            symbol,
            decimals,
            accounts[49],
            blacklist.address,
            whitelist.address).\
            transact({'from':accounts[0]})

        return (token_impl, token_impl_r)
    return method

@pytest.fixture
def token_proxy_deploy(accounts, deploy, token_impl_deploy, admin_upgradability_deploy):
    """
    Deploy a AdminUpgradeabilityProxy.
    Admin will be set to accounts[10]
    """
    def method():
        (token_impl, token_impl_r) = token_impl_deploy()

        (token_proxy, admin_proxy) = admin_upgradability_deploy(token_impl)

        return (token_proxy, admin_proxy)
    return method

@pytest.fixture
def token_proxy_initialize_and_deploy(accounts, deploy, token_proxy_deploy, address_list_initialize_and_deploy):
    """
    Deploy a AdminUpgradeabilityProxy instantiated as a TokenImpl.
    Proxy Admin will be set to accounts[10]
    """
    def method(name, symbol, decimals):
        (token_proxy, admin_proxy) = token_proxy_deploy()

        # Create lists for initialization
        (blacklist, blacklist_r) = address_list_initialize_and_deploy("Blacklist")
        (whitelist, whitelist_r) = address_list_initialize_and_deploy("Whitelist")

        # Initialize AdminUpgradeabilityProxy (TokenImpl.initialize())
        token_proxy.functions.initialize(\
            name,
            symbol,
            decimals,
            accounts[49],
            blacklist.address,
            whitelist.address).\
            transact({'from': accounts[0]})
        return (token_proxy, admin_proxy)
    return method

@pytest.fixture
def set_minter_with_limit(accounts):
    """
    Set accounts[2] as Minter with limit 10,000
    """
    def method(token, limit):
        token.functions.addMinterAdmin(accounts[1]).transact({'from': accounts[0]})
        token.functions.addMintLimiterAdmin(accounts[1]).transact({'from': accounts[0]})
        token.functions.addMinter(accounts[2]).transact({'from': accounts[1]})
        token.functions.addMintLimiter(accounts[2]).transact({'from': accounts[1]})
        token.functions.setMintLimit(accounts[2], limit).transact({'from': accounts[2]})
    return method

def test_address_list_deploy(accounts, address_list_deploy,
        address_list_initialize_and_deploy,
        assert_tx_failed):

    # Test deploy uninitialized
    (address_list, address_list_r) = address_list_deploy()

    # All values will be set to 0 until initialization
    assert address_list.address != 0
    assert address_list.functions.name().call() == ''

    # Test initialization, should only work once
    address_list.functions.initialize('List').transact({'from': accounts[0]})
    assert address_list.functions.name().call() == 'List'
    assert address_list.functions.isOwner(accounts[0]).call()
    assert address_list.functions.initialized().call()
    assert_tx_failed(address_list.functions.initialize('List2'), {'from': accounts[0]})

    # Initialize and deploy
    (address_list, admin_proxy) = address_list_initialize_and_deploy('List')

    # Verify Values, including initialized
    assert address_list.functions.name().call() == 'List'
    assert address_list.functions.isOwner(accounts[0]).call()
    assert address_list.functions.initialized().call()
    assert_tx_failed(address_list.functions.initialize('List2'), {'from': accounts[0]})


def test_token_impl_deploy( accounts, token_impl_deploy):
    (token_impl, token_impl_r) = token_impl_deploy()

    assert token_impl.address != 0
    assert token_impl.functions.decimals().call() == 0


def test_token_impl_initialize_and_deploy(accounts, token_impl_initialize_and_deploy):

    block_gas_limit = 8e6

    (token_impl, token_impl_r) = token_impl_initialize_and_deploy("Infinigold", "PMG", 3)

    # Verify initalized variables
    assert token_impl.address != 0
    assert token_impl.functions.name().call() == "Infinigold"
    assert token_impl.functions.symbol().call() == "PMG"
    assert token_impl.functions.decimals().call() == 3
    assert token_impl.functions.isOwner(accounts[0])

    # Below block gas limits
    assert token_impl_r['gasUsed'] < block_gas_limit

def test_token_proxy_deploy(accounts, token_proxy_deploy):

    (token_proxy, token_proxy_r) = token_proxy_deploy()

    assert token_proxy.address != 0
    assert token_proxy.functions.admin().call({'from': accounts[10]}) == accounts[10]
    assert token_proxy.functions.implementation().call({'from': accounts[10]}) != 0

def test_token_proxy_deploy(accounts, token_proxy_initialize_and_deploy, zero_address):

    # Deploys a TokenProxy and TokenImpl then casts the TokenProxy as a TokenImpl
    (token_proxy, admin_proxy) = token_proxy_initialize_and_deploy("Infinigold", "PMG", 3)

    # Verify initalized variables,
    # accounts[10] is Admin and can't use proxy calls, accounts[1] is Owner
    assert token_proxy.address != 0
    assert token_proxy.functions.name().call() == "Infinigold"
    assert token_proxy.functions.symbol().call() == "PMG"
    assert token_proxy.functions.decimals().call() == 3
    assert token_proxy.functions.isOwner(accounts[0]).call()
    assert token_proxy.functions.whitelist().call() != 0
    assert token_proxy.functions.blacklist().call() != 0
    assert token_proxy.functions.burnAddress().call() == accounts[49]

    # Confirm the overlaying TokeProxy is valid
    assert admin_proxy.address != 0
    assert admin_proxy.functions.admin().call({'from': accounts[10]}) == accounts[10]
    assert admin_proxy.functions.implementation().call({'from': accounts[10]}) != 0

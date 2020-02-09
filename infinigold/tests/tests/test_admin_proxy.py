def test_admin_proxy(
        accounts,
        assert_tx_failed,
        get_logs_for_event,
        token_impl_deploy,
        token_proxy_deploy,
        zero_address,
    ):

    # Deploy a TokenImpl and TokenProxy with accounts[10] as admin
    (token_proxy, admin_proxy) = token_proxy_deploy()

    assert admin_proxy.functions.admin().call({'from': accounts[10]}) == accounts[10]

    # Change admin from accounts[10] to accounts[1]
    tx = admin_proxy.functions.changeAdmin(accounts[1]).transact({'from': accounts[10]})
    assert admin_proxy.functions.admin().call({'from': accounts[1]}) == accounts[1]
    logs = get_logs_for_event(admin_proxy.events.AdminChanged, tx)
    assert logs[0]['args']['previousAdmin'] == accounts[10]
    assert logs[0]['args']['newAdmin'] == accounts[1]

    # Confirm you cannot change admin if not admin
    assert_tx_failed(admin_proxy.functions.changeAdmin(accounts[2]), {'from': accounts[2]})

    # Cannot set admin to 0
    assert_tx_failed(admin_proxy.functions.changeAdmin(zero_address), {'from': accounts[1]})

def test_admin_proxy_upgrade_to(
        accounts,
        assert_tx_failed,
        get_logs_for_event,
        token_impl_deploy,
        token_proxy_deploy,
        zero_address,
    ):

    # Deploy TokenProxy with accounts[10] as admin
    (token_proxy, admin_proxy) = token_proxy_deploy()

    # Create a new token_impl to be upgraded too
    (new_token_impl, new_token_impl_r) = token_impl_deploy()
    tx = admin_proxy.functions.upgradeTo(new_token_impl.address).transact({'from': accounts[10]})
    assert admin_proxy.functions.implementation().call({'from': accounts[10]}) == new_token_impl.address
    logs = get_logs_for_event(admin_proxy.events.Upgraded, tx)
    assert logs[0]['args']['implementation'] == new_token_impl.address

    # Not admin
    assert_tx_failed(admin_proxy.functions.upgradeTo(new_token_impl.address), {'from':accounts[1]})

    # Must be a contract
    assert_tx_failed(admin_proxy.functions.upgradeTo(accounts[2]), {'from': accounts[10]})

def test_admin_proxy_upgrade_to_and_call(
        accounts,
        assert_tx_failed,
        get_logs_for_event,
        token_impl_deploy,
        token_proxy_deploy,
        zero_address,
    ):

    # Deploy TokenProxy with accounts[10] as admin
    (token_proxy, admin_proxy) = token_proxy_deploy()

    # Create a new token_impl to be upgraded too
    (new_token_impl, new_token_impl_r) = token_impl_deploy()

    # Initialize new Implementation, be wary of overriding old values
    args_encoded =  new_token_impl.encodeABI(
        fn_name='name',
        args=[]
    )
    data = bytes.fromhex(args_encoded[2:])

    # Attempt upgradeToAndCall
    tx = admin_proxy.functions.upgradeToAndCall(new_token_impl.address, data).\
        transact({'from': accounts[10]})
    assert admin_proxy.functions.implementation().call({'from': accounts[10]}) == new_token_impl.address
    logs = get_logs_for_event(admin_proxy.events.Upgraded, tx)
    assert logs[0]['args']['implementation'] == new_token_impl.address

    # Not admin
    assert_tx_failed(admin_proxy.functions.upgradeToAndCall(new_token_impl.address, data),\
        {'from':accounts[1]})

    # Must be a contract
    assert_tx_failed(admin_proxy.functions.upgradeToAndCall(accounts[2], data),\
        {'from': accounts[10]})

def test_admin_proxy_upgrade_to_values(
        accounts,
        address_list_initialize_and_deploy,
        assert_tx_failed,
        get_logs_for_event,
        set_minter_with_limit,
        token_impl_deploy,
        token_proxy_initialize_and_deploy,
        zero_address,
    ):

    # Deploy TokenProxy with accounts[10] as admin
    (token_proxy_as_impl, admin_proxy) = token_proxy_initialize_and_deploy("Infinigold", "PMG", 2)

    ## Set some values, to ensure the remain after changing
    # MinterAdmin accounts[1], Minter and limit 1000 to accounts[2]
    set_minter_with_limit(token_proxy_as_impl, 1000)

    # Set balances 10 in accounts[3], 20 in accounts[4], reducing limitOf accounts[2] to 950
    token_proxy_as_impl.functions.mint(accounts[3], 30, 1).transact({'from': accounts[2]})
    token_proxy_as_impl.functions.transfer(accounts[4], 20).transact({'from': accounts[3]})

    # Set approve 10 from accounts[4] to accounts[5]
    token_proxy_as_impl.functions.approve(accounts[5], 10).transact({'from': accounts[4]})

    # Store addresses of whitelist and blacklist to ensure they don't change
    whitelist = token_proxy_as_impl.functions.whitelist().call()
    blacklist = token_proxy_as_impl.functions.blacklist().call()

    # Upgrade to a new TokenImpl
    (new_token_impl, new_token_impl_r) = token_impl_deploy()
    admin_proxy.functions.upgradeTo(new_token_impl.address).transact({'from': accounts[10]})

    ## Check all values set above remain
    assert token_proxy_as_impl.functions.totalSupply().call() == 30
    assert token_proxy_as_impl.functions.balanceOf(accounts[3]).call() == 10
    assert token_proxy_as_impl.functions.balanceOf(accounts[4]).call() == 20
    assert token_proxy_as_impl.functions.allowance(accounts[4], accounts[5]).call() == 10

    assert token_proxy_as_impl.functions.whitelist().call() == whitelist
    assert token_proxy_as_impl.functions.blacklist().call() == blacklist

    assert token_proxy_as_impl.functions.isMinterAdmin(accounts[1]).call()
    assert token_proxy_as_impl.functions.isMinter(accounts[2]).call()
    assert token_proxy_as_impl.functions.mintLimitOf(accounts[2]).call() == 970

    assert token_proxy_as_impl.functions.initialized().call()

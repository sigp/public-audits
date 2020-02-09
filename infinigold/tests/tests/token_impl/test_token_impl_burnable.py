def test_token_impl_update_burn_address(
        token_impl_initialize_and_deploy,
        accounts,
        assert_tx_failed,
        get_logs_for_event):

    # Deploy a TokenImpl with burnAddress accounts[49]
    (token_impl, token_impl_r) = token_impl_initialize_and_deploy("Infinigold", "IFG", 2)

    # Test isBurnAddress
    assert token_impl.functions.isBurnAddress(accounts[49]).call()

    # Test ability to update BurnAddress
    tx = token_impl.functions.updateBurnAddress(accounts[47]).transact({'from': accounts[0]})
    assert token_impl.functions.burnAddress().call() == accounts[47]
    logs = get_logs_for_event(token_impl.events.BurnAddressUpdated, tx)
    assert logs[0]['args']['previousBurnAddress'] == accounts[49]
    assert logs[0]['args']['newBurnAddress'] == accounts[47]

    # Change BurnAddress while not owner
    assert_tx_failed(token_impl.functions.updateBurnAddress(accounts[48]), {'from': accounts[1]})

def test_token_impl_burn(
        accounts,
        token_impl_initialize_and_deploy,
        address_list_initialize_and_deploy,
        set_minter_with_limit,
        zero_address,
        get_logs_for_event):

    # Create a TokenImpl with burnAddress accounts[49]
    (token_impl, token_impl_r) = token_impl_initialize_and_deploy("Infinigold", "IFG", 2)

    # Mint 1,000 tokens to accounts[3]
    set_minter_with_limit(token_impl, 10000)
    token_impl.functions.mint(accounts[3], 1000, 1).transact({'from': accounts[2]})

    # Create new whitelist and add accounts[3]
    (whitelist, whitelist_r) = address_list_initialize_and_deploy("Whitelist")
    token_impl.functions.updateWhitelist(whitelist.address).transact({'from': accounts[0]})
    whitelist.functions.addListerAdmin(accounts[1]).transact({'from': accounts[0]})
    whitelist.functions.addLister(accounts[2]).transact({'from': accounts[1]})
    whitelist.functions.addAddress(accounts[3]).transact({'from': accounts[2]})

    # Burn 100 tokens  from accounts[3]
    tx = token_impl.functions.transfer(accounts[49], 100).transact({'from': accounts[3]})
    assert token_impl.functions.balanceOf(accounts[3]).call() == 900
    assert token_impl.functions.totalSupply().call() == 900
    logs = get_logs_for_event(token_impl.events.Burn, tx)
    assert logs[0]['args']['burner'] == accounts[3]
    assert logs[0]['args']['value'] == 100
    logs = get_logs_for_event(token_impl.events.Transfer, tx)
    assert logs[0]['args']['from'] == accounts[3]
    assert logs[0]['args']['to'] == zero_address
    assert logs[0]['args']['value'] == 100

    # burn 900 tokens
    tx = token_impl.functions.transfer(accounts[49], 900).transact({'from': accounts[3]})
    assert token_impl.functions.balanceOf(accounts[3]).call() == 0
    assert token_impl.functions.totalSupply().call() == 0
    logs = get_logs_for_event(token_impl.events.Burn, tx)
    assert logs[0]['args']['burner'] == accounts[3]
    assert logs[0]['args']['value'] == 900
    logs = get_logs_for_event(token_impl.events.Transfer, tx)
    assert logs[0]['args']['from'] == accounts[3]
    assert logs[0]['args']['to'] == zero_address
    assert logs[0]['args']['value'] == 900


def test_token_impl_burn_invalid(
        accounts,
        address_list_initialize_and_deploy,
        assert_tx_failed,
        set_minter_with_limit,
        token_impl_initialize_and_deploy,
        zero_address,
        get_logs_for_event):

    # Create a TokenImpl with burnAddress accounts[49]
    (token_impl, token_impl_r) = token_impl_initialize_and_deploy("Infinigold", "IFG", 2)

    # Mint 10,000 tokens to accounts[3] and accounts[4]
    set_minter_with_limit(token_impl, 10000)
    token_impl.functions.mint(accounts[3], 5000, 1).transact({'from': accounts[2]})
    token_impl.functions.mint(accounts[4], 5000, 2).transact({'from': accounts[2]})

    # Create new whitelist and add accounts[3]
    (whitelist, blacklist_r) = address_list_initialize_and_deploy("Whitelist")
    token_impl.functions.updateWhitelist(whitelist.address).transact({'from': accounts[0]})
    whitelist.functions.addListerAdmin(accounts[1]).transact({'from': accounts[0]})
    whitelist.functions.addLister(accounts[2]).transact({'from': accounts[1]})
    whitelist.functions.addAddress(accounts[3]).transact({'from': accounts[2]})

    # Burn more than balance
    assert_tx_failed(token_impl.functions.transfer(accounts[49], 99999), {'from': accounts[3]})

    # Not a whitelisted account
    assert_tx_failed(token_impl.functions.transfer(accounts[49], 100), {'from': accounts[4]})

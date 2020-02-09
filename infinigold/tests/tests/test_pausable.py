def test_pausing(
        token_proxy_initialize_and_deploy,
        accounts,
        get_logs_for_event):

    # Create a TokenImpl
    (token_proxy_as_impl, token_proxy) = token_proxy_initialize_and_deploy("Infinigold", "IFG", 2)

    # Add pauser role for accounts[2]
    token_proxy_as_impl.functions.addPauserAdmin(accounts[1]).transact({'from': accounts[0]})
    token_proxy_as_impl.functions.addPauser(accounts[2]).transact({'from': accounts[1]})
    token_proxy_as_impl.functions.addUnpauser(accounts[2]).transact({'from': accounts[1]})

    # Should be initiated as unpaused
    assert not token_proxy_as_impl.functions.paused().call()

    # Attempt to pause
    tx = token_proxy_as_impl.functions.pause().transact({'from': accounts[2]})
    assert token_proxy_as_impl.functions.paused().call()
    logs = get_logs_for_event(token_proxy_as_impl.events.Paused, tx)
    assert logs[0]['args']['pauser'] == accounts[2]

    # Unpause
    tx = token_proxy_as_impl.functions.unpause().transact({'from': accounts[2]})
    assert not token_proxy_as_impl.functions.paused().call()
    logs = get_logs_for_event(token_proxy_as_impl.events.Unpaused, tx)
    assert logs[0]['args']['unpauser'] == accounts[2]

def test_pausing_invalid(
        token_proxy_initialize_and_deploy,
        accounts,
        assert_tx_failed,
        get_logs_for_event):

    # Create a TokenImpl
    (token_proxy_as_impl, token_proxy) = token_proxy_initialize_and_deploy("Infinigold", "IFG", 2)

    # Add pauser role for accounts[2]
    token_proxy_as_impl.functions.addPauserAdmin(accounts[1]).transact({'from': accounts[0]})
    token_proxy_as_impl.functions.addPauser(accounts[2]).transact({'from': accounts[1]})

    # Not a pauser
    assert_tx_failed(token_proxy_as_impl.functions.pause(), {'from': accounts[3]})

    # Unpause when not paused
    assert_tx_failed(token_proxy_as_impl.functions.unpause(), {'from': accounts[2]})

    # Unpause when not pauser
    token_proxy_as_impl.functions.pause().transact({'from': accounts[2]})
    assert_tx_failed(token_proxy_as_impl.functions.unpause(), {'from': accounts[3]})

def test_pausing_owner(
        token_proxy_initialize_and_deploy,
        accounts,
        get_logs_for_event):

    # Create a TokenImpl
    (token_proxy_as_impl, token_proxy) = token_proxy_initialize_and_deploy("Infinigold", "IFG", 2)

    # Should be initiated as unpaused
    assert not token_proxy_as_impl.functions.paused().call()

    # Attempt to pause
    tx = token_proxy_as_impl.functions.pause().transact({'from': accounts[0]})
    assert token_proxy_as_impl.functions.paused().call()
    logs = get_logs_for_event(token_proxy_as_impl.events.Paused, tx)
    assert logs[0]['args']['pauser'] == accounts[0]

    # Unpause
    tx = token_proxy_as_impl.functions.unpause().transact({'from': accounts[0]})
    assert not token_proxy_as_impl.functions.paused().call()
    logs = get_logs_for_event(token_proxy_as_impl.events.Unpaused, tx)
    assert logs[0]['args']['unpauser'] == accounts[0]

def test_paused_modifier(
        accounts,
        assert_tx_failed,
        address_list_initialize_and_deploy,
        get_logs_for_event,
        set_minter_with_limit,
        token_proxy_initialize_and_deploy):

    # Create a TokenImpl
    (token_proxy_as_impl, token_proxy) = token_proxy_initialize_and_deploy("Infinigold", "IFG", 2)

    # Set accounts[2] MintLimit to 10,000, Mint 1,000 tokens to accounts[3]
    set_minter_with_limit(token_proxy_as_impl, 10000)
    token_proxy_as_impl.functions.mint(accounts[3], 1000, 1).transact({'from': accounts[2]})

    # Create new whitelist and add accounts[3]
    (whitelist, whitelist_r) = address_list_initialize_and_deploy("Whitelist")
    token_proxy_as_impl.functions.updateWhitelist(whitelist.address).transact({'from': accounts[0]})
    whitelist.functions.addListerAdmin(accounts[1]).transact({'from': accounts[0]})
    whitelist.functions.addLister(accounts[2]).transact({'from': accounts[1]})
    whitelist.functions.addAddress(accounts[3]).transact({'from': accounts[2]})

    # Set approval
    token_proxy_as_impl.functions.approve(accounts[4], 100).transact({'from': accounts[3]})

    # Pause from accounts[2]
    token_proxy_as_impl.functions.addPauserAdmin(accounts[1]).transact({'from': accounts[0]})
    token_proxy_as_impl.functions.addPauser(accounts[2]).transact({'from': accounts[1]})
    token_proxy_as_impl.functions.pause().transact({'from': accounts[2]})

    # Transfer, Minting, Approve, increase/decrease Allowance and
    # TransferFrom should fail when paused
    assert_tx_failed(token_proxy_as_impl.functions.transfer(accounts[5], 50), {'from': accounts[3]})
    assert_tx_failed(token_proxy_as_impl.functions.mint(accounts[5], 50, 2), {'from': accounts[2]})
    assert_tx_failed(token_proxy_as_impl.functions.approve(accounts[5], 50), {'from': accounts[3]})
    assert_tx_failed(token_proxy_as_impl.functions.increaseAllowance(accounts[4], 50), {'from': accounts[3]})
    assert_tx_failed(token_proxy_as_impl.functions.decreaseAllowance(accounts[4], 50), {'from': accounts[3]})
    assert_tx_failed(token_proxy_as_impl.functions.transferFrom(accounts[3], accounts[4], 50), {'from': accounts[4]})

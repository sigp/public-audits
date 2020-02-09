def test_token_impl_notBlacklisted(
        token_impl_initialize_and_deploy,
        accounts,
        address_list_initialize_and_deploy,
        set_minter_with_limit,
        assert_tx_failed,
        get_logs_for_event):

    # Deploy a TokenImpl and AddressList(blacklist)
    # Owner: accounts[0], ListerAdmin: accounts[1], Lister: accounts[2]
    (token_impl, token_impl_r) = token_impl_initialize_and_deploy("Infinigold", "IFG", 2)
    (blacklist, blacklist_r) = address_list_initialize_and_deploy("Blacklist")
    token_impl.functions.updateBlacklist(blacklist.address).transact({'from': accounts[0]})
    blacklist.functions.addListerAdmin(accounts[1]).transact({'from': accounts[0]})
    blacklist.functions.addLister(accounts[2]).transact({'from': accounts[1]})

    # Mint tokens to accounts[3 to 6]
    set_minter_with_limit(token_impl, 10000)
    token_impl.functions.mint(accounts[3], 250, 1).transact({'from': accounts[2]})
    token_impl.functions.mint(accounts[4], 250, 2).transact({'from': accounts[2]})
    token_impl.functions.mint(accounts[5], 250, 3).transact({'from': accounts[2]})
    token_impl.functions.mint(accounts[6], 250, 4).transact({'from': accounts[2]})

    # Set approvals for testing TransferFrom
    token_impl.functions.approve(accounts[3], 50).transact({'from': accounts[6]})
    token_impl.functions.approve(accounts[3], 50).transact({'from': accounts[4]})
    token_impl.functions.approve(accounts[6], 50).transact({'from': accounts[4]})


    # Add blacklisted address, accounts[3] and accounts[4]
    blacklist.functions.addAddress(accounts[3]).transact({'from': accounts[2]})
    blacklist.functions.addAddress(accounts[4]).transact({'from': accounts[2]})

    # Cannot approve or recieve approval when blacklisted
    assert_tx_failed(token_impl.functions.approve(accounts[5], 10), {'from': accounts[3]})
    assert_tx_failed(token_impl.functions.approve(accounts[3], 10), {'from': accounts[5]})
    assert_tx_failed(token_impl.functions.approve(accounts[3], 10), {'from': accounts[4]})

    # Cannot transfer when blacklisted
    assert_tx_failed(token_impl.functions.transfer(accounts[5], 10), {'from': accounts[3]})
    assert_tx_failed(token_impl.functions.transfer(accounts[3], 10), {'from': accounts[5]})
    assert_tx_failed(token_impl.functions.transfer(accounts[3], 10), {'from': accounts[4]})

    # Cannot increase or decrease allowance while blacklisted
    assert_tx_failed(token_impl.functions.increaseAllowance(accounts[5], 10),
        {'from': accounts[3]})
    assert_tx_failed(token_impl.functions.increaseAllowance(accounts[3], 10),
        {'from': accounts[5]})
    assert_tx_failed(token_impl.functions.increaseAllowance(accounts[3], 10),
        {'from': accounts[4]})
    assert_tx_failed(token_impl.functions.decreaseAllowance(accounts[3], 10),
        {'from': accounts[6]})
    assert_tx_failed(token_impl.functions.decreaseAllowance(accounts[3], 10),
        {'from': accounts[4]})
    assert_tx_failed(token_impl.functions.decreaseAllowance(accounts[6], 10),
        {'from': accounts[4]})

    # Cannot mint when blacklisted (Minter is account[2])
    assert_tx_failed(token_impl.functions.mint(accounts[3], 10, 5), {'from': accounts[2]})
    blacklist.functions.addAddress(accounts[2]).transact({'from': accounts[2]})
    assert_tx_failed(token_impl.functions.mint(accounts[5], 10, 6), {'from': accounts[2]})
    assert_tx_failed(token_impl.functions.transfer(accounts[3], 10), {'from': accounts[2]})

    # Cannot transferFrom when blacklisted
    assert_tx_failed(token_impl.functions.transferFrom(accounts[6], accounts[3], 20),
        {'from': accounts[3]})
    assert_tx_failed(token_impl.functions.transferFrom(accounts[4], accounts[3], 20),
        {'from': accounts[3]})
    assert_tx_failed(token_impl.functions.transferFrom(accounts[4], accounts[6], 20),
        {'from': accounts[7]})
    assert_tx_failed(token_impl.functions.transferFrom(accounts[4], accounts[6], 20),
        {'from': accounts[6]})


def test_token_impl_update_blacklist(
        token_impl_initialize_and_deploy,
        accounts,
        address_list_initialize_and_deploy,
        assert_tx_failed,
        get_logs_for_event,
        zero_address):

    ### Valid Operations
    # Deploy a TokenImpl and AddressList(blacklist) with accounts[0] as owner
    (token_impl, token_impl_r) = token_impl_initialize_and_deploy("Infinigold", "IFG", 2)
    (blacklist, blacklist_r) = address_list_initialize_and_deploy("Blacklist")

    # Update to new blacklist
    tx = token_impl.functions.updateBlacklist(blacklist.address).transact({'from': accounts[0]})
    assert token_impl.functions.blacklist().call() == blacklist.address
    assert token_impl.functions.isBlacklist(blacklist.address).call()
    logs = get_logs_for_event(token_impl.events.BlacklistUpdated, tx)
    assert logs[0]['args']['newBlacklist'] == blacklist.address

    # Update blacklist again
    previousAddress = blacklist.address
    (blacklist, blacklist_r) = address_list_initialize_and_deploy("Blacklist")
    tx = token_impl.functions.updateBlacklist(blacklist.address).transact({'from': accounts[0]})
    assert token_impl.functions.isBlacklist(blacklist.address).call()
    logs = get_logs_for_event(token_impl.events.BlacklistUpdated, tx)
    assert logs[0]['args']['previousBlacklist'] == previousAddress
    assert logs[0]['args']['newBlacklist'] == blacklist.address

    ### Inalid Operations
    # Zero address
    assert_tx_failed(token_impl.functions.updateBlacklist(zero_address), {'from': accounts[0]})

    # Needs to be a contract
    assert_tx_failed(token_impl.functions.updateBlacklist(accounts[0]), {'from': accounts[0]})

    # Can only be updated by owner
    assert_tx_failed(token_impl.functions.updateBlacklist(blacklist.address), {'from': accounts[5]})


def test_token_impl_is_black_listed(
        token_impl_initialize_and_deploy,
        address_list_initialize_and_deploy,
        accounts,
        assert_tx_failed,
        get_logs_for_event):

    # Deploy a TokenImpl and AddressList(blacklist)
    # Owner: accounts[0], ListerAdmin: accounts[1], Lister: accounts[2]
    (token_impl, token_impl_r) = token_impl_initialize_and_deploy("Infinigold", "IFG", 2)
    (blacklist, blacklist_r) = address_list_initialize_and_deploy("Blacklist")
    token_impl.functions.updateBlacklist(blacklist.address).transact({'from': accounts[0]})
    blacklist.functions.addListerAdmin(accounts[1]).transact({'from': accounts[0]})
    blacklist.functions.addLister(accounts[2]).transact({'from': accounts[1]})
    blacklist.functions.addUnlister(accounts[2]).transact({'from': accounts[1]})

    # Test Blacklist
    assert not token_impl.functions.isBlacklisted(accounts[3]).call()
    blacklist.functions.addAddress(accounts[3]).transact({'from': accounts[2]})
    assert token_impl.functions.isBlacklisted(accounts[3]).call()
    blacklist.functions.removeAddress(accounts[3]).transact({'from': accounts[2]})
    assert not token_impl.functions.isBlacklisted(accounts[3]).call()


def test_token_impl_is_white_listed(
        token_impl_initialize_and_deploy,
        address_list_initialize_and_deploy,
        accounts,
        assert_tx_failed,
        get_logs_for_event):

    # Deploy a TokenImpl and AddressList(whitelist)
    # Owner: accounts[0], ListerAdmin: accounts[1], Lister: accounts[2]
    (token_impl, token_impl_r) = token_impl_initialize_and_deploy("Infinigold", "IFG", 2)
    (whitelist, whitelist_r) = address_list_initialize_and_deploy("Whitelist")
    token_impl.functions.updateWhitelist(whitelist.address).transact({'from': accounts[0]})
    whitelist.functions.addListerAdmin(accounts[1]).transact({'from': accounts[0]})
    whitelist.functions.addLister(accounts[2]).transact({'from': accounts[1]})
    whitelist.functions.addUnlister(accounts[2]).transact({'from': accounts[1]})

    # Test Whitelist
    assert not token_impl.functions.isWhitelisted(accounts[3]).call()
    whitelist.functions.addAddress(accounts[3]).transact({'from': accounts[2]})
    assert token_impl.functions.isWhitelisted(accounts[3]).call()
    whitelist.functions.removeAddress(accounts[3]).transact({'from': accounts[2]})
    assert not token_impl.functions.isWhitelisted(accounts[3]).call()


def test_token_impl_update_whitelist(
        token_impl_initialize_and_deploy,
        accounts,
        address_list_initialize_and_deploy,
        assert_tx_failed,
        get_logs_for_event,
        zero_address):

    # Deploy a TokenImpl and AddressList(whitelist) with accounts[0] as owner
    (token_impl, token_impl_r) = token_impl_initialize_and_deploy("Infinigold", "IFG", 2)
    (whitelist, whitelist_r) = address_list_initialize_and_deploy("Whitelist")

    ### Valid Operations
    # Update to new whitelist
    tx = token_impl.functions.updateWhitelist(whitelist.address).transact({'from': accounts[0]})
    assert token_impl.functions.whitelist().call() == whitelist.address
    assert token_impl.functions.isWhitelist(whitelist.address).call()
    logs = get_logs_for_event(token_impl.events.WhitelistUpdated, tx)
    assert logs[0]['args']['newWhitelist'] == whitelist.address

    # Update whitelist again
    previousAddress = whitelist.address
    (whitelist, whitelist_r) = address_list_initialize_and_deploy("Whitelist")
    tx = token_impl.functions.updateWhitelist(whitelist.address).transact({'from': accounts[0]})
    assert token_impl.functions.isWhitelist(whitelist.address).call()
    logs = get_logs_for_event(token_impl.events.WhitelistUpdated, tx)
    assert logs[0]['args']['previousWhitelist'] == previousAddress
    assert logs[0]['args']['newWhitelist'] == whitelist.address

    ### Invalid Operations
    # Zero address
    assert_tx_failed(token_impl.functions.updateWhitelist(zero_address), {'from': accounts[0]})

    # Needs to be a contract
    assert_tx_failed(token_impl.functions.updateWhitelist(accounts[0]), {'from': accounts[0]})

    # Can only be updated by owner
    assert_tx_failed(token_impl.functions.updateWhitelist(whitelist.address), {'from': accounts[5]})

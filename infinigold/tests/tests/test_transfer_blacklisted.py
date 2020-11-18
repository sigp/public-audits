def test_transfer_blacklist(
        accounts,
        set_minter_with_limit,
        token_proxy_initialize_and_deploy,
        address_list_initialize_and_deploy,
        assert_tx_failed,
        get_logs_for_event):

    (token_proxy_as_impl, token_proxy) = token_proxy_initialize_and_deploy("Infinigold", "PMGT", 2)

    # Define test users
    owner = accounts[0]
    alice = accounts[1]
    bob = accounts[2]
    carol = accounts[3]
    david = accounts[4]
    eve = accounts[5]
    zero_address = '0x' + '00' * 20

    # Define bob as minter and mint 1,000 tokens to carol
    set_minter_with_limit(token_proxy_as_impl, 1000)
    token_proxy_as_impl.functions.mint(carol, 1000, 1).transact({'from': bob})

    # Send 200 tokens to David
    token_proxy_as_impl.functions.transfer(david, 200).transact({'from':carol})

    # Set up a new blacklist with Bob as a lister
    (blacklist, _) = address_list_initialize_and_deploy("Whitelist")
    token_proxy_as_impl.functions.updateBlacklist(blacklist.address).transact({'from': owner})
    blacklist.functions.addListerAdmin(alice).transact({'from': owner})
    blacklist.functions.addLister(bob).transact({'from': alice})
    blacklist.functions.addUnlister(bob).transact({'from': alice})

    # Blacklist David
    blacklist.functions.addAddress(david).transact({'from':bob})
    assert token_proxy_as_impl.functions.isBlacklisted(david).call() == 1

    # Ensure David still has his tokens
    assert token_proxy_as_impl.functions.balanceOf(david).call() == 200

    # Ensure Bob doesn't have any tokens
    assert token_proxy_as_impl.functions.balanceOf(bob).call() == 0

    # Move some of David's tokens to Bob via transferFromBlacklisted
    token_proxy_as_impl.functions.transferFromBlacklisted(david, bob, 100).transact({'from': owner})
    assert token_proxy_as_impl.functions.balanceOf(bob).call() == 100
    assert token_proxy_as_impl.functions.balanceOf(david).call() == 100


def test_transfer_blacklist_invalid(
        accounts,
        set_minter_with_limit,
        token_proxy_initialize_and_deploy,
        address_list_initialize_and_deploy,
        assert_tx_failed,
        get_logs_for_event):

    (token_proxy_as_impl, token_proxy) = token_proxy_initialize_and_deploy("Infinigold", "PMGT", 2)

    # Define test users
    owner = accounts[0]
    alice = accounts[1]
    bob = accounts[2]
    carol = accounts[3]
    david = accounts[4]
    eve = accounts[5]
    zero_address = '0x' + '00' * 20

    # Define bob as minter and mint 1,000 tokens to carol
    set_minter_with_limit(token_proxy_as_impl, 1000)
    token_proxy_as_impl.functions.mint(carol, 1000, 1).transact({'from': bob})

    # Send 200 tokens to David
    token_proxy_as_impl.functions.transfer(david, 200).transact({'from':carol})

    # Set up a new blacklist with Bob as a lister
    (blacklist, _) = address_list_initialize_and_deploy("Whitelist")
    token_proxy_as_impl.functions.updateBlacklist(blacklist.address).transact({'from': owner})
    blacklist.functions.addListerAdmin(alice).transact({'from': owner})
    blacklist.functions.addLister(bob).transact({'from': alice})
    blacklist.functions.addUnlister(bob).transact({'from': alice})

    # Blacklist David
    blacklist.functions.addAddress(david).transact({'from':bob})
    assert token_proxy_as_impl.functions.isBlacklisted(david).call() == 1

    # Make sure owners can't call transferFromBlacklisted for non-blacklisted accounts
    assert_tx_failed(token_proxy_as_impl.functions.transferFromBlacklisted(carol, bob, 200), {'from': owner})

    # Make sure 0 value transfers revert
    assert_tx_failed(token_proxy_as_impl.functions.transferFromBlacklisted(david, bob, 0), {'from': owner})

    # Make sure transfers to the zero address revert:
    assert_tx_failed(token_proxy_as_impl.functions.transferFromBlacklisted(david, zero_address, 100), {'from': owner})

    # Remove David from the Blacklist
    blacklist.functions.removeAddress(david).transact({'from':bob})

    # Make sure an owner can no longer transfer David's tokens
    assert_tx_failed(token_proxy_as_impl.functions.transferFromBlacklisted(david, bob, 100), {'from': owner})

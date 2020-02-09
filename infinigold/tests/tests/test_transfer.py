def test_transfer(
        accounts,
        set_minter_with_limit,
        token_proxy_initialize_and_deploy,
        get_logs_for_event):

    (token_proxy_as_impl, token_proxy) = token_proxy_initialize_and_deploy("Infinigold", "PMG", 2)

    # Mint 1,000 tokens to accounts[3]
    set_minter_with_limit(token_proxy_as_impl, 1000)
    token_proxy_as_impl.functions.mint(accounts[3], 1000, 1).transact({'from': accounts[2]})

    # Transfer 50 from accounts[3] to accounts[4]
    tx = token_proxy_as_impl.functions.transfer(accounts[4], 50).transact({'from':accounts[3]})
    assert token_proxy_as_impl.functions.balanceOf(accounts[3]).call() == 950
    assert token_proxy_as_impl.functions.balanceOf(accounts[4]).call() == 50
    logs = get_logs_for_event(token_proxy_as_impl.events.Transfer, tx)
    assert logs[0]['args']['from'] == accounts[3]
    assert logs[0]['args']['to'] == accounts[4]
    assert logs[0]['args']['value'] == 50

    # Transfer 30 from accounts[3] to accounts[5] and 40 from accounts[4] to accounts[5]
    token_proxy_as_impl.functions.transfer(accounts[5], 30).transact({'from':accounts[3]})
    tx = token_proxy_as_impl.functions.transfer(accounts[5], 40).transact({'from':accounts[4]})
    assert token_proxy_as_impl.functions.balanceOf(accounts[3]).call() == 920
    assert token_proxy_as_impl.functions.balanceOf(accounts[4]).call() == 10
    assert token_proxy_as_impl.functions.balanceOf(accounts[5]).call() == 70
    logs = get_logs_for_event(token_proxy_as_impl.events.Transfer, tx)
    assert logs[0]['args']['from'] == accounts[4]
    assert logs[0]['args']['to'] == accounts[5]
    assert logs[0]['args']['value'] == 40

def test_transfer_invalid(
        accounts,
        assert_tx_failed,
        get_logs_for_event,
        set_minter_with_limit,
        token_proxy_initialize_and_deploy,
        zero_address):

    (token_proxy_as_impl, token_proxy) = token_proxy_initialize_and_deploy("Infinigold", "IFG", 2)

    # Mint 1,000 tokens to accounts[3]
    set_minter_with_limit(token_proxy_as_impl, 10000)
    token_proxy_as_impl.functions.mint(accounts[3], 1000, 1).transact({'from': accounts[2]})

    # Not enough balance
    assert_tx_failed(token_proxy_as_impl.functions.transfer(accounts[5], 2**256 - 1), {'from':accounts[3]})
    assert_tx_failed(token_proxy_as_impl.functions.transfer(accounts[5], 2**256 - 1), {'from':accounts[4]})

    # Send to zero address
    assert_tx_failed(token_proxy_as_impl.functions.transfer(zero_address, 1), {'from':accounts[3]})

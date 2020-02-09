def test_token_impl_transfer(
        accounts,
        set_minter_with_limit,
        token_impl_initialize_and_deploy,
        get_logs_for_event):

    (token_impl, token_impl_r) = token_impl_initialize_and_deploy("Infinigold", "IFG", 2)

    # Mint 1,000 tokens to accounts[3]
    set_minter_with_limit(token_impl, 1000)
    token_impl.functions.mint(accounts[3], 1000, 1).transact({'from': accounts[2]})

    # Transfer 50 from accounts[3] to accounts[4]
    tx = token_impl.functions.transfer(accounts[4], 50).transact({'from':accounts[3]})
    assert token_impl.functions.balanceOf(accounts[3]).call() == 950
    assert token_impl.functions.balanceOf(accounts[4]).call() == 50
    logs = get_logs_for_event(token_impl.events.Transfer, tx)
    assert logs[0]['args']['from'] == accounts[3]
    assert logs[0]['args']['to'] == accounts[4]
    assert logs[0]['args']['value'] == 50

    # Transfer 30 from accounts[3] to accounts[5] and 40 from accounts[4] to accounts[5]
    token_impl.functions.transfer(accounts[5], 30).transact({'from':accounts[3]})
    tx = token_impl.functions.transfer(accounts[5], 40).transact({'from':accounts[4]})
    assert token_impl.functions.balanceOf(accounts[3]).call() == 920
    assert token_impl.functions.balanceOf(accounts[4]).call() == 10
    assert token_impl.functions.balanceOf(accounts[5]).call() == 70
    logs = get_logs_for_event(token_impl.events.Transfer, tx)
    assert logs[0]['args']['from'] == accounts[4]
    assert logs[0]['args']['to'] == accounts[5]
    assert logs[0]['args']['value'] == 40

def test_token_impl_transfer_invalid(
        accounts,
        token_impl_initialize_and_deploy,
        assert_tx_failed,
        get_logs_for_event,
        set_minter_with_limit,
        zero_address):

    (token_impl, token_impl_r) = token_impl_initialize_and_deploy("Infinigold", "IFG", 2)

    # Mint 1,000 tokens to accounts[3]
    set_minter_with_limit(token_impl, 1000)
    token_impl.functions.mint(accounts[3], 1000, 1).transact({'from': accounts[2]})

    # Not enough balance
    assert_tx_failed(token_impl.functions.transfer(accounts[5], 2**256 - 1), {'from':accounts[3]})
    assert_tx_failed(token_impl.functions.transfer(accounts[5], 2**256 - 1), {'from':accounts[4]})

    # Send to zero address
    assert_tx_failed(token_impl.functions.transfer(zero_address, 1), {'from':accounts[3]})

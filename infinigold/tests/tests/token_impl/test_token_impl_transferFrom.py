def test_token_impl_transferFrom(
        token_impl_initialize_and_deploy,
        accounts,
        set_minter_with_limit,
        get_logs_for_event):

    # Deploy a TokenImpl
    (token_impl, token_impl_r) = token_impl_initialize_and_deploy("Infinigold", "IFG", 2)

    # Mint tokens to accounts[3 to 5]
    set_minter_with_limit(token_impl, 1000)
    token_impl.functions.mint(accounts[3], 250, 1).transact({'from': accounts[2]})
    token_impl.functions.mint(accounts[4], 250, 2).transact({'from': accounts[2]})
    token_impl.functions.mint(accounts[5], 250, 3).transact({'from': accounts[2]})

    # Approval from accounts[3] to accounts[4] of value 100
    token_impl.functions.approve(accounts[4], 100).transact({'from': accounts[3]})

    # TransferFrom accounts[3] to accounts[4] value 10
    tx = token_impl.functions.transferFrom(accounts[3], accounts[4], 10).transact({'from': accounts[4]})
    assert token_impl.functions.balanceOf(accounts[3]).call() == 240
    assert token_impl.functions.balanceOf(accounts[4]).call() == 260
    assert token_impl.functions.allowance(accounts[3], accounts[4]).call() == 90
    logs = get_logs_for_event(token_impl.events.Transfer, tx)
    assert logs[0]['args']['from'] == accounts[3]
    assert logs[0]['args']['to'] == accounts[4]
    assert logs[0]['args']['value'] == 10
    logs = get_logs_for_event(token_impl.events.Approval, tx)
    assert logs[0]['args']['owner'] == accounts[3]
    assert logs[0]['args']['spender'] == accounts[4]
    assert logs[0]['args']['value'] == 90

    # TransferFrom accounts[3] to accounts[4] the remaining balance (90)
    tx = token_impl.functions.transferFrom(accounts[3], accounts[4], 90).transact({'from': accounts[4]})
    assert token_impl.functions.balanceOf(accounts[3]).call() == 150
    assert token_impl.functions.balanceOf(accounts[4]).call() == 350
    assert token_impl.functions.allowance(accounts[3], accounts[4]).call() == 0
    logs = get_logs_for_event(token_impl.events.Transfer, tx)
    assert logs[0]['args']['from'] == accounts[3]
    assert logs[0]['args']['to'] == accounts[4]
    assert logs[0]['args']['value'] == 90
    logs = get_logs_for_event(token_impl.events.Approval, tx)
    assert logs[0]['args']['owner'] == accounts[3]
    assert logs[0]['args']['spender'] == accounts[4]
    assert logs[0]['args']['value'] == 0

### Is this a bug or desired behaviou?!
def test_token_impl_transferFrom_different_to(
        token_impl_initialize_and_deploy,
        accounts,
        set_minter_with_limit,
        get_logs_for_event):

    # Deploy a TokenImpl
    (token_impl, token_impl_r) = token_impl_initialize_and_deploy("Infinigold", "IFG", 2)

    # Mint tokens to accounts[3 to 5]
    set_minter_with_limit(token_impl, 1000)
    token_impl.functions.mint(accounts[3], 250, 1).transact({'from': accounts[2]})
    token_impl.functions.mint(accounts[4], 250, 2).transact({'from': accounts[2]})
    token_impl.functions.mint(accounts[5], 250, 3).transact({'from': accounts[2]})

    # Approval from accounts[3] to accounts[4] of value 100
    token_impl.functions.approve(accounts[4], 100).transact({'from': accounts[3]})
    # TransferFrom accounts[3] to accounts[4] value 10
    tx = token_impl.functions.transferFrom(accounts[3], accounts[5], 10).transact({'from': accounts[4]})
    assert token_impl.functions.balanceOf(accounts[3]).call() == 240
    assert token_impl.functions.balanceOf(accounts[4]).call() == 250
    assert token_impl.functions.balanceOf(accounts[5]).call() == 260
    assert token_impl.functions.allowance(accounts[3], accounts[4]).call() == 90

def test_token_impl_transferFrom_invalid(
        token_impl_initialize_and_deploy,
        accounts,
        assert_tx_failed,
        set_minter_with_limit,
        zero_address,
        get_logs_for_event):

    # Deploy a TokenImpl
    (token_impl, token_impl_r) = token_impl_initialize_and_deploy("Infinigold", "IFG", 2)

    # Mint tokens to accounts[3 to 4]
    set_minter_with_limit(token_impl, 1000)
    token_impl.functions.mint(accounts[3], 250, 1).transact({'from': accounts[2]})
    token_impl.functions.mint(accounts[4], 250, 2).transact({'from': accounts[2]})

    # Approval from accounts[3] to accounts[4] of value 100
    token_impl.functions.approve(accounts[4], 100).transact({'from': accounts[3]})

    # Transfer more than allowance (and less than balance)
    assert_tx_failed(token_impl.functions.transferFrom(accounts[3], accounts[4], 200),
        {'from': accounts[4]})

    # Transfer to/from the zero_address
    assert_tx_failed(token_impl.functions.transferFrom(accounts[3], zero_address, 10),
        {'from': accounts[4]})
    assert_tx_failed(token_impl.functions.transferFrom(zero_address, accounts[4], 10),
        {'from': accounts[4]})

    # Transfer more than balance (and less than allowance)
    token_impl.functions.approve(accounts[4], 300).transact({'from': accounts[3]})
    assert_tx_failed(token_impl.functions.transferFrom(accounts[3], accounts[4], 275),
        {'from': accounts[4]})

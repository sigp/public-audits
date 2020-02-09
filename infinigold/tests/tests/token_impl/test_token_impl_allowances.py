def test_token_impl_allowances(
        token_impl_initialize_and_deploy,
        accounts,
        set_minter_with_limit,
        get_logs_for_event):

    # Deploy a TokenImpl
    (token_impl, token_impl_r) = token_impl_initialize_and_deploy("Infinigold", "IFG", 2)

    # Mint tokens to accounts[3 and 4]
    set_minter_with_limit(token_impl, 10000)
    token_impl.functions.mint(accounts[3], 250, 1).transact({'from': accounts[2]})
    token_impl.functions.mint(accounts[4], 250, 2).transact({'from': accounts[2]})

    # Test approval from accounts[3] to accounts[4] of value 10
    tx = token_impl.functions.approve(accounts[4], 10).transact({'from': accounts[3]})
    assert token_impl.functions.allowance(accounts[3], accounts[4]).call() == 10
    logs = get_logs_for_event(token_impl.events.Approval, tx)
    assert logs[0]['args']['owner'] == accounts[3]
    assert logs[0]['args']['spender'] == accounts[4]
    assert logs[0]['args']['value'] == 10

    # Test re-approval from accounts[3] to accounts[4] to value 8
    tx = token_impl.functions.approve(accounts[4], 8).transact({'from': accounts[3]})
    assert token_impl.functions.allowance(accounts[3], accounts[4]).call() == 8
    logs = get_logs_for_event(token_impl.events.Approval, tx)
    assert logs[0]['args']['owner'] == accounts[3]
    assert logs[0]['args']['spender'] == accounts[4]
    assert logs[0]['args']['value'] == 8

    # Test increasing allowance (of accounts[3] to accounts[4] by 10 from 8 to 18
    tx = token_impl.functions.increaseAllowance(accounts[4], 10).transact({'from': accounts[3]})
    assert token_impl.functions.allowance(accounts[3], accounts[4]).call() == 18
    logs = get_logs_for_event(token_impl.events.Approval, tx)
    assert logs[0]['args']['owner'] == accounts[3]
    assert logs[0]['args']['spender'] == accounts[4]
    assert logs[0]['args']['value'] == 18

    # Test decreasing allowance (of accounts[3] to accounts[4] by 5 from 18 to 13
    tx = token_impl.functions.decreaseAllowance(accounts[4], 5).transact({'from': accounts[3]})
    assert token_impl.functions.allowance(accounts[3], accounts[4]).call() == 13
    logs = get_logs_for_event(token_impl.events.Approval, tx)
    assert logs[0]['args']['owner'] == accounts[3]
    assert logs[0]['args']['spender'] == accounts[4]
    assert logs[0]['args']['value'] == 13

    # Test using decrease balance to set allowance to 0
    token_impl.functions.decreaseAllowance(accounts[4], 13).transact({'from': accounts[3]})
    assert token_impl.functions.allowance(accounts[3], accounts[4]).call() == 0

    # Test using increase balance to set allowance to Max uint256
    max_uint256 = 2 ** 256 - 1
    token_impl.functions.increaseAllowance(accounts[4], max_uint256).transact({'from': accounts[3]})
    assert token_impl.functions.allowance(accounts[3], accounts[4]).call() == max_uint256
    token_impl.functions.approve(accounts[4], 0).transact({'from': accounts[3]})
    token_impl.functions.approve(accounts[4], max_uint256).transact({'from': accounts[3]})
    assert token_impl.functions.allowance(accounts[3], accounts[4]).call() == max_uint256


def test_token_impl_allowances_invalid(
        token_impl_initialize_and_deploy,
        accounts,
        assert_tx_failed,
        set_minter_with_limit,
        zero_address,
        get_logs_for_event):

    # Deploy a TokenImpl
    (token_impl, token_impl_r) = token_impl_initialize_and_deploy("Infinigold", "IFG", 2)

    # Mint tokens to accounts[3 to 5]
    set_minter_with_limit(token_impl, 10000)
    token_impl.functions.mint(accounts[3], 250, 1).transact({'from': accounts[2]})

    # Test allowance overflow and underflow
    max_uint256 = 2 ** 256 - 1
    token_impl.functions.approve(accounts[3], 500).transact({'from': accounts[4]})
    assert_tx_failed(token_impl.functions.increaseAllowance(accounts[3], max_uint256), {'from': accounts[4]})
    assert_tx_failed(token_impl.functions.decreaseAllowance(accounts[3], max_uint256), {'from': accounts[4]})

    # Test allowance to zero_address
    assert_tx_failed(token_impl.functions.decreaseAllowance(zero_address, max_uint256), {'from': accounts[4]})

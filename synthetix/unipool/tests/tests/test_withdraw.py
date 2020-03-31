import pytest

def test_withdraw(
        accounts,
        get_logs_for_event,
        snx_token_deploy,
        uni_token_deploy,
        unipool_deploy,
    ):

    # Deploy an SNX token
    (snx, _) = snx_token_deploy()

    # Deploy a UNI token
    (uni, _) = uni_token_deploy()

    # Deploy a Unipool contract
    (pool, pool_r) = unipool_deploy(uni.address, snx.address)

    # Mint tokens
    uni.functions.mint(accounts[1], 10000).transact({'from': accounts[0]})

    # Approve the pool to spend these tokens
    stake_amount = 1000
    uni.functions.approve(pool.address, stake_amount).transact({'from': accounts[1]})

    # Stake tokens
    pool.functions.stake(stake_amount).transact({'from':accounts[1]})

    # Assert the pool supply is updated correctly
    assert pool.functions.totalSupply().call() == stake_amount
    assert pool.functions.balanceOf(accounts[1]).call() == stake_amount

    # Withdraw tokens
    tx = pool.functions.withdraw(stake_amount).transact({'from':accounts[1]})

    # Verify Withdrawn logs
    logs = get_logs_for_event(pool.events.Withdrawn, tx)
    assert logs[0]['args']['user'] == accounts[1], "Withdrawn logs incorrect user"
    assert logs[0]['args']['amount'] == stake_amount, "Withdrawn logs incorrect amount"

    # Assert the pool user balance has decreased
    assert pool.functions.balanceOf(accounts[1]).call() == 0

    # Assert the pool supply is updated correctly
    assert pool.functions.totalSupply().call() == 0

    # Assert the user's balance is updated accordingly
    assert uni.functions.balanceOf(accounts[1]).call() == 10000


def test_over_withdraw(
        accounts,
        assert_tx_failed,
        snx_token_deploy,
        uni_token_deploy,
        unipool_deploy,
    ):

    # Deploy an SNX token
    (snx, _) = snx_token_deploy()

    # Deploy a UNI token
    (uni, _) = uni_token_deploy()

    # Deploy a Unipool contract
    (pool, pool_r) = unipool_deploy(uni.address, snx.address)

    # Mint tokens
    uni.functions.mint(accounts[1], 10000).transact({'from': accounts[0]})

    # Approve the pool to spend these tokens
    stake_amount = 1000
    uni.functions.approve(pool.address, stake_amount).transact({'from': accounts[1]})

    # Stake tokens
    pool.functions.stake(stake_amount).transact({'from':accounts[1]})

    # Assert the pool supply is updated correctly
    assert pool.functions.totalSupply().call() == stake_amount
    assert pool.functions.balanceOf(accounts[1]).call() == stake_amount

    # Withdraw tokens above the balance
    assert_tx_failed(pool.functions.withdraw(2 * stake_amount), {'from':accounts[1]})

    # Assert the pool supply is NOT updated
    assert pool.functions.totalSupply().call() == stake_amount

    # Assert the user's balance is NOT updated
    assert uni.functions.balanceOf(accounts[1]).call() == 10000 - stake_amount


def test_withdraw_no_balance(
        accounts,
        assert_tx_failed,
        get_logs_for_event,
        snx_token_deploy,
        uni_token_deploy,
        unipool_deploy,
    ):

    # Deploy an SNX token
    (snx, _) = snx_token_deploy()

    # Deploy a UNI token
    (uni, _) = uni_token_deploy()

    # Deploy a Unipool contract
    (pool, pool_r) = unipool_deploy(uni.address, snx.address)

    # Mint tokens
    uni.functions.mint(accounts[1], 10000).transact({'from': accounts[0]})

    # Withdraw tokens above the balance
    # Update: this transaction should now revert
    assert_tx_failed(pool.functions.withdraw(0), {'from':accounts[1]})

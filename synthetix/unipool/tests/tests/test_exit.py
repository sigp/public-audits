def test_exit(
        accounts,
        get_logs_for_event,
        snx_token_deploy,
        uni_token_deploy,
        unipool_deploy,
    ):
    """
    Simple exit with not rewards
    """

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

    # Exit
    tx = pool.functions.exit().transact({'from':accounts[1]})

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


def test_exit_rewards(
        accounts,
        ganache_increase_time,
        get_logs_for_event,
        snx_token_deploy,
        uni_token_deploy,
        unipool_deploy,
    ):
    """

    """

    # Deploy an SNX token
    (snx, _) = snx_token_deploy()

    # Deploy a UNI token
    (uni, _) = uni_token_deploy()

    # Deploy a Unipool contract
    (pool, pool_r) = unipool_deploy(uni.address, snx.address)

    # Mint uni tokens
    uni.functions.mint(accounts[1], 10000000).transact({'from': accounts[0]})
    uni.functions.mint(accounts[2], 10000000).transact({'from': accounts[0]})

    # Mint snx tokens
    snx.functions.mint(pool.address, 10000000).transact({'from': accounts[0]})

    # Verify pool balance of SNX
    assert snx.functions.balanceOf(pool.address).call() == 10000000

    # Set accounts[2] as rewardDistribution
    pool.functions.setRewardDistribution(accounts[2]).transact({'from': accounts[0]})

    # Give pool rewards
    uni.functions.transfer(pool.address, 1000000).transact({'from': accounts[2]})

    # Approve the pool to spend these tokens
    stake_amount = 100000
    uni.functions.approve(pool.address, stake_amount).transact({'from': accounts[1]})

    # Call notifyRewardAmount to prevent earnings bug
    duration = 10
    reward = 1000000
    pool.functions.notifyRewardAmount(reward).transact({'from': accounts[2]})

    # Stake tokens
    pool.functions.stake(stake_amount).transact({'from':accounts[1]})

    # Pass a minimum of duration
    ganache_increase_time(duration)

    earned = pool.functions.earned(accounts[1]).call()
    # Exit
    tx = pool.functions.exit().transact({'from':accounts[1]})

    # Verify Withdrawn logs
    logs = get_logs_for_event(pool.events.Withdrawn, tx)
    assert logs[0]['args']['user'] == accounts[1], "Withdrawn logs incorrect user"
    assert logs[0]['args']['amount'] == stake_amount, "Withdrawn logs incorrect amount"

    # Verify RewardPaid logs
    logs = get_logs_for_event(pool.events.RewardPaid, tx)
    assert logs[0]['args']['user'] == accounts[1], "RewardPaid logs incorrect user"
    assert logs[0]['args']['reward'] == earned, "RewardPaid logs incorrect amount"

    # Assert the pool user balance has decreased
    assert pool.functions.balanceOf(accounts[1]).call() == 0

    # Assert the pool supply is updated correctly
    assert pool.functions.totalSupply().call() == 0

    # Assert the user's balance is updated accordingly
    assert uni.functions.balanceOf(accounts[1]).call() == 10000000
    assert snx.functions.balanceOf(accounts[1]).call() == earned

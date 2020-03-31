import pytest


def test_get_rewards(
        accounts,
        ganache_increase_time,
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

    # Call notifyRewardAmount to allow for rewards
    pool.functions.notifyRewardAmount(1000000).transact({'from': accounts[2]})

    # Stake tokens
    pool.functions.stake(stake_amount).transact({'from':accounts[1]})

    # Pass a minimum of 1 second
    ganache_increase_time(10)

    # Store reward earned
    earned = pool.functions.earned(accounts[1]).call()

    # Retrieve the reward
    tx = pool.functions.getReward().transact({'from': accounts[1]})


    # Verify RewardPaid logs
    logs = get_logs_for_event(pool.events.RewardPaid, tx)
    assert logs[0]['args']['user'] == accounts[1], "RewardPaid logs incorrect user"
    assert logs[0]['args']['reward'] >= earned, "RewardPaid logs incorrect amount"

    assert pool.functions.rewards(accounts[1]).call() == 0, "Rewards not decreased after transfer"


def test_get_rewards_larger_duration(
        accounts,
        ganache_increase_time,
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

    # Mint uni tokens
    uni.functions.mint(accounts[1], 10000).transact({'from': accounts[0]})
    uni.functions.mint(accounts[2], 10000).transact({'from': accounts[0]})

    # Mint snx tokens
    snx.functions.mint(pool.address, 10000).transact({'from': accounts[0]})

    # Verify pool balance of SNX
    assert snx.functions.balanceOf(pool.address).call() == 10000

    # Set accounts[2] as rewardDistribution
    pool.functions.setRewardDistribution(accounts[2]).transact({'from': accounts[0]})

    # Give pool rewards
    uni.functions.transfer(pool.address, 10000).transact({'from': accounts[2]})

    # Approve the pool to spend these tokens
    stake_amount = 1000
    uni.functions.approve(pool.address, stake_amount).transact({'from': accounts[1]})

    # Call notifyRewardAmount to allow for rewards
    pool.functions.notifyRewardAmount(1000000).transact({'from': accounts[2]})

    # Stake tokens
    pool.functions.stake(stake_amount).transact({'from':accounts[1]})

    # Pass a minimum of 1 second
    ganache_increase_time(10)

    # Store reward earned
    earned = pool.functions.earned(accounts[1]).call()

    assert earned > 0, "Rewards should have been earned"


def test_get_rewards_stake_early(
        accounts,
        ganache_increase_time,
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

    # Mint uni tokens
    uni.functions.mint(accounts[1], 10000).transact({'from': accounts[0]})
    uni.functions.mint(accounts[2], 10000).transact({'from': accounts[0]})

    # Mint snx tokens
    snx.functions.mint(pool.address, 10000).transact({'from': accounts[0]})

    # Verify pool balance of SNX
    assert snx.functions.balanceOf(pool.address).call() == 10000

    # Set accounts[2] as rewardDistribution
    pool.functions.setRewardDistribution(accounts[2]).transact({'from': accounts[0]})

    # Give pool rewards
    uni.functions.transfer(pool.address, 10000).transact({'from': accounts[2]})

    # Approve the pool to spend these tokens
    stake_amount = 1000
    uni.functions.approve(pool.address, stake_amount).transact({'from': accounts[1]})

    # Stake tokens
    pool.functions.stake(stake_amount).transact({'from':accounts[1]})

    # Call notifyRewardAmount to allow for rewards
    pool.functions.notifyRewardAmount(1).transact({'from': accounts[2]})

    # Pass a minimum of 1 second
    ganache_increase_time(1)

    # Attempt to withdraw rewards more than contract balance
    pool.functions.getReward().transact({'from': accounts[1]})


def test_get_rewards_multiple(
        accounts,
        ganache_increase_time,
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

    # Call notifyRewardAmount to allow for rewards
    pool.functions.notifyRewardAmount(1000000).transact({'from': accounts[2]})

    # Stake tokens
    pool.functions.stake(stake_amount).transact({'from':accounts[1]})

    # Pass a minimum of 1 second
    ganache_increase_time(100)

    # Store reward earned
    earned = pool.functions.earned(accounts[1]).call()

    # Call notifyRewardAmount to allow for rewards
    pool.functions.notifyRewardAmount(1000000).transact({'from': accounts[2]})

    # Pass a minimum of 1 second
    ganache_increase_time(100)

    # Check the rewards received has increased
    earned2 = pool.functions.earned(accounts[1]).call()
    assert earned2 > earned, "Rewards earned not increased"

    # Retrieve the reward
    tx = pool.functions.getReward().transact({'from': accounts[1]})

    # Verify RewardPaid logs
    logs = get_logs_for_event(pool.events.RewardPaid, tx)
    assert logs[0]['args']['user'] == accounts[1], "RewardPaid logs incorrect user"
    assert logs[0]['args']['reward'] >= earned2, "RewardPaid logs incorrect amount"

    assert pool.functions.rewards(accounts[1]).call() == 0, "Rewards not decreased after transfer"

    # Call notifyRewardAmount to allow for rewards
    pool.functions.notifyRewardAmount(1).transact({'from': accounts[2]})

    # Pass a minimum of 1 second
    ganache_increase_time(2)

    # Check the rewards received has increased
    earned3 = pool.functions.earned(accounts[1]).call()
    assert earned3 > 0, "Rewards earned incorrect"

    # Retrieve the reward
    tx = pool.functions.getReward().transact({'from': accounts[1]})

    # Verify RewardPaid logs
    logs = get_logs_for_event(pool.events.RewardPaid, tx)
    assert logs[0]['args']['user'] == accounts[1], "RewardPaid logs incorrect user"
    assert logs[0]['args']['reward'] >= earned3, "RewardPaid logs incorrect amount"

    assert pool.functions.rewards(accounts[1]).call() == 0, "Rewards not decreased after transfer"


def test_get_rewards_slippage(
        accounts,
        ganache_increase_time,
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

    # Call notifyRewardAmount to allow for rewards
    pool.functions.notifyRewardAmount(1000000).transact({'from': accounts[2]})

    # Stake tokens
    pool.functions.stake(stake_amount).transact({'from':accounts[1]})

    # Pass time of a greater length than duration
    ganache_increase_time(100)

    # Call notifyRewardAmount to allow for rewards
    pool.functions.notifyRewardAmount(1000000).transact({'from': accounts[2]})

    # Pass time equal to duration
    ganache_increase_time(100)

    # Retrieve the reward
    tx = pool.functions.getReward().transact({'from': accounts[1]})

    # Verify RewardPaid logs
    logs = get_logs_for_event(pool.events.RewardPaid, tx)
    assert logs[0]['args']['user'] == accounts[1], "RewardPaid logs incorrect user"
    # assert logs[0]['args']['reward'] <= 2, "RewardPaid logs incorrect amount"

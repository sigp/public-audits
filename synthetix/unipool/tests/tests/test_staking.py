def test_stake(snx_token_deploy, uni_token_deploy, unipool_deploy, accounts, get_logs):

    block_gas_limit = 7e6  # Or there about

    # Deploy an SNX token
    (snx, _) = snx_token_deploy()

    # Deploy a UNI token
    (uni, _) = uni_token_deploy()

    # Deploy a Unipool contract
    (pool, pool_r) = unipool_deploy(uni.address, snx.address)

    # Mint tokens
    uni.functions.mint(accounts[1], 10000).transact({'from': accounts[0]})

    # Approve the pool to spend these tokens
    uni.functions.approve(pool.address, 1000).transact({'from': accounts[1]})
    uni.functions.approve(pool.address, 1000).transact({'from': accounts[2]})
    uni.functions.approve(pool.address, 1000).transact({'from': accounts[3]})

    # Stake 10 tokens
    pool.functions.stake(10).transact({'from':accounts[1]})

    # Assert the pool supply is updated correctly
    assert pool.functions.totalSupply().call() == 10
    assert pool.functions.balanceOf(accounts[1]).call() == 10

    # Assert the user's UNI balance is updated accordingly
    assert uni.functions.balanceOf(accounts[1]).call() == 9990

    # Assert the balance is updated accordingly
    assert pool.functions.balanceOf(accounts[1]).call() == 10

    # Assert user can exit
    pool.functions.exit().transact({'from':accounts[1]})
    assert pool.functions.balanceOf(accounts[1]).call() == 0

    # Assert the pool supply is updated correctly
    assert pool.functions.totalSupply().call() == 0

    # Assert the user's balance is updated accordingly
    assert uni.functions.balanceOf(accounts[1]).call() == 10000

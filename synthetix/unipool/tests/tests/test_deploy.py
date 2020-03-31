def test_deploy(snx_token_deploy, uni_token_deploy, unipool_deploy, accounts, get_logs):

    block_gas_limit = 7e6  # Or there about

    # Deploy an SNX token
    (snx, _) = snx_token_deploy()

    # Deploy a UNI token
    (uni, _) = uni_token_deploy()

    # Deploy a Unipool contract
    (pool, pool_r) = unipool_deploy(uni.address, snx.address)

    print("")  # new line
    print("Gas used to deploy a Unipool contract: {}".format(pool_r['gasUsed']))

    assert pool_r['status'] == 1, "Unipool contract not deployed correctly"

    # Below block gas limits
    assert pool_r['gasUsed'] < block_gas_limit

    assert snx.address != 0, "Address returned not expected"
    assert uni.address != 0, "Address returned not expected"
    assert pool.address != 0, "Address returned not expected"

    assert uni.functions.totalSupply().call() == 0
    assert pool.functions.totalSupply().call() == 0

    assert pool.functions.snx().call() == snx.address, "Wrong SNX contract"
    assert pool.functions.uni().call() == uni.address, "Wrong UNI contract"

    # reward = pool.functions.rewardPerToken().call()
    # assert pool.functions.uni().call() == uni.address;
    # assert pool.functions.rewardRate().call() == snx.address;

    assert uni.functions.balanceOf(accounts[0]).call() == 0, "Incorrect balance"
    assert snx.functions.balanceOf(accounts[0]).call() == 0, "Incorrect balance"

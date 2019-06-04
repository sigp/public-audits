def test_deploy(oracle_deploy, basic_consumer_deploy, accounts, get_logs):

    block_gas_limit = 7e6  # Or there about

    # Deploy an oracle and a Link Token
    (link, oracle, link_r, oracle_r) = oracle_deploy()

    # Deploy a basic consumer
    specId = "00" + "A9E"*10  # random 32 byte specId
    (consumer, consumer_r) = basic_consumer_deploy(
                                                   link.address,
                                                   oracle.address,
                                                   specId)

    print("")  # new line
    print("Gas used to deploy Link token: {}".format(link_r['gasUsed']))
    print("Gas used to deploy Oracle: {}".format(oracle_r['gasUsed']))
    print("Gas used to deploy a basic Consumer: {}".
          format(consumer_r['gasUsed']))

    # Below block gas limits
    assert link_r['gasUsed'] < block_gas_limit
    assert oracle_r['gasUsed'] < block_gas_limit
    assert consumer_r['gasUsed'] < block_gas_limit

    assert link.address != 0, "Address returned not expected"
    assert link.functions.balanceOf(
            accounts[0]).call() == (10**27), \
            "Balance incorrectly set in constructor"
    assert oracle.address != 0, "Address returned not expected"
    assert consumer.address != 0, "Address returned not expected"

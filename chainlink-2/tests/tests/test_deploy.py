def test_deploy(basic_conversion_rate_deploy, oracle_deploy, accounts, get_logs):

    # Currently block gas limit 8 million
    block_gas_limit = 8e6

    # Deploy an oracle and a Link Token
    (link, oracle, link_r, oracle_r) = oracle_deploy()
    minimum_responses = 1
    payment_amount = 100
    (conversion_rate, conversion_rate_r) = basic_conversion_rate_deploy(
        link.address,
        payment_amount,
        minimum_responses,
        [oracle.address],
        ["0x01"])

    print("")  # new line
    print("Gas used to deploy Link token: {}".format(link_r['gasUsed']))
    print("Gas used to deploy Oracle: {}".format(oracle_r['gasUsed']))

    # Below block gas limits
    assert link_r['gasUsed'] < block_gas_limit
    assert oracle_r['gasUsed'] < block_gas_limit
    assert conversion_rate_r['gasUsed'] < block_gas_limit

    # Ensure contracts exist
    assert link.address != 0, "Address returned not expected"
    assert oracle.address != 0, "Address returned not expected"
    assert conversion_rate.address != 0, "Address returned not expected"

    # Ensure balance of LinkTokens sent to accounts[0]
    assert link.functions.balanceOf(
        accounts[0]).call() == (10**27), \
        "Balance incorrectly set in constructor"

    # Check ConversionRate initial values
    assert conversion_rate.functions.owner().call() == accounts[0], "Owner should be accounts[0]"
    assert conversion_rate.functions.minimumResponses().call() == minimum_responses, "Minimum responses set incorrectly"
    assert conversion_rate.functions.paymentAmount().call() == payment_amount, "Payment amount set incorrectly"
    assert conversion_rate.functions.jobIds(0).call() == b'\x01' + b'\x00' * 31, "Job Id incorrectly set"
    assert conversion_rate.functions.oracles(0).call() == oracle.address, "Oracle address incorrectly set"

def test_full_conversion_rate_deploy(
        accounts,
        full_conversion_rate_deploy,
        ):

    # Currently block gas limit 8 million
    block_gas_limit = 8e6

    # Set constructor paramters
    minimum_responses = 1
    payment_amount = 100
    num_oracles = 2

    # Deploy Conversion rate and associated functions
    (conversion_rate, conversion_rate_r, oracles, oracles_r, link, link_r) = full_conversion_rate_deploy(payment_amount, minimum_responses, num_oracles)

    # Below block gas limits
    assert conversion_rate_r['gasUsed'] < block_gas_limit

    # Check ConversionRate contract exists
    assert conversion_rate.address != 0, "Address returned not expected"

    # Check ConversionRate initial values
    assert conversion_rate.functions.owner().call() == accounts[0], "Owner should be accounts[0]"
    assert conversion_rate.functions.minimumResponses().call() == minimum_responses, "Minimum responses set incorrectly"
    assert conversion_rate.functions.paymentAmount().call() == payment_amount, "Payment amount set incorrectly"
    assert conversion_rate.functions.jobIds(0).call() == b'\x01' + b'\x00' * 31, "Job Id incorrectly set"
    assert conversion_rate.functions.oracles(0).call() == oracles[0].address, "Oracle address incorrectly set"

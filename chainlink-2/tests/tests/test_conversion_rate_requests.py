####################################################
# Simple function tests
####################################################
import pytest

def test_request_update(full_conversion_rate_deploy, accounts, get_logs_for_event, w3):
    payment_amount = 100
    minimum_responses = 1
    num_oracles = 1

    # Deploy a ConversionRate contract
    (conversion_rate, conversion_rate_r, oracles, oracles_r, link, link_r) = full_conversion_rate_deploy(
        payment_amount,
        minimum_responses,
        num_oracles,
    )

    # Send LNK to the conversion contract
    link.functions.transfer(conversion_rate.address,
            payment_amount*10).transact({'from': accounts[0]})

    # Call request update, which requests an update from oracle
    tx = conversion_rate.functions.requestRateUpdate().transact({'from': accounts[0]})


    # Verify logs
    logs = get_logs_for_event(conversion_rate.events.ChainlinkRequested, tx)
    request_ids = [0] * num_oracles
    for i in range(num_oracles):
        request_ids[i] = logs[i]['args']['id']
        assert request_ids[i] != 0

    logs = get_logs_for_event(oracles[0].events.OracleRequest, tx)
    for i in range(num_oracles):
        assert logs[i]['args']['requestId'] == request_ids[i], "Request Id does not match"
        assert logs[i]['args']['payment'] == payment_amount, "Payment amount does not match"
        assert logs[i]['args']['callbackAddr'] == conversion_rate.address, "Callback address does not match"
        assert logs[i]['args']['callbackFunctionId'].hex() == w3.sha3(text='chainlinkCallback(bytes32,uint256)').hex()[2:10], "callbackFunctionId does not match"

def test_update_request_details(full_conversion_rate_deploy, accounts, get_logs_for_event):
    payment_amount = 1
    num_oracles = 2
    minimum_responses = num_oracles

    # Deploy a ConversionRate contract
    (conversion_rate, conversion_rate_r, oracles, oracles_r, link, link_r) = full_conversion_rate_deploy(
        payment_amount,
        minimum_responses,
        num_oracles,
    )

    # Pre checks
    assert conversion_rate.functions.minimumResponses().call() == minimum_responses, "minimumResponsese incorrectly set"
    assert conversion_rate.functions.paymentAmount().call() == payment_amount, "paymentAmount incorrectly set"
    assert conversion_rate.functions.oracles(0).call() == oracles[0].address, "Oracle address incorrectly set"
    assert conversion_rate.functions.oracles(1).call() == oracles[1].address, "Oracle address incorrectly set"
    assert conversion_rate.functions.jobIds(0).call() == b'\x01' + b'\x00' * 31, "Job Id incorrectly set"
    assert conversion_rate.functions.jobIds(1).call() == b'\x01' + b'\x00' * 31, "Job Id incorrectly set"

    # Update the request details
    payment_amount = 2
    num_oracles = 5
    minimum_responses = num_oracles
    tx = conversion_rate.functions.updateRequestDetails(
            payment_amount,
            minimum_responses,
            [oracles[1].address] * num_oracles,
            [b'\x02'] * num_oracles,
        ).transact({'from': accounts[0], 'gas': 7999999})

    # Ensure details are updated
    assert conversion_rate.functions.minimumResponses().call() == minimum_responses, "minimumResponsese incorrectly set"
    assert conversion_rate.functions.paymentAmount().call() == payment_amount, "paymentAmount incorrectly set"
    for i in range(num_oracles):
        assert conversion_rate.functions.oracles(i).call() == oracles[1].address, "Oracle address incorrectly set"
        assert conversion_rate.functions.jobIds(0).call() == b'\x02' + b'\x00' * 31, "Job Id incorrectly set"

####################################################
# ORACLE Limits based off block gas limit 8,000,000
####################################################

@pytest.mark.xfail()
def test_constructor_oracle_limit(full_conversion_rate_deploy, accounts):
    # Set function parameters
    payment_amount = 1
    num_oracles = 142 # fails at 143
    minimum_responses = num_oracles

    # Deploy a ConversionRate contract
    (conversion_rate, conversion_rate_r, oracles, oracles_r, link, link_r) = full_conversion_rate_deploy(
        payment_amount,
        minimum_responses,
        num_oracles,
    )

def test_update_request_details_oracle_limit(full_conversion_rate_deploy, assert_tx_failed, accounts):

    payment_amount = 1
    num_oracles = 1 # note increasing this will increase the num oracles that can be updated below

    minimum_responses = num_oracles
    # Deploy a ConversionRate contract
    (conversion_rate, conversion_rate_r, oracles, oracles_r, link, link_r) = full_conversion_rate_deploy(
        payment_amount,
        minimum_responses,
        num_oracles,
    )

    # Update the number of oracles to
    num_oracles = 190
    minimum_responses = num_oracles

    # Send LNK to the conversion contract
    link.functions.transfer(
            conversion_rate.address,
            payment_amount * num_oracles
        ).transact({'from': accounts[0]})

    # Attempt to update details with too many oracles
    assert_tx_failed(conversion_rate.functions.updateRequestDetails(
            payment_amount,
            minimum_responses,
            [oracles[0].address] * num_oracles,
            [b'x02'] * num_oracles,
        ), {'from': accounts[0], 'gas': 7999999})

@pytest.mark.xfail()
def test_request_rate_update_oracle_limit(full_conversion_rate_deploy, assert_tx_failed, accounts):

    payment_amount = 1
    num_oracles = 76
    minimum_responses = num_oracles

    # Deploy a ConversionRate contract
    (conversion_rate, conversion_rate_r, oracles, oracles_r, link, link_r) = full_conversion_rate_deploy(
        payment_amount,
        minimum_responses,
        num_oracles,
    )

    # Send LNK to the conversion contract
    link.functions.transfer(
            conversion_rate.address,
            payment_amount * num_oracles
        ).transact({'from': accounts[0]})

    # Call request rate update, which requests an update from oracle
    assert_tx_failed(conversion_rate.functions.requestRateUpdate(), {'from': accounts[0]})

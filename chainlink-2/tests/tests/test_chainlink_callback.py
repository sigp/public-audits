import pytest
import math
import random

def test_chainlink_callback_random(oracle_deploy, basic_conversion_rate_deploy,
        multi_oracle_deploy, accounts, get_logs_for_event, get_receipt,
        ):
    """
     This test evaluates the gas used in the Oracle callback function given a
     number of Oracles randomly ordered.
     Even a cheap oracle sending the bare minimum gas will process all answers
     if the number of oracles is low enough.
    """
    # Set number of oracles
    no_oracles = 30 # fails at 45 +-5

    # Minimum required by oracle such that 400K minimum is sent to callback
    gas_limit = int(4.39e5)

    # Deploy LinkToken, required Oracles and conversion rate
    (link, link_r, oracles, oracles_r) = multi_oracle_deploy(no_oracles)
    minimum_responses = no_oracles
    payment_amount = 10

    (conversion_rate, conversion_rate_r) = basic_conversion_rate_deploy(
        link.address,
        payment_amount,
        minimum_responses,
        [oracle.address for oracle in oracles],
        ["0x01" for data in range(no_oracles)])


    # Send LINK to the conversion contract
    link.functions.transfer(conversion_rate.address,
            payment_amount*no_oracles).transact({'from': accounts[0]})

    # Send requests to all the oracles
    tx = conversion_rate.functions.requestRateUpdate().transact({'from': accounts[0] } )

    # Iterate through the oracles such that make conversion_rate.chainlinkCallback()
    logs = get_logs_for_event(oracles[0].events.OracleRequest, tx)
    for index in range(no_oracles):
        data = logs[index]['args']
        # fulfillOracleRequest calls chainlinkCallback
        tx = oracles[index].functions.fulfillOracleRequest(
                data['requestId'],
                data['payment'],
                data['callbackAddr'],
                data['callbackFunctionId'],
                data['cancelExpiration'],
                (math.floor(100000*random.random())).to_bytes(32, byteorder='big'),
                ).transact({'from': accounts[0], 'gas': gas_limit})
        latest = conversion_rate.functions.currentAnswer().call()

    # If latest has not changed, not enough gas was sent to chainlinkCallback
    assert latest != 0, "Latest should be updated of last callback failed"


@pytest.mark.xfail()
def test_chainlink_callback_restricted_gas(oracle_deploy, basic_conversion_rate_deploy,
        multi_oracle_deploy, accounts, get_logs_for_event, get_receipt,
        ):
    """
     This test evaluates the gas used in the Oracle callback function given a
     number of Oracles in the sorted list.
     The test fails as a cheap Oracle will send 400K exactly as a gas limit to
     chainlinkCallback() function which will not be enough gas to delete all of
     answers before the gas refund is recieved
    """
    # Set number of oracles and gas to be sent
    no_oracles = 50 # passes at 49
    gas_limit = int(4.39e5) # Minimum required by oracle such that 400K minimum is achieved

    # Deploy LinkToken, required Oracles and conversion rate
    (link, link_r, oracles, oracles_r) = multi_oracle_deploy(no_oracles)
    minimum_responses = no_oracles
    payment_amount = 10

    (conversion_rate, conversion_rate_r) = basic_conversion_rate_deploy(
        link.address,
        payment_amount,
        minimum_responses,
        [oracle.address for oracle in oracles],
        ["0x01" for data in range(no_oracles)])

    # Send LINK to the conversion contract
    link.functions.transfer(conversion_rate.address,
            payment_amount*no_oracles).transact({'from': accounts[0]})

    # Send requests to all the oracles
    tx = conversion_rate.functions.requestRateUpdate().transact({'from': accounts[0] } )

    # Iterate through the oracles such that make conversion_rate.chainlinkCallback()
    logs = get_logs_for_event(oracles[0].events.OracleRequest, tx)
    previous_latest = 0
    for index in range(no_oracles):
        data = logs[index]['args']
        # fulfillOracleRequest calls chainlinkCallback
        tx = oracles[index].functions.fulfillOracleRequest(
                data['requestId'],
                data['payment'],
                data['callbackAddr'],
                data['callbackFunctionId'],
                data['cancelExpiration'],
                ((no_oracles - index)*2).to_bytes(32, byteorder='big'), # ordered
                ).transact({'from': accounts[0], 'gas': gas_limit})
        latest = conversion_rate.functions.currentAnswer().call()

    # If latest has not changed, not enough gas was sent to chainlinkCallback
    assert latest != 0, "Latest hash not changed"

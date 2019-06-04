from statistics import median
import pytest
import math
import random


@pytest.mark.parametrize(
    "responses",
    [
    ([1, 2, 3, 4, 5, 200]),
    ([400, 1000, 8, 42, int(1e18), int(1e12)]),
    ([23, 0, 0, 40, int(1e23), 40]),
    ([0, 0, 0, 0 ]),
    ([0, 0, 0, 0, 0 ]),
    ([1, 1, 1, 1, 1 ]),
    ([1, 1, 1, 1, 1 ]),
    ([500, 500, 500, 500, int(1e8), int(1e8), int(1e8)]),
    ]
)
def test_median_result(oracle_deploy, basic_conversion_rate_deploy,
        multi_oracle_deploy, accounts, get_logs_for_event,
        responses):
    """
     This test demonstrates the median calculation for a variety of Oracles
     and responses
    """

    # Deploy the number of oracles that match list length and a Link Token
    # contract
    (link, link_r, oracles, oracles_r) = multi_oracle_deploy(len(responses))
    minimum_responses = 1
    payment_amount = 100
    (conversion_rate, conversion_rate_r) = basic_conversion_rate_deploy(
        link.address,
        payment_amount,
        minimum_responses,
        [oracle.address for oracle in oracles],
        ["0x01" for data in responses])

    # Send LINK to the conversion contract
    link.functions.transfer(conversion_rate.address,
            payment_amount*len(responses)).transact({'from': accounts[0]})

    # Send requests to all the oracles
    tx = conversion_rate.functions.requestRateUpdate().transact({'from': accounts[0] } )

    # Use logs to fulfill the requests
    logs = get_logs_for_event(oracles[0].events.OracleRequest, tx)

    counter = 0
    for oracle in oracles:
        data = logs[counter]['args']
        oracle.functions.fulfillOracleRequest(
                data['requestId'],
                data['payment'],
                data['callbackAddr'],
                data['callbackFunctionId'],
                data['cancelExpiration'],
                (responses[counter]).to_bytes(32, byteorder='big'),
                ).transact({'from': accounts[0], 'gas': 500000})
        counter += 1

    latest = conversion_rate.functions.currentAnswer().call()
    # Have to round down to match solidity.
    assert latest == math.floor(median(responses))


def test_async_oracle_callback(oracle_deploy, basic_conversion_rate_deploy,
        multi_oracle_deploy, accounts, get_logs_for_event):
    """
    This test demonstrates only a minimum number of random-ordered oracles
    returning data to the contract.
    """

    # Deploy the number of oracles that match list length and a Link Token
    # contract
    responses = [100,200,300,400,500,600,700,800]
    (link, link_r, oracles, oracles_r) = multi_oracle_deploy(len(responses))
    minimum_responses = 5
    payment_amount = 100
    (conversion_rate, conversion_rate_r) = basic_conversion_rate_deploy(
        link.address,
        payment_amount,
        minimum_responses,
        [oracle.address for oracle in oracles],
        ["0x01" for data in responses])

    # Send LINK to the conversion contract
    link.functions.transfer(conversion_rate.address,
            payment_amount*len(responses)).transact({'from': accounts[0]})

    # Send requests to all the oracles
    tx = conversion_rate.functions.requestRateUpdate().transact({'from': accounts[0] } )

    # Use logs to fulfill the requests
    logs = get_logs_for_event(oracles[0].events.OracleRequest, tx)

    index_list = list(range(len(responses)))
    results_provided = []
    random.shuffle(index_list)
    for index in range(minimum_responses):
        rand_index = index_list[index]
        results_provided.append(responses[rand_index])
        data = logs[rand_index]['args']
        oracles[rand_index].functions.fulfillOracleRequest(
                data['requestId'],
                data['payment'],
                data['callbackAddr'],
                data['callbackFunctionId'],
                data['cancelExpiration'],
                (responses[rand_index]).to_bytes(32, byteorder='big'),
                ).transact({'from': accounts[0], 'gas': 500000})

    latest = conversion_rate.functions.currentAnswer().call()
    # Have to round down to match solidity.
    assert latest == math.floor(median(results_provided))

def test_async_oracle_callback_more_than_min(oracle_deploy, basic_conversion_rate_deploy,
        multi_oracle_deploy, accounts, get_logs_for_event):
    """
    This test demonstrates more than a minimum number of random-ordered oracles
    return data to the contract.
    """

    # Deploy the number of oracles that match list length and a Link Token
    # contract
    responses = [100,200,300,400,500,600,700,800]
    (link, link_r, oracles, oracles_r) = multi_oracle_deploy(len(responses))
    minimum_responses = 4
    payment_amount = 100
    (conversion_rate, conversion_rate_r) = basic_conversion_rate_deploy(
        link.address,
        payment_amount,
        minimum_responses,
        [oracle.address for oracle in oracles],
        ["0x01" for data in responses])

    # Send LINK to the conversion contract
    link.functions.transfer(conversion_rate.address,
            payment_amount*len(responses)).transact({'from': accounts[0]})

    # Send requests to all the oracles
    tx = conversion_rate.functions.requestRateUpdate().transact({'from': accounts[0] } )

    # Use logs to fulfill the requests
    logs = get_logs_for_event(oracles[0].events.OracleRequest, tx)

    index_list = list(range(len(responses)))
    results_provided = []
    random.shuffle(index_list)
    for index in range(minimum_responses+2):
        rand_index = index_list[index]
        results_provided.append(responses[rand_index])
        data = logs[rand_index]['args']
        oracles[rand_index].functions.fulfillOracleRequest(
                data['requestId'],
                data['payment'],
                data['callbackAddr'],
                data['callbackFunctionId'],
                data['cancelExpiration'],
                (responses[rand_index]).to_bytes(32, byteorder='big'),
                ).transact({'from': accounts[0], 'gas': 500000})

    latest = conversion_rate.functions.currentAnswer().call()
    # Have to round down to match solidity.
    assert latest == math.floor(median(results_provided))

def test_async_oracle_callback_less_than_min(oracle_deploy, basic_conversion_rate_deploy,
        multi_oracle_deploy, accounts, get_logs_for_event):
    """
    This test demonstrates only less than a minimum number of random-ordered oracles
    return data to the contract.
    """

    # Deploy the number of oracles that match list length and a Link Token
    # contract
    responses = [100,200,300,400,500,600,700,800]
    (link, link_r, oracles, oracles_r) = multi_oracle_deploy(len(responses))
    minimum_responses = 5
    payment_amount = 100
    (conversion_rate, conversion_rate_r) = basic_conversion_rate_deploy(
        link.address,
        payment_amount,
        minimum_responses,
        [oracle.address for oracle in oracles],
        ["0x01" for data in responses])

    # Send LINK to the conversion contract
    link.functions.transfer(conversion_rate.address,
            payment_amount*len(responses)).transact({'from': accounts[0]})

    # Send requests to all the oracles
    tx = conversion_rate.functions.requestRateUpdate().transact({'from': accounts[0] } )

    # Use logs to fulfill the requests
    logs = get_logs_for_event(oracles[0].events.OracleRequest, tx)

    index_list = list(range(len(responses)))
    results_provided = []
    random.shuffle(index_list)
    for index in range(minimum_responses-1):
        rand_index = index_list[index]
        results_provided.append(responses[rand_index])
        data = logs[rand_index]['args']
        oracles[rand_index].functions.fulfillOracleRequest(
                data['requestId'],
                data['payment'],
                data['callbackAddr'],
                data['callbackFunctionId'],
                data['cancelExpiration'],
                (responses[rand_index]).to_bytes(32, byteorder='big'),
                ).transact({'from': accounts[0], 'gas': 500000})

    latest = conversion_rate.functions.currentAnswer().call()
    assert latest == 0


def test_async_oracle_multiple_requests(oracle_deploy, basic_conversion_rate_deploy,
        multi_oracle_deploy, accounts, get_logs_for_event):
    """
    This test demonstrates multiple requests with asynchronous, random-ordered responses from
    a varied list of Oracles.
    """

    # Create three sets of oracles and their responses. This test will have
    # asynchronous updates accross the three sets with various responses during
    # the updates from each set.
    responses1 = [100,200,300,400,500,600,700,800]
    responses2 = [7000,7500,7750,8000,8125,8250,8350,7324]
    responses3 = [90,120,125,10,80]
    total_oracles = len(responses1) + len(responses2) + len(responses3)

    (link, link_r, oracles, oracles_r) = multi_oracle_deploy(total_oracles)
    minimum_responses = 5
    payment_amount = 100
    (conversion_rate, conversion_rate_r) = basic_conversion_rate_deploy(
        link.address,
        payment_amount,
        minimum_responses,
        [oracle.address for oracle in oracles[0:len(responses1)]],
            ["0x01" for data in oracles[0:len(responses1)]])

    # Define oracle sets for clarity
    oracles1 = oracles[0:len(responses1)]
    oracles2 = oracles[len(responses1):len(responses1) + len(responses2)]
    oracles3 = oracles[len(responses2):len(responses2) + len(responses3)]

    # Send LINK to the conversion contract
    link.functions.transfer(conversion_rate.address,
            payment_amount*total_oracles).transact({'from': accounts[0]})

    # Send requests to all the oracles
    tx = conversion_rate.functions.requestRateUpdate().transact({'from': accounts[0] } )

    # Randomly get 3 responses from the first set of oracles
    logs1 = get_logs_for_event(oracles[0].events.OracleRequest, tx)
    index_list1 = list(range(len(oracles1)))
    random.shuffle(index_list1)
    results_sent1 = []
    for index in range(3):
        rand_index = index_list1[index]
        results_sent1.append(responses1[rand_index])
        data = logs1[rand_index]['args']
        oracles1[rand_index].functions.fulfillOracleRequest(
                data['requestId'],
                data['payment'],
                data['callbackAddr'],
                data['callbackFunctionId'],
                data['cancelExpiration'],
                (responses1[rand_index]).to_bytes(32, byteorder='big'),
                ).transact({'from': accounts[0], 'gas': 500000})

    latest = conversion_rate.functions.currentAnswer().call()
    assert latest == 0

    # Update the oracle set and minimum amount
    payment = 50
    minimum_responses = 6
    conversion_rate.functions.updateRequestDetails(payment,
            minimum_responses, [oracle.address for oracle in oracles2], ["0x01" for data in oracles2]).transact({'from': accounts[0] } )

    # Send requests to all the oracles
    tx = conversion_rate.functions.requestRateUpdate().transact({'from': accounts[0] } )

    # Send 4 random responses from oracle set 2
    logs2 = get_logs_for_event(oracles[0].events.OracleRequest, tx)
    index_list2 = list(range(len(oracles2)))
    random.shuffle(index_list2)
    for index in range(4):
        rand_index = index_list2[index]
        data = logs2[rand_index]['args']
        oracles2[rand_index].functions.fulfillOracleRequest(
                data['requestId'],
                data['payment'],
                data['callbackAddr'],
                data['callbackFunctionId'],
                data['cancelExpiration'],
                (responses2[rand_index]).to_bytes(32, byteorder='big'),
                ).transact({'from': accounts[0], 'gas': 500000})

    latest = conversion_rate.functions.currentAnswer().call()
    assert latest == 0

    # Send another 3 responses from oracle set 1 - This puts us over the
    # minimum of the original set. Forming the first result
    for index in range(3,6):
        rand_index = index_list1[index]
        results_sent1.append(responses1[rand_index])
        data = logs1[rand_index]['args']
        oracles1[rand_index].functions.fulfillOracleRequest(
                data['requestId'],
                data['payment'],
                data['callbackAddr'],
                data['callbackFunctionId'],
                data['cancelExpiration'],
                (responses1[rand_index]).to_bytes(32, byteorder='big'),
                ).transact({'from': accounts[0], 'gas': 500000})

    # Should have a first result
    latest = conversion_rate.functions.currentAnswer().call()
    assert latest == math.floor(median(results_sent1))

    # Update to the last set of Oracles
    payment = 50
    minimum_responses = 5
    conversion_rate.functions.updateRequestDetails(payment,
            minimum_responses, [oracle.address for oracle in oracles3], ["0x01" for data in oracles3]).transact({'from': accounts[0] } )

    # Send requests to all the oracles
    tx = conversion_rate.functions.requestRateUpdate().transact({'from': accounts[0] } )

    # All of Oracles 3 respond
    logs3 = get_logs_for_event(oracles[0].events.OracleRequest, tx)
    index_list3 = list(range(len(oracles3)))
    random.shuffle(index_list3)
    for index in range(len(oracles3)):
        rand_index = index_list3[index]
        data = logs3[rand_index]['args']
        oracles3[rand_index].functions.fulfillOracleRequest(
                data['requestId'],
                data['payment'],
                data['callbackAddr'],
                data['callbackFunctionId'],
                data['cancelExpiration'],
                (responses3[rand_index]).to_bytes(32, byteorder='big'),
                ).transact({'from': accounts[0], 'gas': 500000})

    # Should have the median from Oracle 3 set
    latest = conversion_rate.functions.currentAnswer().call()
    assert latest == math.floor(median(responses3))

    # All the remaining Oracles respond
    # Oracle set 1
    for index in range(6,len(responses1)):
        rand_index = index_list1[index]
        data = logs1[rand_index]['args']
        oracles1[rand_index].functions.fulfillOracleRequest(
                data['requestId'],
                data['payment'],
                data['callbackAddr'],
                data['callbackFunctionId'],
                data['cancelExpiration'],
                (responses1[rand_index]).to_bytes(32, byteorder='big'),
                ).transact({'from': accounts[0], 'gas': 500000})

    # Should still have the median from Oracle 3 set
    latest = conversion_rate.functions.currentAnswer().call()
    assert latest == math.floor(median(responses3))

    # Oracle set 2
    for index in range(4,len(responses2)):
        rand_index = index_list2[index]
        data = logs2[rand_index]['args']
        oracles2[rand_index].functions.fulfillOracleRequest(
                data['requestId'],
                data['payment'],
                data['callbackAddr'],
                data['callbackFunctionId'],
                data['cancelExpiration'],
                (responses2[rand_index]).to_bytes(32, byteorder='big'),
                ).transact({'from': accounts[0], 'gas': 500000})

    # Should still have the median from Oracle 3 set
    latest = conversion_rate.functions.currentAnswer().call()
    assert latest == math.floor(median(responses3))

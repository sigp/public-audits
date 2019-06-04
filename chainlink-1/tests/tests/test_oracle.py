## A series of tests that are oracle focused
import pytest


@pytest.mark.parametrize(
    "calldata_length, transaction_succeeds",
    [
        (1, False),
        (2, False),
        (12, False),
        (13, False),
        (8*32, False),   # Number of parameters
        (9*32, True),  # Include encoded _data
        (10*32, True),  # Partial _data
        (11*32, True),  # Include encoded _data
    ]
)
def test_on_token_transfer_data_length(
        oracle_deploy,
        calldata_length,
        transaction_succeeds,
        w3,
        accounts,
        get_logs_for_event,
        assert_tx_failed
        ):

    (link, oracle, _, _) = oracle_deploy()

    function_selector = w3.sha3(
            text="requestData(address,uint256,uint256,bytes32,address,bytes4,uint256,bytes)").hex()[2:10]

    # Send the function selector and an arbitrary length of bytes
    calldata = function_selector + "00"*int(calldata_length)


    if (int(calldata_length) >= 9*32): # Use real data to test

        spare_data_length = calldata_length - 9*32
        hex_spare_data_length = hex(spare_data_length)[2:4]
        function_selector = w3.sha3(
                text="requestData(address,uint256,uint256,bytes32,address,bytes4,uint256,bytes)").hex()[2:10]

        sender = "00" * 32              # Leave Empty - 32 bytes
        amount = "00" * 32              # Leave Empty - 32 bytes
        version = "0" * 63 + "1"        # Version of 1 - 32 bytes
        specId = "0" * 61 + "A9E"       # Random data - 32 bytes
        # Pad address to 32 bytes
        callbackAddress = "00" * 12 + accounts[0][2:]  # Must put the current address to cancel
        callbackFunctionId = "00"*32    # Leave empty - 32 bytes
        externalId = "00"*31 + "01"     # ExternalId of 1
        data_location = "0" * 61 + "100"      # Location of data, hex 100 - 32 bytes
        data_length = "0" * (64-len(hex_spare_data_length))  + hex_spare_data_length         # Length of data unimportant, let's say 1
        data = 'FF'*spare_data_length + (32-spare_data_length)*"00"              # Random 1 byte data, 255

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

    # Call the oracle's onTokenTransfer function
    tx = link.functions.transferAndCall(
            oracle.address,
            300,  # amount of LINK to send
            calldata)

    if transaction_succeeds:
        tx = tx.transact({'from': accounts[0]})

        # Get event that occurred
        event = get_logs_for_event(oracle.events.RunRequest, tx)[0]['args']
        print('')
        print("Sender: {}".format(event['requester']))
        print("Amount: {}".format(event['amount']))
        print("Version: {}".format(event['version']))
        print("SpecId: {}".format(event['specId'].hex()))
        print("InternalId: {}".format(event['requestId']))
        print("Data: {}".format(event['data']))

        # We expect to have lost Link tokens
        assert link.functions.balanceOf(oracle.address).call() == 300, "Expecting \
        to lose 300 Link tokens"

    else:  # We expect the transaction to fail
        assert_tx_failed(tx, {'from': accounts[0]})

def test_can_duplicate_id(
        w3,
        accounts,
        oracle_deploy,
        get_logs_for_event,
        ganache_increase_time,
        assert_tx_failed,
        ):

    (link, oracle, _, _) = oracle_deploy()

    initial_balance = link.functions.balanceOf(accounts[0]).call()

    function_selector = w3.sha3(
            text="requestData(address,uint256,uint256,bytes32,address,bytes4,uint256,bytes)").hex()[2:10]

    sender = "00" * 32              # Leave Empty - 32 bytes
    amount = "00" * 32              # Leave Empty - 32 bytes
    version = "0" * 63 + "1"        # Version of 1 - 32 bytes
    specId = "0" * 61 + "A9E"       # Random data - 32 bytes
    # Pad address to 32 bytes
    callbackAddress = "00" * 12 + accounts[0][2:]  # Must put the current address to cancel
    callbackFunctionId = "00"*32    # Leave empty - 32 bytes
    externalId = "00"*31 + "01"     # ExternalId of 1
    data_location = "0" * 61 + "100"      # Location of data, hex 100 - 32 bytes
    data_length = "0" * 62 + "20"         # Length of data unimportant, let's say 1
    data = 'FF' + ("0" * 62)              # Random 1 byte data, 255

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

    # Call the oracle's onTokenTransfer function - send 1000 tokens
    tx = link.functions.transferAndCall(
            oracle.address,
            1000,  # amount of LINK to send
            calldata).transact({'from': accounts[0]})

    # calculate the expected internalId
    expected_request_id = w3.soliditySha3(
                                            ["address", "bytes32"],
                                            [accounts[0], "0x" + externalId])
    # Get event that occurred
    event = get_logs_for_event(oracle.events.RunRequest,tx)[0]['args']

    # verify the tx worked as expected
    assert event['requester'] == accounts[0], "Incorrect sender sent to Oracle"
    # verify the internal_id is as expected
    assert hex(event['requestId']) == expected_request_id.hex(), "RequestId not as expected"

    # create a new request with the same id.
    tx = link.functions.transferAndCall(
            oracle.address,
            1000,  # amount of LINK to send
            calldata).transact({'from': accounts[0]})

    # Get event that occurred
    event = get_logs_for_event(oracle.events.RunRequest,)[0]['args']

    # verify the tx worked as expected
    assert event['requester'] == accounts[0], "Incorrect sender sent to Oracle"
    # verify the internal_id is as expected
    assert hex(event['requestId']) == expected_request_id.hex(), "RequestId not as expected"

    # should have spent 2000 tokens now
    current_balance = link.functions.balanceOf(accounts[0]).call()
    assert initial_balance - current_balance == 2000, "should have spent 2000 tokens"

    # Expire the request by moving forward in time
    ganache_increase_time(301)  # just over 5 mins


    # cancel the request with duplicate id
    oracle.functions.cancel(externalId).transact({'from': accounts[0]})

    # should have spent 1000 tokens now
    current_balance = link.functions.balanceOf(accounts[0]).call()
    assert initial_balance - current_balance == 1000, "should have regained 1000 tokens"

    # cannot get our original tokens back
    # cancel the request with duplicate id
    tx = oracle.functions.cancel(externalId)

    # Assert that this fails
    assert_tx_failed(tx, {'from': accounts[0]})

    # should have recovered all tokens now but we do not
    current_balance = link.functions.balanceOf(accounts[0]).call()
    assert initial_balance - current_balance != 0, "should not have regained all tokens"


@pytest.mark.parametrize(
    "gas_to_spend",
    [
        (450e3),
        (500e3),
        (1e6),
        (2e6),
        (5e6),
    ]
)
def test_cannot_DOS_requests(
        w3,
        accounts,
        oracle_deploy,
        DOS_deploy,
        gas_to_spend,
        chainlinked_test_deploy,
        function_selector,
        get_logs_for_event,
        get_receipt):
    """
    A malicious user creates a callback function which consumes all gas. This
    tests for various gas values, whether this can prevent Oracles from completing
    requests and claiming their fees.
    """

    # Deploy the link token and an oracle
    (link, oracle, _, _) = oracle_deploy()
    specId = "00" + "A9E"*10  # random 32 byte specId
    # We use the ChainlinkedTest contract which gives us the ability to make
    # requests that have custom variables, specifically we can specify our own
    # callback address
    (malicious_requester, _) = chainlinked_test_deploy(link.address, oracle.address)

    # Deploy a malicious callback address, i.e DOSContract (see test/contracts/)
    (dos, _) = DOS_deploy()

    # Give the malicious_requester some link tokens
    link.functions.transfer(malicious_requester.address, int(1e20)).transact({'from': accounts[0]})

    # make a request
    callback_address = dos.address  # dos contract the callback
    function_signature = function_selector("fulfill(bytes32,bytes32)")  # function sig of consumer callback
    data = "Arbitrary request data"  # poor example of malicious request
    tokens_spent = int(1e18)  # 1 link token

    # make the call
    tx = malicious_requester.functions.publicRequestRun(
                                                    specId,
                                                    callback_address,
                                                    function_signature,
                                                    data,
                                                    tokens_spent).transact({'from':accounts[2]})
    internal_id2 = get_logs_for_event(malicious_requester.events.ChainlinkRequested,
    tx)[0]['args']['id']
    #  The oracle tries to fulfill the request
    fulfill_data = "00"*32  # 0 value, why not
    tx = oracle.functions.fulfillData(int.from_bytes(internal_id2,byteorder='big'), fulfill_data).transact({'from':accounts[0], 'gas': int(gas_to_spend)})

    receipt = get_receipt(tx)
    print('')
    print('Gas used in transaction: {}'.format(receipt['cumulativeGasUsed']))

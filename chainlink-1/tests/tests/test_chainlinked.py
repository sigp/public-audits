# Tests focused on the chainlinked contract
import pytest

@pytest.mark.parametrize(
    "spec_id, callback_addr, callback_fn",
    [
    # User should be able to create NewRuns with valid input params
    (b"A9E", "self", "fulfillRequest(bytes32,bytes32)"), # base case
    (b"A9E", "self", "invalid_callback_selector"), # User can input invalid callback fn
    (b"A9E", "self", ""), # User can input empty callback function
    (b"A9E", "other", "fulfillRequest(bytes32,bytes32)"), # User can specify different callback address
    (b"N/A", "self", "fulfillRequest(bytes32,bytes32)"), # specID can be anything
    ]
)
# Tests Chainlinked.newRun() with various specIDs, callback addresses/functions
def test_new_run(
        w3,
        accounts,
        oracle_deploy,
        chainlinked_test_deploy,
        get_logs_for_event,
        spec_id,
        callback_addr,
        callback_fn,
        function_selector,
        assert_tx_failed):

    (link, oracle, _, _) = oracle_deploy()
    (test, _) = chainlinked_test_deploy(link.address, oracle.address)

    # Default callback address is test.address
    callback_addr = test.address if callback_addr == "self" else accounts[1]
    callback_fn = function_selector(callback_fn)

    tx = test.functions.publicNewRun(
                                    spec_id,
                                    callback_addr,
                                    callback_fn).transact({'from': accounts[0]})

    # Get logs from event: Run.specId should be as user specified
    logs = get_logs_for_event(test.events.Run, tx)
    log_spec_id = logs[0]['args']['specId'].hex()
    log_callback_addr = logs[0]['args']['callbackAddress']
    log_callback_fn = logs[0]['args']['callbackfunctionSelector'].hex()

    # Run.spec_id and callback address should correspond with valid user inputs
    assert log_spec_id[:6] == spec_id.hex(), "Spec IDs should match"
    assert log_callback_addr == callback_addr, "Callback addresses should match"

    # Run.callbackFunctionId should be as user specified
    assert log_callback_fn == callback_fn, "Callback functions should match"


@pytest.mark.parametrize(
    "data_size, amount, should_pass",
    [
    (128, 500, True),   # base test case
    (128, 0, True), # 0 tokens staked
    (0, 500, True), # 0 request data passed
    # Users should not be able to make requests with invalid input pararms
    (128, 10001, False), # invalid token limit
    ]
)
# Tests Chainlinked.chainlinkRequest() with various data input and token allocations
def test_make_request(
        accounts,
        oracle_deploy,
        chainlinked_test_deploy,
        get_logs_for_event,
        data_size,
        amount,
        should_pass,
        function_selector,
        assert_tx_failed):

    # deploy link, oracle, and test contracts
    (link, oracle, _, _) = oracle_deploy()
    (test, _) = chainlinked_test_deploy(link.address, oracle.address)

    # give some tokens to the test contract
    link.functions.transfer(
                            test.address,
                            10000).transact({'from': accounts[0]})

    # Set up parameters for request
    specId = b"A9E"
    callbackAddress = test.address
    funcSig = function_selector("fulfillRequest(bytes32,bytes32)")
    data = " " * data_size # arbitary string of n length
    tx = test.functions.publicRequestRun(
                                            specId,
                                            callbackAddress,
                                            funcSig,
                                            data,
                                            amount)

    # Requests with valid inputs should succeed
    if should_pass:
        tx = tx.transact({'from': accounts[0]})
        # get the logs to verify the request
        logs = get_logs_for_event(test.events.ChainlinkRequested, tx)
        log_request_id = logs[0]['args']['id'].hex()
        # get the currentId for the request from the test contract
        request_id = test.functions.curRequestId().call().hex()

        # these Ids should match, indicating a request was made
        assert log_request_id == request_id, "Id's should match"

    # Requesters with insufficient tokens should fail
    else:
        assert_tx_failed(tx, {'from': accounts[0]})


def test_consumer_can_make_multiple_requests(
        oracle_deploy,
        chainlinked_test_deploy,
        accounts,
        function_selector,
        get_logs_for_event):

    (link, oracle, _, _) = oracle_deploy()
    (test, _) = chainlinked_test_deploy(link.address, oracle.address)
    link.functions.transfer(test.address, int(1e20)).transact({'from': accounts[0]})

    # First data request
    specId = "00" + "A9E"*10  # random 32 byte specId
    tx1 = test.functions.publicRequestRun(
                                        specId,
                                        test.address,
                                        function_selector("fulfill(bytes32,bytes32)"),
                                        "",
                                        10).transact({'from':accounts[0]})
    log_request_id_1 = get_logs_for_event(test.events.ChainlinkRequested, tx1)[0]['args']['id'].hex()

    # Second data request
    tx2 = test.functions.publicRequestRun(
                                        specId,
                                        test.address,
                                        function_selector("fulfill(bytes32,bytes32)"),
                                        "",
                                        10).transact({'from':accounts[0]})


    log_request_id_2 = get_logs_for_event(test.events.ChainlinkRequested, tx2)[0]['args']['id'].hex()

    # Assert that requests_IDs are different, 
    assert log_request_id_2 != log_request_id_1


def test_can_cancel_request(
        w3,
        oracle_deploy,
        chainlinked_test_deploy,
        accounts,
        get_logs_for_event,
        ganache_increase_time):

    (link, oracle, _, _) = oracle_deploy()
    (test, _) = chainlinked_test_deploy(link.address, oracle.address)
    link.functions.transfer(test.address, int(1e20)).transact({'from': accounts[0]})

    # request data
    specId = "00" + "A9E" * 10  # random 32 byte specId
    make_tx = test.functions.publicRequestRun(specId, test.address, "12345678", "", 10).transact({'from':accounts[0]})
    request_id = get_logs_for_event(test.events.ChainlinkRequested, make_tx)[0]['args']['id'].hex()

    # wait for request to expire
    ganache_increase_time(99999999)

    # requestor attempts to cancel request
    cancel_tx = test.functions.publicCancelRequest(request_id).transact({'from': accounts[0]}).hex()
    log_cancel_id = get_logs_for_event(test.events.ChainlinkCancelled, cancel_tx)[0]['args']['id'].hex()

    # Expectation: Request is canceled in Requester's own unfulfilledRequests[] log
    assert log_cancel_id == request_id

    # Now we check if request is cancelled in oracle
    expected_request_id = w3.soliditySha3(
                                    ["address", "uint256"],
                                    [test.address, 1]).hex()

    oracle_cancelled_id = get_logs_for_event(oracle.events.CancelRequest,
    cancel_tx)[0]['args']['requestId']

    # Expectation: Request is canceled in Oracle (pre-fulfillment)
    assert expected_request_id == "0x" + oracle_cancelled_id.hex()


def test_cannot_cancel_if_different_callback_addr(
        w3,
        oracle_deploy,
        chainlinked_test_deploy,
        accounts,
        get_logs_for_event,
        ganache_increase_time,
        assert_tx_failed):

    (link, oracle, _, _) = oracle_deploy()
    (test, _) = chainlinked_test_deploy(link.address, oracle.address)
    link.functions.transfer(test.address, int(1e20)).transact({'from': accounts[0]})

    # request data, where callback addr is a different address
    specId = "00" + "A9E" * 10  # random 32 byte specId
    make_tx = test.functions.publicRequestRun(specId, accounts[1], "12345678", "", 10).transact({'from':accounts[0]})
    request_id = get_logs_for_event(test.events.ChainlinkRequested, make_tx)[0]['args']['id'].hex()
    ganache_increase_time(99999999)
    cancel_tx = test.functions.publicCancelRequest(request_id)

    # Expectation: original user is not able to cancel their own request!
    assert_tx_failed(cancel_tx, {'from': accounts[0]})


def test_can_fulfill_request(
        accounts,
        oracle_deploy,
        chainlinked_test_deploy,
        function_selector,
        get_logs_for_event
        ):
    # Setup
    (link, oracle, _, _) = oracle_deploy()
    (test, _) = chainlinked_test_deploy(link.address, oracle.address)
    link.functions.transfer(test.address, int(1e20)).transact({'from': accounts[0]})

    # User makes a data request:
    specId = "00" + "A9E" * 10  # random 32 byte specId
    functionSig = function_selector("fulfillRequest(bytes32,bytes32)")
    make_tx = test.functions.publicRequestRun(specId, test.address, functionSig, "", 10).transact({'from':accounts[0]})
    request_id = get_logs_for_event(test.events.ChainlinkRequested, make_tx)[0]['args']['id']

    # Oracle fulfills request:
    fulfill_data = "00"*32  # 0 value, why not
    fulfill_tx = oracle.functions.fulfillData(int.from_bytes(request_id,byteorder='big'),
    fulfill_data).transact({'from':accounts[0], 'gas':500000})
    fulfill_id = get_logs_for_event(test.events.ChainlinkFulfilled, fulfill_tx)[0]['args']['id'].hex()

    # Expectation: ChainlinkFulfilled is emitted, i.e. request is fulfilled
    assert fulfill_id == request_id.hex()


def test_cannot_fulfill_request_if_different_callback_addr(
        accounts,
        oracle_deploy,
        chainlinked_test_deploy,
        get_logs_for_event,
        function_selector,
        assert_tx_failed
        ):

    # Setup
    (link, oracle, _, _) = oracle_deploy()
    (test, _) = chainlinked_test_deploy(link.address, oracle.address)
    link.functions.transfer(test.address, int(1e20)).transact({'from': accounts[0]})

    # User makes a data request:
    specId = "00" + "A9E" * 10  # random 32 byte specId
    functionSig = function_selector("fulfillRequest(bytes32,bytes32)")
    make_tx = test.functions.publicRequestRun(specId, accounts[1], functionSig, "", 10).transact({'from':accounts[0]})
    request_id = get_logs_for_event(test.events.ChainlinkRequested, make_tx)[0]['args']['id']

    # Oracle fulfills request:
    fulfill_data = "00"*32  # 0 value, why not

    # this trx succeeds even though chainlinks reverts
    fulfill_tx = oracle.functions.fulfillData(int.from_bytes(request_id,
    byteorder='big'), fulfill_data).transact({'from':accounts[0], 'gas':500000})

    # Expectation: Requester didn't emit any ChainlinkFulfilled events
    log_fulfilled = get_logs_for_event(test.events.ChainlinkFulfilled, fulfill_tx)
    assert len(log_fulfilled) == 0


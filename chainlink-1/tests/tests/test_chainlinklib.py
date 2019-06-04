# These are a set of tests to check the chainlinklib contract, with a run
# struct in state. These tests are not designed to verify the CBOR solidity
# library, rather check the ChainlinkedLib wrapper.

import pytest


@pytest.mark.parametrize(
    "data_bytes",
    [
        (1),
        (2),
        (10),
        (127),
        (128),
        (129),
        (500),
        (1000),
    ]
)
def test_adding_data_sizes(
                        accounts,
                        data_bytes,
                        chainlinklib_test_deploy):
    """
    This checks a variety of data sizes that can be encoded and
    dynamically adjusted in the chainlinklib contract, which initializes the
    buffer to 128 bytes.
    """

    # standard transaction dict
    transaction = {'from': accounts[0]}

    # set up an instance of ChainlinkLibTest (see
    # contracts/ChainlinkLibTest in the tests folder).
    (tester, _) = chainlinklib_test_deploy()

    # set up basic parameters
    spec_id = "0"*61 + "A9E"
    callback_address = "0x" + "0"*37 + "A9e"
    function_sig = "A9EA9EFF"

    # initialize run struct
    tester.functions.initialize(spec_id,
                                callback_address,
                                function_sig).transact(transaction)

    # add bytes of data to the buffer
    # build the string
    data = ""
    for no_bytes in range(data_bytes):
        data += "FF"

    tester.functions.addBytes(data, data).transact(transaction)

    # read the result
    result = tester.functions.readRunBuffer().call()
    print("")  # new line
    print("Buffer contents: {}".format(result.hex()))

    # The buffer should dynamically resize and return the bytes we gave it
    assert result.hex()[-2*data_bytes:] == data.lower(), "Buffer doesn't store required data"


def test_adding_string_array(
                        accounts,
                        chainlinklib_test_deploy):
    """
    This checks the adding of string array data types
    """

    # standard transaction dict
    transaction = {'from': accounts[0]}

    # set up an instance of ChainlinkLibTest (see
    # contracts/ChainlinkLibTest in the tests folder).
    (tester, _) = chainlinklib_test_deploy()

    # set up basic parameters
    spec_id = "0"*61 + "A9E"
    callback_address = "0x" + "0"*37 + "A9e"
    function_sig = "A9EA9EFF"

    # initialize run struct
    tester.functions.initialize(spec_id,
                                callback_address,
                                function_sig).transact(transaction)

    # string array
    key = "StringArrayTest"
    array = ["     "]*10  # 10 strings consisting of 5 spaces

    tester.functions.addStringArray(key, array).transact(transaction)

    # read the result
    result = tester.functions.readRunBuffer().call()
    print("")  # new line
    print("Buffer contents: {}".format(result.hex()))

    expected_hex_result = "bf6f537472696e674172726179546573749f652020202020652020202020652020202020652020202020652020202020652020202020652020202020652020202020652020202020652020202020ff"

    # Expect to have encoded the string as utf8
    assert result.hex() == expected_hex_result, "Buffer doesn't encode data as expected"


def test_add_bytes(
                        accounts,
                        chainlinklib_test_deploy):
    """
    This checks adding the bytes data type
    """

    # standard transaction dict
    transaction = {'from': accounts[0]}

    # set up an instance of ChainlinkLibTest (see
    # contracts/ChainlinkLibTest in the tests folder).
    (tester, _) = chainlinklib_test_deploy()

    # set up basic parameters
    spec_id = "0"*61 + "A9E"
    callback_address = "0x" + "0"*37 + "A9e"
    function_sig = "A9EA9EFF"

    # initialize run struct
    tester.functions.initialize(spec_id,
                                callback_address,
                                function_sig).transact(transaction)

    # bytes data type
    key = "Bytes"
    data = b'\xAF\xFF\xAF'

    tester.functions.addBytes(key, data).transact(transaction)

    # read the result
    result = tester.functions.readRunBuffer().call()
    print("")  # new line
    print("Buffer contents: {}".format(result.hex()))

    # Expect to have added the bytes to the end of the buffer
    assert result.hex()[-6:] == data.hex(), "Buffer doesn't encode data as expected"


def test_close_buffer(
                        accounts,
                        chainlinklib_test_deploy):
    """
    This checks adding the bytes data type
    """

    # standard transaction dict
    transaction = {'from': accounts[0]}

    # set up an instance of ChainlinkLibTest (see
    # contracts/ChainlinkLibTest in the tests folder).
    (tester, _) = chainlinklib_test_deploy()

    # set up basic parameters
    spec_id = "0"*61 + "A9E"
    callback_address = "0x" + "0"*37 + "A9e"
    function_sig = "A9EA9EFF"

    # initialize run struct
    tester.functions.initialize(spec_id,
                                callback_address,
                                function_sig).transact(transaction)

    # Note: We can close multiple times.
    tester.functions.close().transact(transaction)
    tester.functions.close().transact(transaction)
    tester.functions.close().transact(transaction)
    tester.functions.close().transact(transaction)

    # read the result
    result = tester.functions.readRunBuffer().call()
    print("")  # new line
    print("Buffer contents: {}".format(result.hex()))

    # Expect to have added the bytes to the end of the buffer
    assert result.hex()[-8:] == "ffffffff", "Buffer doesn't add expected \
                            terminating bytes"

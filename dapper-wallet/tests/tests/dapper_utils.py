import pytest

INTERFACE_TYPES = {
    # 'ERC721': '0x80ac58cd', Not implemented, only receiver
    # 'ERC725': '0xd202158d', Removed as the new updated contract does not support ERC725 anymore
    'ERC223': '0xc0ee0b8a',
    'ERC165': '0x01ffc9a7',
    'ERC1271': '0x20c13b0b' # Added support for ERC1271 in new contract version
}


@pytest.fixture
def invoke_tuple():
    """
    Formats the tuple part of the invoke
    """
    def method(to, amount, data=[]):
        fb = b''
        fb += bytes.fromhex(to[2:])
        fb += amount.to_bytes(32, 'big')
        if len(data) > 0:
            fb += (len(data)).to_bytes(32, 'big')
            fb += data
        else:
            fb += int(0).to_bytes(32, 'big')
        return fb
    return method


@pytest.fixture
def invoke_data(w3, invoke_tuple):
    """
    Formats the data for invoke
    """
    def method(revert, to, amount, buf):
        # print("Revert: {}\n TO: {}\n AMOUNT: {}\n BUF: {}\n BUFLEN: {}".format(revert, to, amount, buf.hex(), len(buf)))
        fb = b''
        fb += revert.to_bytes(1, 'big')

        fb += invoke_tuple(to, amount, buf)

#         fb += bytes.fromhex(to[2:])
#         fb += amount.to_bytes(32, 'big')
#         fb += (len(buf)).to_bytes(32, 'big')
#         fb += buf
        return fb
    return method


@pytest.fixture
def invoke1_sign_data(w3):
    """
    Formats the data and provides the hash for using `invoke1`.
    """
    def method(wallet, nonce, address, data):
        databytes = b'' + 0x19.to_bytes(1, 'big') + 0x0.to_bytes(1, 'big')
        databytes += bytes.fromhex(wallet.address[2:])
        databytes += nonce.to_bytes(32, 'big')
        databytes += bytes.fromhex(address[2:])
        databytes += data

        return {'bytes': databytes, 'hash': w3.sha3(databytes)}
    return method


@pytest.fixture
def interface_ids():
    """
    Provides a list of the interfaces as described in the contracts.
    """
    return INTERFACE_TYPES


@pytest.fixture
def ready_invoke_chain(invoke_tuple):
    """
    Ready the information to send an `invoke`.
    """
    def method(revert, tuples):
        fb = b''
        fb += revert.to_bytes(1, 'big')

        for tup in tuples:
            fb += invoke_tuple(tup[0], tup[1], tup[2])

        return fb

    return method

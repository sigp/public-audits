import pytest


@pytest.fixture
def send_eth(w3):
    def send_eth(from_addr, to_addr, value):
        return w3.eth.sendTransaction({
            'from': from_addr,
            'to': to_addr,
            'value': value
        })
    return send_eth

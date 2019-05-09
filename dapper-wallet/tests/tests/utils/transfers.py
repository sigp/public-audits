import pytest


@pytest.fixture
def send_eth(w3):
    def send_eth(from_addr, to_addr, value, convert_from_ether=False):
        if convert_from_ether:
            value = w3.toWei(value, 'ether')
        return w3.eth.sendTransaction({
            'from': from_addr,
            'to': to_addr,
            'value': value
        })
    return send_eth


@pytest.fixture
def send_eth_return_rcpt(send_eth, w3):
    def method(from_addr, to_addr, value, convert_from_ether=False):
        tx = send_eth(from_addr, to_addr, value, convert_from_ether)
        return w3.eth.getTransactionReceipt(tx)
    return method

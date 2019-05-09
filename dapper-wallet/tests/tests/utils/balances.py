import pytest


@pytest.fixture
def zero_address():
    return '0x0000000000000000000000000000000000000000'


@pytest.fixture
def get_balance(w3):
    def get_balance(addr):
        return w3.eth.getBalance(addr)
    return get_balance

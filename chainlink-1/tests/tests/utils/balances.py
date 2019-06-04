import pytest


@pytest.fixture
def get_balance(w3):
    def get_balance(addr):
        return w3.eth.getBalance(addr)
    return get_balance

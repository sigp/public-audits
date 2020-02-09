import pytest


@pytest.fixture
def block_timestamp(w3):
    def method(block='latest'):
        return w3.eth.getBlock(block).timestamp
    return method

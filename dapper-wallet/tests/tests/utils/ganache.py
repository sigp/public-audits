import pytest


@pytest.fixture
def ganache_mine_block(w3):
    """
    Forces ganache mine a block.
    """
    def method(blocks=1):
        for i in range(0, blocks):
            w3.manager.request_blocking(
                "evm_mine", []
            )
    return method


@pytest.fixture
def ganache_increase_time(w3, ganache_mine_block):
    """
    Create a new block, ensuring its timestamp is
    delta higher than the previous block.
    """
    def method(delta):
        w3.manager.request_blocking(
            "evm_increaseTime",
            [delta]
        )
        ganache_mine_block()

    return method


@pytest.fixture
def ganache_set_time(w3, ganache_increase_time,
                     block_timestamp):
    """
    Create a new block with a specified timestamp. Timestamp must
    be in the future.
    """
    def method(future_time):
        present_time = block_timestamp()
        assert future_time >= present_time, "New time must be in the future."
        ganache_increase_time(future_time - present_time)
    return method

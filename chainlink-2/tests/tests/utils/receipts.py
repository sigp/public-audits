import pytest


@pytest.fixture
def get_receipt(w3):
    def get_receipt(tx_hash):
        return w3.eth.getTransactionReceipt(tx_hash)
    return get_receipt


@pytest.fixture
def get_logs(w3):
    """
    Returns all logs picked up from a tx_hash
    """
    def get_logs(tx_hash):
        return w3.eth.getTransactionReceipt(tx_hash).logs
    return get_logs


@pytest.fixture
def get_logs_for_event(w3):
    """
    Returns all logs that match a given ContractEvent.
    Example: get_logs_with_name(c.events.myContract, tx_hash)
    """
    def get_log(event, tx_hash):
        r = w3.eth.getTransactionReceipt(tx_hash)
        return(event().processReceipt(r))
    return get_log

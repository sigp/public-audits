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


@pytest.fixture
def ether_used_for_gas(w3):
    """
    Calculates the total amount of ether that was spent on gas, given a receipt or list of receipts.
    """

    def _gas_used_in_ether(receipt):

        if isinstance(receipt, bytes):
            receipt = w3.eth.getTransactionReceipt(receipt)

        if isinstance(receipt.gasUsed, int):
            return w3.fromWei(receipt.gasUsed * w3.eth.gasPrice, 'ether')

        raise Exception("Receipt is unknown type.")


    def method(receipts):
        eth_used_for_gas = 0
        if isinstance(receipts, list):
            for rcpt in receipts:
                eth_used_for_gas += _gas_used_in_ether(rcpt)
        else:
            # it is a single receipt, not a list of receipts
            eth_used_for_gas = _gas_used_in_ether(receipts)

        return eth_used_for_gas

    return method

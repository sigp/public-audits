import pytest


@pytest.fixture
def assert_tx_failed():
    def assert_revert(tx, tx_details, msg=""):
        message = "Transaction did not fail. ({0})".format(msg)
        with pytest.raises(ValueError, message=message) as e:
            tx.transact(tx_details)

        assert "VM Exception while processing transaction" in str(e), \
               "Did not find VM exception in error message."
    return assert_revert


@pytest.fixture
def assert_sendtx_failed(w3):
    def sendtx_failed(tx_details):
        with pytest.raises(ValueError, message="Transaction did not fail.") as e:
            w3.eth.sendTransaction(tx_details)

        assert "VM Exception while processing transaction" in str(e), \
               "Did not find VM exception in error message."
    return sendtx_failed

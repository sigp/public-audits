import pytest


@pytest.fixture
def assert_tx_failed():
    def assert_revert(tx, tx_details):
        with pytest.raises(ValueError, message="Transaction did not fail.") as e:
            tx.transact(tx_details)

        assert "VM Exception while processing transaction" in str(e), \
               "Did not find VM exception in error message."
    return assert_revert


@pytest.fixture
def assert_tx_gas_failed():
    """
    This fixture exists due to a Ganache issue - instead of the transaction
    failing, it returns the response that the contract is not deployable.

    Expected action: Transaction failed due to gas limit.
    """
    def assert_gas_failed(tx, tx_details):
        with pytest.raises(ValueError, message="Transaction did not fail.") as e:
            tx.transact(tx_details)

        assert "gas limits" in str(e), \
            "Did not find Gas Limit error in error message."
    return assert_gas_failed

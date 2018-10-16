import pytest


@pytest.mark.parametrize(
    "owners, required, confirmations, should_transact",
    [
        (8, 5, 5, True),
        (2, 1, 1, True),
        (4, 4, 4, True),
        (1, 1, 1, True),
        (20, 10, 10, True),
        (20, 10, 1, False),
        (8, 5, 4, False),
        (2, 2, 1, False),
    ]
)
def test_execute_transaction(accounts, multisig_deploy, assert_tx_failed,
                             owners, required, confirmations,
                             should_transact, send_eth, get_balance,
                             multisig_submitTransaction,
                             multisig_confirmTransaction,
                             multisig_confirmationCount):
    assert confirmations <= owners, "test is invalid"
    assert confirmations <= required, "test is invalid"
    assert confirmations > 0, "test is invalid"
    assert required <= owners, "test is invalid"

    owner_accounts = accounts[0:owners]

    submitter = owner_accounts[0]
    confirmer_accounts = owner_accounts[1: confirmations]
    destination = accounts[-1]
    value = 1 * 10**18

    (c, _) = multisig_deploy(
        owners=owner_accounts,
        required=required,
        recoveryModeTriggerTime=1000
    )

    send_eth(accounts[0], c.address, value)
    assert get_balance(c.address) == value, "contract does not have required \
            balance"

    transaction = {
        'destination': destination,
        'value': value,
        'data': b""
    }

    tx_id = multisig_submitTransaction(
        contract=c,
        transaction=transaction,
        from_addr=submitter
    )

    for addr in confirmer_accounts:
        if addr != submitter:
            multisig_confirmTransaction(c, tx_id, addr)

    assert multisig_confirmationCount(c, tx_id) == confirmations

    if should_transact:
        assert get_balance(c.address) == 0
    else:
        assert get_balance(c.address) == value

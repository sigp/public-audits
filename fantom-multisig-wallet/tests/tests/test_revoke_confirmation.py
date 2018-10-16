

def test_confirmation_revocation(accounts, multisig_deploy, assert_tx_failed,
                                 send_eth, get_balance,
                                 multisig_submitTransaction,
                                 multisig_confirmTransaction,
                                 multisig_revokeConfirmation,
                                 multisig_executeTransaction,
                                 multisig_confirmationCount):
    owner_count = 5
    owners = accounts[0:owner_count]
    required_confirmations = 3
    value = 1 * 10**18

    submitter = owners[0]
    destination = accounts[-1]
    value = 1 * 10**18

    (c, _) = multisig_deploy(
        owners=owners,
        required=required_confirmations,
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

    revoker = accounts[1]
    confirmer = accounts[2]

    assert multisig_confirmationCount(c, tx_id) == 1

    multisig_confirmTransaction(c, tx_id, from_addr=revoker)

    assert multisig_confirmationCount(c, tx_id) == 2

    multisig_revokeConfirmation(c, tx_id, from_addr=revoker)

    assert multisig_confirmationCount(c, tx_id) == 1

    multisig_confirmTransaction(c, tx_id, from_addr=confirmer)

    assert multisig_confirmationCount(c, tx_id) == 2

    executed = multisig_executeTransaction(c, tx_id, from_addr=submitter)
    assert not executed

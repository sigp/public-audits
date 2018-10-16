import pytest


def test_updates_last_tx_time(accounts,
                              send_eth, get_balance,
                              block_timestamp,
                              ganache_set_time,
                              multisig_deploy,
                              multisig_submitTransaction,
                              multisig_executeTransaction,
                              multisig_lastTransactionTime):

    owner_count = 1
    owners = accounts[0:owner_count]
    required_confirmations = owner_count
    value = 1 * 10**18

    (c, _) = multisig_deploy(
        owners=owners,
        required=required_confirmations,
        recoveryModeTriggerTime=2 * 60**2   # 2 hours
    )
    deployed_time = block_timestamp()

    send_eth(accounts[0], c.address, value)
    assert get_balance(c.address) == value

    assert multisig_lastTransactionTime(c) == deployed_time

    transaction = {
        'destination': accounts[-1],
        'value': value,
        'data': b""
    }

    ganache_set_time(deployed_time + 60**2)     # 1 hour

    multisig_submitTransaction(
        contract=c,
        transaction=transaction,
        from_addr=owners[0]
    )

    assert multisig_lastTransactionTime(c) == block_timestamp()


@pytest.mark.parametrize(
    "trigger_time, elapsed_time, should_enter_recovery",
    [
        (100, 50, False),
        (100000, 50, False),
        (937502340, 100, False),
        (100, 100, True),
        (1, 100, True),
        (100, 101, True),
        (100, 10000, True),
    ]
)
def test_enters_recover(accounts, assert_tx_failed,
                        send_eth, get_balance,
                        trigger_time, elapsed_time,
                        should_enter_recovery,
                        block_timestamp,
                        ganache_set_time,
                        multisig_deploy,
                        multisig_submitTransaction,
                        multisig_executeTransaction,
                        multisig_enterRecoveryMode,
                        multisig_confirmationCount):

    owner_count = 5
    owners = accounts[0:owner_count]
    required_confirmations = 3
    value = 1 * 10**18

    (c, _) = multisig_deploy(
        owners=owners,
        required=required_confirmations,
        recoveryModeTriggerTime=trigger_time
    )
    deployed_time = block_timestamp()

    send_eth(accounts[0], c.address, value)
    assert get_balance(c.address) == value

    transaction = {
        'destination': accounts[-1],
        'value': value,
        'data': b""
    }

    tx_id = multisig_submitTransaction(
        contract=c,
        transaction=transaction,
        from_addr=owners[0]
    )

    ganache_set_time(deployed_time + elapsed_time)

    if should_enter_recovery:
        multisig_enterRecoveryMode(c, owners[0])
        assert c.functions.required().call() == required_confirmations - 1
    else:
        assert_tx_failed(
            lambda: multisig_enterRecoveryMode(c, owners[0])
        )
        executed = multisig_executeTransaction(c, tx_id, owners[0])
        assert not executed
        assert get_balance(c.address) == value


@pytest.mark.parametrize(
    "required, confirmations, recovery_mode_times, allowed",
    [
        (3, 2, 1, True),
        (5, 2, 1, False),
        (5, 2, 3, True),
        (5, 3, 2, True),
        (5, 1, 2, False),
        (5, 1, 3, False),
        (5, 1, 4, True),
        (5, 3, 1, False),
    ]
)
def test_recovery_iterations(accounts, assert_tx_failed,
                             send_eth, get_balance,
                             required, confirmations,
                             recovery_mode_times, allowed,
                             block_timestamp,
                             ganache_set_time,
                             multisig_deploy,
                             multisig_submitTransaction,
                             multisig_executeTransaction,
                             multisig_confirmTransaction,
                             multisig_enterRecoveryMode,
                             multisig_confirmationCount):

    owner_count = 10 
    owners = accounts[0:owner_count]
    required_confirmations = required
    value = 1 * 10**18
    elapsed_time = 150

    (c, _) = multisig_deploy(
        owners=owners,
        required=required_confirmations,
        recoveryModeTriggerTime=100
    )
    deployed_time = block_timestamp()

    send_eth(accounts[0], c.address, value)
    assert get_balance(c.address) == value

    transaction = {
        'destination': accounts[-1],
        'value': value,
        'data': b""
    }

    tx_id = multisig_submitTransaction(
        contract=c,
        transaction=transaction,
        from_addr=owners[0]
    )

    # Confirm the transaction
    for account_index in range(confirmations-1):
        multisig_confirmTransaction(c, tx_id, accounts[account_index+1])

    for recovery_iteration in range(recovery_mode_times-1):
        deployed_time = block_timestamp()
        ganache_set_time(deployed_time + elapsed_time)

        assert multisig_confirmationCount(c, tx_id) == confirmations
        
        multisig_enterRecoveryMode(c, owners[0])
        assert c.functions.required().call() == required_confirmations \
            - (recovery_iteration + 1)
        # Should not be able to withdraw yet
        executed = multisig_executeTransaction(c, tx_id, owners[0])
        assert not executed
        assert get_balance(c.address) == value

    # The last iteration
    deployed_time = block_timestamp()
    ganache_set_time(deployed_time + elapsed_time)

    assert multisig_confirmationCount(c, tx_id) == confirmations
    
    multisig_enterRecoveryMode(c, owners[0])
    assert c.functions.required().call() == required_confirmations \
        - recovery_mode_times

    # Should not be able to withdraw yet
    executed = multisig_executeTransaction(c, tx_id, owners[0])
    if allowed:
        assert executed
        assert get_balance(c.address) == 0
    else:
        assert not executed
        assert get_balance(c.address) == value

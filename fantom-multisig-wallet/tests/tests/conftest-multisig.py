import pytest


@pytest.fixture
def deploy_multisig(multisig_deploy):
    """
    For legacy use
    """
    return multisig_deploy


@pytest.fixture
def multisig_deploy(accounts, deploy):
    """
    Deploys an instance of the Fantom MultiSigWallet contract.
    """
    def method(owners, required, recoveryModeTriggerTime):
        (c, r) = deploy(
            contract="MultiSigWallet",
            transaction={
                # We're always using the same address because
                # the deployer address is inconsequential.
                'from': accounts[0]
            },
            args={
                '_owners': owners,
                '_required':  required,
                '_recoveryModeTriggerTime': recoveryModeTriggerTime
            }
        )
        return (c, r)
    return method


@pytest.fixture
def multisig_submitTransaction(get_logs_for_event):
    def method(contract, transaction, from_addr):
        logs = get_logs_for_event(
            contract.events.Submission,
            contract.functions.submitTransaction(**transaction).transact({
                'from': from_addr
            })
        )
        return logs[0].args.transactionId
    return method


@pytest.fixture
def multisig_executeTransaction(get_logs_for_event):
    """
    Calls "executeTransaction" and returns true if an execution
    log was created.
    """
    def method(contract, tx_id, from_addr):
        logs = get_logs_for_event(
            contract.events.Execution,
            contract.functions.executeTransaction(tx_id).transact({
                'from': from_addr
            })
        )
        return len(logs) > 0
    return method


@pytest.fixture
def multisig_confirmTransaction(get_logs_for_event):
    def method(contract, tx_id, from_addr):
        logs = get_logs_for_event(
            contract.events.Confirmation,
            contract.functions.confirmTransaction(tx_id).transact({
                'from': from_addr
            })
        )
        assert logs[0].args.sender == from_addr
        assert logs[0].args.transactionId == tx_id
    return method


@pytest.fixture
def multisig_revokeConfirmation(get_logs_for_event):
    def method(contract, tx_id, from_addr):
        logs = get_logs_for_event(
            contract.events.Revocation,
            contract.functions.revokeConfirmation(tx_id).transact({
                'from': from_addr
            })
        )
        assert logs[0].args.sender == from_addr
        assert logs[0].args.transactionId == tx_id
    return method


@pytest.fixture
def multisig_confirmationCount():
    def method(contract, tx_id):
        return len(
            contract.functions.getConfirmations(tx_id).call()
        )
    return method


@pytest.fixture
def multisig_enterRecoveryMode(get_logs_for_event):
    def method(contract, from_addr):
        logs = get_logs_for_event(
            contract.events.RecoveryModeActivated,
            contract.functions.enterRecoveryMode().transact({
                'from': from_addr
            })
        )
        assert len(logs) == 1
    return method


@pytest.fixture
def multisig_lastTransactionTime():
    def method(contract):
        return contract.functions.lastTransactionTime().call()
    return method

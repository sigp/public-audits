import pytest

"""

"""
@pytest.mark.parametrize(
    "owners, required, confirmations, submitter_id, initial_balance, value_to_send, dst_contract_id, tx_should_execute",
    [
        (10,10,10,5, 50,1,1, True),
        (10,1,5,2, 30,1,1, True),
        (10,1,1,0, 1,1,1, True),
        (1,1,1,0, 1,1,1, True),
        (10,5,5,9, 50,50,1, True),
        (10,10,4,5, 50,1,2, False),
        (10,1,10,2, 30,1,2, True),
        (10,1,1,0, 1,1,2, True),
        (1,1,1,0, 1,1,2, True),
        (10,5,5,9, 50,50,2, True),
        (10,10,4,5, 50,1,3, False),
        (10,1,10,2, 30,1,3, False),
        (10,1,1,0, 1,1,3, False),
        (1,1,1,0, 1,1,3, False),
        (10,5,1,9, 50,50,3, False),
    ]
)
def test_scenarios(accounts, deploy_multisig, assert_tx_failed, deploy,
                             owners, required, confirmations, initial_balance,
                             value_to_send, dst_contract_id,
                             tx_should_execute,
                             submitter_id, get_logs_for_event, send_eth,
                             get_balance):
    """
    Tests various multisig options deployed to a variety of contracts
    """
    assert confirmations <= owners, "test is invalid"
    assert confirmations > 0, "test is invalid"
    assert required <= owners, "test is invalid"
    assert len(accounts) >= owners, "not enough accounts for test"
    assert value_to_send <= initial_balance, "not enough initial balance to perform test" 

    owner_accounts = accounts[0:owners]
    submitter = owner_accounts[submitter_id]
    confirmer_accounts = owner_accounts[0: confirmations]
    value = initial_balance * int(1e18) # convert to wei

    (c, _) = deploy_multisig(
        owners=owner_accounts,
        required=required,
        recoveryModeTriggerTime=1000
    )


    # deploy a destination contract 
    (d,_) = deploy(
            contract="Contract" + str(dst_contract_id),
            transaction={'from': accounts[0]},
            args={}
            )
    destination = d.address
    
    # send ether to the multisig
    send_eth(accounts[0], c.address, value)
    assert get_balance(c.address) == value, "contract does not have required \
            balance"

    transaction = {
        'destination': destination,
        'value': value_to_send*int(1e18),
        'data': b""
    }
    logs = get_logs_for_event(
        c.events.Submission,
        c.functions.submitTransaction(**transaction).transact({
            'from': submitter 
        })
    )
    tx_id = logs[0].args.transactionId
    print(logs)

    confirmations = 1;
    if confirmations != required:
        for addr in confirmer_accounts:
            if addr != submitter:
                c.functions.confirmTransaction(tx_id).transact({'from': addr})
                confirmations+=1
                if confirmations >= required:
                    break

    if tx_should_execute:
        assert c.functions.getConfirmationCount(tx_id).call() == \
           required 
        assert c.functions.isConfirmed(tx_id).call() 
        print(c.functions.transactions(tx_id).call())


    if tx_should_execute:
        assert get_balance(c.address) == (initial_balance - value_to_send)*int(1e18)
        assert c.functions.transactions(tx_id).call()[3]
    else: 
        assert get_balance(c.address) == initial_balance*int(1e18)
        assert not (c.functions.transactions(tx_id).call()[3])

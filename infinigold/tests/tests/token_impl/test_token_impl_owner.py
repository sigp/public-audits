def test_token_impl_owner(token_impl_initialize_and_deploy, accounts, assert_tx_failed, get_logs_for_event):
    # Deploy a TokenImpl with account[0] as owner
    (token_impl, token_impl_r) = token_impl_initialize_and_deploy("Infinigold", "IFG", 2)

    ### Valid owner operations
    # Confirm account[0] is owner
    assert token_impl.functions.isOwner(accounts[0]).call()

    # Add account[1] as an owner
    tx = token_impl.functions.addOwner(accounts[1]).transact({'from': accounts[0]})
    assert token_impl.functions.isOwner(accounts[1]).call()
    logs = get_logs_for_event(token_impl.events.OwnerAdded, tx)
    assert logs[0]['args']['account'] == accounts[1]

    # Add account[2] as an owner by accounts[1]
    tx = token_impl.functions.addOwner(accounts[2]).transact({'from': accounts[1]})
    assert token_impl.functions.isOwner(accounts[2]).call()
    logs = get_logs_for_event(token_impl.events.OwnerAdded, tx)
    assert logs[0]['args']['account'] == accounts[2]

    # Remove account[0]
    tx = token_impl.functions.removeOwner(accounts[0]).transact({'from': accounts[1]})
    assert not token_impl.functions.isOwner(accounts[0]).call()
    logs = get_logs_for_event(token_impl.events.OwnerRemoved, tx)
    assert logs[0]['args']['account'] == accounts[0]

    ### Invalid Owner Operations
    ## Note account[2] is the only owner
    # Remove account[1] by account[1]
    assert_tx_failed(token_impl.functions.removeOwner(accounts[1]), {'from': accounts[1]})

    # Remove owner while not owner
    assert_tx_failed(token_impl.functions.removeOwner(accounts[2]), {'from': accounts[0]})

    # Add owner while not owner
    assert_tx_failed(token_impl.functions.addOwner(accounts[0]), {'from': accounts[0]})

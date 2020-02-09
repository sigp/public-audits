def test_owner(token_proxy_initialize_and_deploy, accounts, assert_tx_failed, get_logs_for_event):
    # Deploy a TokenImpl with account[0] as owner
    (token_proxy_as_impl, token_proxy) = token_proxy_initialize_and_deploy("Infinigold", "PMG", 2)

    ### Valid owner operations
    # Confirm account[0] is owner
    assert token_proxy_as_impl.functions.isOwner(accounts[0]).call()

    # Add account[1] as an owner
    tx = token_proxy_as_impl.functions.addOwner(accounts[1]).transact({'from': accounts[0]})
    assert token_proxy_as_impl.functions.isOwner(accounts[1]).call()
    logs = get_logs_for_event(token_proxy_as_impl.events.OwnerAdded, tx)
    assert logs[0]['args']['account'] == accounts[1]

    # Add account[2] as an owner by accounts[1]
    tx = token_proxy_as_impl.functions.addOwner(accounts[2]).transact({'from': accounts[1]})
    assert token_proxy_as_impl.functions.isOwner(accounts[2]).call()
    logs = get_logs_for_event(token_proxy_as_impl.events.OwnerAdded, tx)
    assert logs[0]['args']['account'] == accounts[2]

    # Remove account[0]
    tx = token_proxy_as_impl.functions.removeOwner(accounts[0]).transact({'from': accounts[1]})
    assert not token_proxy_as_impl.functions.isOwner(accounts[0]).call()
    logs = get_logs_for_event(token_proxy_as_impl.events.OwnerRemoved, tx)
    assert logs[0]['args']['account'] == accounts[0]


    ### Invalid Owner Operations
    ## Note acount[1] and account[2] are owners
    # Remove account[1] by account[1]
    assert_tx_failed(token_proxy_as_impl.functions.removeOwner(accounts[1]), {'from': accounts[1]})

    # Remove owner while not owner
    assert_tx_failed(token_proxy_as_impl.functions.removeOwner(accounts[2]), {'from': accounts[0]})

    # Add owner while not owner
    assert_tx_failed(token_proxy_as_impl.functions.addOwner(accounts[0]), {'from': accounts[0]})

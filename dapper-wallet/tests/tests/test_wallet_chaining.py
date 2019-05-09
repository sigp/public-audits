from eth_account import Account


def test_invoke0_can_chain(
        fullwallet_deploy,
        assert_tx_failed,
        zero_address,
        accounts,
        invoke_data,
        ready_invoke_chain,
        invoke1_sign_data,
        get_logs_for_event,
        w3):
    """
    Check that invoke0 can chain commands.
    """

    signer = Account.privateKeyToAccount('0xed765f17c0930ed68ae04a929548f4386d50236903016c0e01e191670543fab7')
    cosigner = Account.privateKeyToAccount('0x989dbcbd23972f521370a8b13462bf915489b24e11a1bb724935a19fff036fb5')

    (wallet, _, _) = fullwallet_deploy(
        accounts[1],
        accounts[1],
        accounts[3]
    )

    # Authorize
    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[signer.address, int(cosigner.address, 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    wallet.functions.invoke0(data).transact({'from': accounts[1]})

    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[accounts[2], int(accounts[2], 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    wallet.functions.invoke0(data).transact({'from': accounts[1]})

    wallet.fallback.transact({'from': signer.address, 'value': w3.toWei(5, 'ether')})

    # invoke0 - can we send eth to 5 accounts and then invoke an account?

    sending_data = []
    prev_balance = []
    for acc in accounts[5:10]:
        sending_data.append((acc, w3.toWei(1, 'ether'), []))
        prev_balance.append(w3.eth.getBalance(acc))

    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[accounts[5], int(cosigner.address, 0)]
    )

    sending_data.append((wallet.address, 0, bytes.fromhex(args_encoded[2:])))

    data = ready_invoke_chain(1, sending_data)

    tx_h = wallet.functions.invoke0(data).transact({'from': accounts[2]})

    # No revert == success?
    tx_success_event = get_logs_for_event(
        wallet.events.InvocationSuccess,
        tx_h.hex()
    )
    tx_auth_event = get_logs_for_event(
        wallet.events.Authorized,
        tx_h.hex()
    )

    assert tx_success_event[0]['args']['result'] == 0, "Result shows revert"
    assert tx_success_event[0]['args']['numOperations'] == 6, "Incorect numOperations"
    assert tx_auth_event[0]['args']['authorizedAddress'] == accounts[5], "Incorrect account authorized"


def test_invoke1_can_chain(
        fullwallet_deploy,
        assert_tx_failed,
        zero_address,
        accounts,
        invoke_data,
        ready_invoke_chain,
        invoke1_sign_data,
        get_logs_for_event,
        w3):

    """
    Check that invoke1 can chain commands.
    """

    signer = Account.privateKeyToAccount('0xed765f17c0930ed68ae04a929548f4386d50236903016c0e01e191670543fab7')
    cosigner = Account.privateKeyToAccount('0x989dbcbd23972f521370a8b13462bf915489b24e11a1bb724935a19fff036fb5')

    (wallet, _, _) = fullwallet_deploy(
        accounts[1],
        accounts[1],
        accounts[3]
    )

    # Authorize
    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[signer.address, int(cosigner.address, 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    wallet.functions.invoke0(data).transact({'from': accounts[1]})

    wallet.fallback.transact({'from': signer.address, 'value': w3.toWei(5, 'ether')})

    # invoke0 - can we send eth to 5 accounts and then invoke an account?

    sending_data = []
    prev_balance = []
    for acc in accounts[5:10]:
        sending_data.append((acc, w3.toWei(1, 'ether'), []))
        prev_balance.append(w3.eth.getBalance(acc))

    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[accounts[5], int(cosigner.address, 0)]
    )

    sending_data.append((wallet.address, 0, bytes.fromhex(args_encoded[2:])))

    data = ready_invoke_chain(1, sending_data)

    nonce_signer = wallet.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(wallet, nonce_signer, signer.address, data)
    signed = signer.signHash(operation_data['hash'])

    tx_h = wallet.functions.invoke1CosignerSends(
        signed['v'],   # v
        signed['r'].to_bytes(32, 'big'),    # r
        signed['s'].to_bytes(32, 'big'),    # s
        nonce_signer,                       # nonce
        signer.address,
        data                                # data
    ).transact({'from': cosigner.address})

    # No revert == success?
    tx_success_event = get_logs_for_event(
        wallet.events.InvocationSuccess,
        tx_h.hex()
    )
    tx_auth_event = get_logs_for_event(
        wallet.events.Authorized,
        tx_h.hex()
    )

    assert tx_success_event[0]['args']['result'] == 0, "Result shows revert"
    assert tx_success_event[0]['args']['numOperations'] == 6, "Incorect numOperations"
    assert tx_auth_event[0]['args']['authorizedAddress'] == accounts[5], "Incorrect account authorized"

    for i in range(5, 10):
        assert w3.eth.getBalance(accounts[i]) == prev_balance[i - 5] + w3.toWei(1, 'ether')

    ##############################
    # SignerSends (Same test)
    ##############################

    wallet.fallback.transact({'from': signer.address, 'value': w3.toWei(5, 'ether')})

    # invoke0 - can we send eth to 5 accounts and then invoke an account?

    sending_data = []
    prev_balance = []
    for acc in accounts[10:15]:
        sending_data.append((acc, w3.toWei(1, 'ether'), []))
        prev_balance.append(w3.eth.getBalance(acc))

    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[accounts[7], int(cosigner.address, 0)]
    )

    sending_data.append((wallet.address, 0, bytes.fromhex(args_encoded[2:])))

    data = ready_invoke_chain(1, sending_data)

    nonce_signer = wallet.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(wallet, nonce_signer, signer.address, data)
    signed = cosigner.signHash(operation_data['hash'])

    tx_h = wallet.functions.invoke1SignerSends(
        signed['v'],   # v
        signed['r'].to_bytes(32, 'big'),    # r
        signed['s'].to_bytes(32, 'big'),    # s
        # nonce_signer,                       # nonce
        data                                # data
    ).transact({'from': signer.address})

    # No revert == success?
    tx_success_event = get_logs_for_event(
        wallet.events.InvocationSuccess,
        tx_h.hex()
    )
    tx_auth_event = get_logs_for_event(
        wallet.events.Authorized,
        tx_h.hex()
    )

    assert tx_success_event[0]['args']['result'] == 0, "Result shows revert"
    assert tx_success_event[0]['args']['numOperations'] == 6, "Incorect numOperations"
    assert tx_auth_event[0]['args']['authorizedAddress'] == accounts[7], "Incorrect account authorized"

    for i in range(10, 15):
        assert w3.eth.getBalance(accounts[i]) == prev_balance[i - 10] + w3.toWei(1, 'ether')

def test_invoke2_can_chain(
        fullwallet_deploy,
        assert_tx_failed,
        zero_address,
        accounts,
        invoke_data,
        ready_invoke_chain,
        invoke1_sign_data,
        get_logs_for_event,
        w3):

    """
    Check that invoke1 can chain commands.
    """

    signer = Account.privateKeyToAccount('0xed765f17c0930ed68ae04a929548f4386d50236903016c0e01e191670543fab7')
    cosigner = Account.privateKeyToAccount('0x989dbcbd23972f521370a8b13462bf915489b24e11a1bb724935a19fff036fb5')

    (wallet, _, _) = fullwallet_deploy(
        accounts[1],
        accounts[1],
        accounts[3]
    )

    # Authorize
    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[signer.address, int(cosigner.address, 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    wallet.functions.invoke0(data).transact({'from': accounts[1]})

    wallet.fallback.transact({'from': signer.address, 'value': w3.toWei(5, 'ether')})

    # invoke0 - can we send eth to 5 accounts and then invoke an account?

    sending_data = []
    prev_balance = []
    for acc in accounts[5:10]:
        sending_data.append((acc, w3.toWei(1, 'ether'), []))
        prev_balance.append(w3.eth.getBalance(acc))

    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[accounts[5], int(cosigner.address, 0)]
    )

    sending_data.append((wallet.address, 0, bytes.fromhex(args_encoded[2:])))

    data = ready_invoke_chain(1, sending_data)

    nonce_signer = wallet.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(wallet, nonce_signer, signer.address, data)
    signed = {
        'signer': signer.signHash(operation_data['hash']),
        'cosigner': cosigner.signHash(operation_data['hash'])
    }

    tx_h = wallet.functions.invoke2(
        [signed['signer']['v'], signed['cosigner']['v']],
        [signed['signer']['r'].to_bytes(32, 'big'), signed['cosigner']['r'].to_bytes(32, 'big')],
        [signed['signer']['s'].to_bytes(32, 'big'), signed['cosigner']['s'].to_bytes(32, 'big')],
        nonce_signer,
        signer.address,
        data
    ).transact({'from': accounts[1]})  # Can send from different account

    # No revert == success?
    tx_success_event = get_logs_for_event(
        wallet.events.InvocationSuccess,
        tx_h.hex()
    )
    tx_auth_event = get_logs_for_event(
        wallet.events.Authorized,
        tx_h.hex()
    )

    assert tx_success_event[0]['args']['result'] == 0, "Result shows revert"
    assert tx_success_event[0]['args']['numOperations'] == 6, "Incorect numOperations"
    assert tx_auth_event[0]['args']['authorizedAddress'] == accounts[5], "Incorrect account authorized"

    for i in range(5, 10):
        assert w3.eth.getBalance(accounts[i]) == prev_balance[i - 5] + w3.toWei(1, 'ether')


def test_basic_chaining(
        fullwallet_deploy,
        assert_tx_failed,
        zero_address,
        accounts,
        invoke_data,
        ready_invoke_chain,
        invoke1_sign_data,
        get_logs_for_event,
        w3):
    """
    Test that we can send eth to multiple addresses in one transaction
    """

    # Set up accounts for invoke
    signer = Account.privateKeyToAccount('0xed765f17c0930ed68ae04a929548f4386d50236903016c0e01e191670543fab7')
    cosigner = Account.privateKeyToAccount('0x989dbcbd23972f521370a8b13462bf915489b24e11a1bb724935a19fff036fb5')

    (wallet, _, _) = fullwallet_deploy(
        accounts[1],
        accounts[1],
        accounts[3]
    )

    # Authorize
    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[signer.address, int(cosigner.address, 0)]
    )
    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    wallet.functions.invoke0(data).transact({'from': accounts[1]})
    wallet.fallback.transact({'from': signer.address, 'value': w3.toWei(10, 'ether')})

    wallet_balance = w3.eth.getBalance(wallet.address)

    tuples = [
        (accounts[i], w3.toWei(1, 'ether'), []) for i in range(10, 15)
    ]
    data = ready_invoke_chain(0, tuples)

    nonce_signer = wallet.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(wallet, nonce_signer, signer.address, data)

    signed = cosigner.signHash(operation_data['hash'])
    gas_price = w3.eth.gasPrice

    prev = []
    for i in range(10, 15):
        prev.append(w3.eth.getBalance(accounts[i]))

    signer_prev = w3.eth.getBalance(signer.address)

    tx = wallet.functions.invoke1SignerSends(
        signed['v'],   # v
        signed['r'].to_bytes(32, 'big'),    # r
        signed['s'].to_bytes(32, 'big'),    # s
        # nonce_signer,                       # nonce
        data                                # data
    ).transact({'from': signer.address, 'gasPrice': gas_price})

    tx_receipt = w3.eth.getTransactionReceipt(tx.hex())

    # Check the accounts ALL got transferred
    for i in range(10, 15):
        assert w3.eth.getBalance(accounts[i]) == (prev[i - 10] + w3.toWei(1, 'ether')), "Account not paid"

    # print("BEFORE: {}".format(signer_prev))
    # print("AFTER: {}".format(w3.eth.getBalance(signer.address)))
    # print("MINUS: {}".format(signer_prev - w3.eth.getBalance(signer.address)))
    # print("GASUSED: {}".format(tx_receipt['gasUsed']))
    # print("GASPRICE: {}".format(w3.eth.gasPrice))
    # print("BOTH: {}".format(w3.eth.gasPrice * tx_receipt['gasUsed']))
    # Check that the wallet balance decreases, not just the user.
    events = get_logs_for_event(wallet.events.InvocationSuccess, tx.hex())
    assert events[0]['args']['hash'] == operation_data['hash'], "Operation Hash incorrect"
    assert w3.eth.getBalance(wallet.address) == wallet_balance - (5 * w3.toWei(1, 'ether')), "Wallet balance did not decrease"
    assert w3.eth.getBalance(signer.address) == (signer_prev - (tx_receipt['gasUsed'] * gas_price)), "Signer balance decreased instead of wallet"


def test_chain_authorizing(
        fullwallet_deploy,
        assert_tx_failed,
        zero_address,
        accounts,
        invoke_data,
        ready_invoke_chain,
        invoke1_sign_data,
        get_logs_for_event,
        w3):
    """
    Test that you can chain a number of `authorizeAccount`.
    """

    (wallet, _, _) = fullwallet_deploy(
        accounts[1],
        accounts[1],
        accounts[3]
    )

    # invoke0
    sending_tuples = []
    for i in range(10, 40):
        args_encoded = wallet.encodeABI(
            fn_name='setAuthorized',
            args=[accounts[i], int(accounts[2], 0)]
        )
        sending_tuples.append((wallet.address, 0, bytes.fromhex(args_encoded[2:])))

    for i in range(10, 40):
        assert wallet.functions.authorizations((1 << 160) + int(accounts[i], 0)).call() == 0, "Account already authorized"

    data = ready_invoke_chain(1, sending_tuples)

    tx = wallet.functions.invoke0(data).transact({'from': accounts[1]})
    events = get_logs_for_event(wallet.events.Authorized, tx.hex())
    tx_success = get_logs_for_event(wallet.events.InvocationSuccess, tx.hex())

    for i in range(10, 40):
        assert wallet.functions.authorizations((1 << 160) + int(accounts[i], 0)).call() == int(accounts[2], 0), "Account already authorized"

    assert tx_success[0]['args']['numOperations'] == 30, "Not all operations counted in InvocationSuccess"
    assert len(events) == 30, "Not all events emitted"


def test_chain_and_revert(
        fullwallet_deploy,
        assert_tx_failed,
        zero_address,
        accounts,
        invoke_data,
        ready_invoke_chain,
        invoke1_sign_data,
        get_logs_for_event,
        w3):
    """
    Test that `revert`'s in a chain of commands will act accordingly.
    """

    (wallet, _, _) = fullwallet_deploy(
        accounts[1],
        accounts[1],
        accounts[3]
    )

    # invoke1
    signer = Account.privateKeyToAccount('0xed765f17c0930ed68ae04a929548f4386d50236903016c0e01e191670543fab7')
    cosigner = Account.privateKeyToAccount('0x989dbcbd23972f521370a8b13462bf915489b24e11a1bb724935a19fff036fb5')

    # Authorize
    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[signer.address, int(cosigner.address, 0)]
    )
    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    wallet.functions.invoke0(data).transact({'from': accounts[1]})

    # Give amount to smart contract
    wallet.fallback.transact({'from': signer.address, 'value': w3.toWei(5, 'ether')})

    tuples = [
        (accounts[i], w3.toWei(2, 'ether'), []) for i in range(10, 15)
    ]

    data = ready_invoke_chain(0, tuples)

    nonce_signer = wallet.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(wallet, nonce_signer, signer.address, data)
    signed = cosigner.signHash(operation_data['hash'])

    tx = wallet.functions.invoke1SignerSends(
        signed['v'],   # v
        signed['r'].to_bytes(32, 'big'),    # r
        signed['s'].to_bytes(32, 'big'),    # s
        # nonce_signer,                       # nonce
        data                                # data
    ).transact({'from': signer.address})

    success_event = get_logs_for_event(wallet.events.InvocationSuccess, tx.hex())

    assert success_event[0]['args']['result'] != 0, "Revert not calculated correctly for event"

    # Should throw when we give a 1
    wallet.fallback.transact({'from': signer.address, 'value': w3.toWei(3, 'ether')})

    tuples = [
        (accounts[i], w3.toWei(2, 'ether'), []) for i in range(10, 15)
    ]

    data = ready_invoke_chain(0, tuples)

    nonce_signer = wallet.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(wallet, nonce_signer, signer.address, data)
    signed = cosigner.signHash(operation_data['hash'])

    tx = wallet.functions.invoke1SignerSends(
        signed['v'],   # v
        signed['r'].to_bytes(32, 'big'),    # r
        signed['s'].to_bytes(32, 'big'),    # s
        # nonce_signer,                       # nonce
        data                                # data
    ).transact({'from': signer.address})

    success_event = get_logs_for_event(wallet.events.InvocationSuccess, tx.hex())

    tuples = [
        (accounts[i], w3.toWei(2, 'ether'), []) for i in range(10, 15)
    ]

    data = ready_invoke_chain(1, tuples)
    nonce_signer = wallet.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(wallet, nonce_signer, signer.address, data)
    signed = cosigner.signHash(operation_data['hash'])

    assert_tx_failed(
        wallet.functions.invoke1SignerSends(
            signed['v'],   # v
            signed['r'].to_bytes(32, 'big'),    # r
            signed['s'].to_bytes(32, 'big'),    # s
            # nonce_signer,                       # nonce
            data                                # data
        ),
        {'from': signer.address}
    )

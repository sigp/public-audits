from eth_account import Account

def test_erc20_token_transfer(
        fullwallet_deploy,
        accounts,
        get_logs_for_event,
        erc20_deploy,
        invoke_data,
        invoke1_sign_data,
        ready_invoke_chain,
        w3):
    """
    Receive and Transfer ERC-20 tokens
    """
    signer = Account.privateKeyToAccount('0581fdbce9da7694915eff1d2ae9c2c7efb376a0b153a0b6e75cf7584aeb4a43')
    cosigner = Account.privateKeyToAccount('bb4eefd8877aa7211b9bffff2432af2638ce158cbf74ce1066efc5bf21b64b7f')

    (wallet, _, _) = fullwallet_deploy(
        accounts[1], # Signer
        accounts[1], # Cosigner
        accounts[3]  # Recovery Address
    )
    (token, _) = erc20_deploy()

    # Send Wallet some tokens
    initial_balance = 1000 * 10 ** 18
    token.functions.transfer(wallet.address, initial_balance).transact({'from': accounts[0]})
    assert token.functions.balanceOf(wallet.address).call() == initial_balance, "Wallet has not received tokens"

    # Perform 10 invoke0 ERC20 transfers

    amount = 5 * 10 ** 18
    recipients = accounts[5:15]
    for i in range(10):
        args_encoded = token.encodeABI(
            fn_name='transfer',
            args=[recipients[i], amount]
        )
        data = invoke_data(1, token.address, 0, bytes.fromhex(args_encoded[2:]))
        tx = wallet.functions.invoke0(data).transact({'from': accounts[1]})
        assert token.functions.balanceOf(recipients[i]).call() == amount, "Recipient has not received tokens"

    # Change authorisation to introduce a cosigner:
    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[signer.address, int(cosigner.address, 0)]
    )
    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    tx = wallet.functions.invoke0(data).transact({'from': accounts[1]})


    # Perform 10 invoke1SignerSends ERC20 transfers

    recipients = accounts[16:26]
    for i in range(10):
        args_encoded = token.encodeABI(
            fn_name='transfer',
            args=[recipients[i], amount]
        )
        data = invoke_data(1, token.address, 0, bytes.fromhex(args_encoded[2:]))
        signer_nonce = wallet.functions.nonces(signer.address).call()
        operation_data = invoke1_sign_data(wallet, signer_nonce, signer.address, data)
        signed_data = cosigner.signHash(operation_data['hash'])

        tx = wallet.functions.invoke1SignerSends(
            signed_data['v'],                        # v
            signed_data['r'].to_bytes(32, 'big'),    # r
            signed_data['s'].to_bytes(32, 'big'),    # s
            data  # Data
        ).transact({'from': signer.address})
        assert token.functions.balanceOf(recipients[i]).call() == amount, "Recipient has not received tokens"

    # Perform 10 invoke1CosignerSends

    recipients = accounts[27:37]
    for i in range(10):
        args_encoded = token.encodeABI(
            fn_name='transfer',
            args=[recipients[i], amount]
        )
        data = invoke_data(1, token.address, 0, bytes.fromhex(args_encoded[2:]))
        signer_nonce = wallet.functions.nonces(signer.address).call()
        operation_data = invoke1_sign_data(wallet, signer_nonce, signer.address, data)
        signed_data = signer.signHash(operation_data['hash'])

        tx = wallet.functions.invoke1CosignerSends(
            signed_data['v'],   # v
            signed_data['r'].to_bytes(32, 'big'),   # r
            signed_data['s'].to_bytes(32, 'big'),   # s
            signer_nonce,         # nonce
            signer.address,
            data       # data
        ).transact({'from': cosigner.address})
        assert token.functions.balanceOf(recipients[i]).call() == amount, "Recipient has not received tokens"

    # Perform 10 invoke2

    recipients = accounts[38:48]
    for i in range(10):
        args_encoded = token.encodeABI(
            fn_name='transfer',
            args=[recipients[i], amount]
        )
        data = invoke_data(1, token.address, 0, bytes.fromhex(args_encoded[2:]))
        signer_nonce = wallet.functions.nonces(signer.address).call()
        operation_data = invoke1_sign_data(wallet, signer_nonce, signer.address, data)
        signer_data = signer.signHash(operation_data['hash'])
        cosigner_data = cosigner.signHash(operation_data['hash'])

        tx = wallet.functions.invoke2(
            [signer_data['v'], cosigner_data['v']],       # v
            [signer_data['r'].to_bytes(32, 'big'),          # r0
                cosigner_data['r'].to_bytes(32, 'big')],      # r1
            [signer_data['s'].to_bytes(32, 'big'),          # s0
                cosigner_data['s'].to_bytes(32, 'big')],      # s1
            signer_nonce,                                                  # nonce
            signer.address,
            data  # Data
        ).transact({'from': accounts[20], 'gas': 2000000})

        assert token.functions.balanceOf(recipients[i]).call() == amount, "Recipient has not received tokens"

    # Chain 3 token transfers in the same transaction with an invoke1

    chained_data = []
    for acc in accounts[1:4]:
        args_encoded = token.encodeABI(
            fn_name='transfer',
            args=[acc, amount]
        )
        chained_data.append((token.address, 0, bytes.fromhex(args_encoded[2:])))

    data = ready_invoke_chain(1, chained_data)
    signer_nonce = wallet.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(wallet, signer_nonce, signer.address, data)
    signed_data = cosigner.signHash(operation_data['hash'])

    tx = wallet.functions.invoke1SignerSends(
        signed_data['v'],                        # v
        signed_data['r'].to_bytes(32, 'big'),    # r
        signed_data['s'].to_bytes(32, 'big'),    # s
        data  # Data
    ).transact({'from': signer.address})

    for acc in accounts[1:4]:
        assert token.functions.balanceOf(acc).call() == amount, "Recipient has not received tokens"

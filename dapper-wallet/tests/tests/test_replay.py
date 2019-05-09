from eth_account import Account

# The vulnerability illustrated in this test file (DAP-01) has been closed. Hence, the "malicious" transactions should now revert
# Related transactions have been updated to be expected to revert

def test_replay_cosigner_different(
        fullwallet_deploy,
        accounts,
        assert_tx_failed,
        invoke_data,
        invoke1_sign_data):
    """
    Depicts the scenario where a cosigner's signed transaction can be replayed
    when set to a signer of the same nonce.
    """

    signer = Account.privateKeyToAccount('0xed765f17c0930ed68ae04a929548f4386d50236903016c0e01e191670543fab7')
    cosigner = Account.privateKeyToAccount('0x989dbcbd23972f521370a8b13462bf915489b24e11a1bb724935a19fff036fb5')
    mallory = Account.privateKeyToAccount('0xd211dafb69b3338a8718f4fa92348db10ea293dfe863142762f62741704ca323')

    ##################################################

    # Step 1 make {signer: cosigner} authorized.

    (wallet, _, _) = fullwallet_deploy(
        accounts[1],
        accounts[1],
        accounts[3]
    )

    # Add {signer: cosigner} to `authorized`
    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[signer.address, int(cosigner.address, 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    wallet.functions.invoke0(data).transact({'from': accounts[1]})

    ##################################################

    # Step 2 cosigner signs for a tx to set account[7] as authorized with
    # Mallory.
    #   Note: signer nonce is 0;

    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[accounts[7], int(mallory.address, 0)]
    )

    data_original = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    signer_nonce = wallet.functions.nonces(signer.address).call()
    operation_data_original = invoke1_sign_data(wallet, signer_nonce, signer.address, data_original)
    signed_original = cosigner.signHash(operation_data_original['hash'])

    wallet.functions.invoke1SignerSends(
        signed_original['v'],                        # v
        signed_original['r'].to_bytes(32, 'big'),    # r
        signed_original['s'].to_bytes(32, 'big'),    # s
        data_original                                # Data
    ).transact({'from': signer.address})

    ##################################################

    # Step 3 people see Mallory as malicious, so they want account[7] to change
    # cosigner.

    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[accounts[7], int(cosigner.address, 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    wallet.functions.invoke0(data).transact({'from': accounts[1]})

    assert wallet.functions.authorizations(
        (1 << 160) + int(accounts[7], 0)
    ).call() == int(cosigner.address, 0), "Cosigner not re-set"

    ##################################################

    # Step 4 Mallory wishes to re-gain power over account[7], so gets to be
    #   authorized with cosigner

    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[mallory.address, int(cosigner.address, 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    wallet.functions.invoke0(data).transact({'from': accounts[1]})

    ##################################################

    # Step 5 Mallory replays the cosigned transaction to get control

    assert wallet.functions.authorizations(
        (1 << 160) + int(accounts[7], 0)
    ).call() != int(mallory.address, 0), "Mallory already set"

    assert_tx_failed(wallet.functions.invoke1SignerSends(
        signed_original['v'],                        # v
        signed_original['r'].to_bytes(32, 'big'),    # r
        signed_original['s'].to_bytes(32, 'big'),    # s
        data_original                                # Data
    ), {'from': mallory.address})

    assert wallet.functions.authorizations(
        (1 << 160) + int(accounts[7], 0)
    ).call() == int(cosigner.address, 0), "REPLAY SUCCESSFULL: Mallory re-set"

    assert wallet.functions.authorizations(
        (1 << 160) + int(accounts[7], 0)
    ).call() != int(mallory.address, 0), "REPLAY SUCCESSFULL: Mallory re-set"


def test_replay_cosigner_is_signer(
        fullwallet_deploy,
        accounts,
        invoke_data,
        assert_tx_failed,
        invoke1_sign_data):
    """
    Depicts the scenario where a signer is authorized as both signer and
    cosigner and previous signed information can be replayed through invoke2.
    """

    signer = Account.privateKeyToAccount('0xed765f17c0930ed68ae04a929548f4386d50236903016c0e01e191670543fab7')
    cosigner = Account.privateKeyToAccount('0x989dbcbd23972f521370a8b13462bf915489b24e11a1bb724935a19fff036fb5')
    mallory = Account.privateKeyToAccount('0xd211dafb69b3338a8718f4fa92348db10ea293dfe863142762f62741704ca323')

    ##################################################

    # Step 1 make {signer: cosigner} authorized.

    (wallet, _, _) = fullwallet_deploy(
        accounts[1],
        accounts[1],
        accounts[3]
    )

    # Add {signer: cosigner} to `authorized`
    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[signer.address, int(cosigner.address, 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    wallet.functions.invoke0(data).transact({'from': accounts[1]})

    ##################################################

    # Step 2 cosigner signs for a tx to set account[7] as authorized with
    # Mallory.
    #   Note: signer nonce is 0;

    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[accounts[7], int(mallory.address, 0)]
    )

    data_original = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    signer_nonce = wallet.functions.nonces(signer.address).call()
    operation_data_original = invoke1_sign_data(wallet, signer_nonce, signer.address, data_original)
    signed_original = cosigner.signHash(operation_data_original['hash'])

    wallet.functions.invoke1SignerSends(
        signed_original['v'],                        # v
        signed_original['r'].to_bytes(32, 'big'),    # r
        signed_original['s'].to_bytes(32, 'big'),    # s
        data_original                                # Data
    ).transact({'from': signer.address})

    ##################################################

    # Step 3 people see Mallory as malicious, so they want account[7] to change
    # cosigner.

    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[accounts[7], int(cosigner.address, 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    wallet.functions.invoke0(data).transact({'from': accounts[1]})

    assert wallet.functions.authorizations(
        (1 << 160) + int(accounts[7], 0)
    ).call() == int(cosigner.address, 0), "Cosigner not re-set"

    ##################################################

    # Step 4 cosigner becomes authorized as both signer and cosigner

    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[cosigner.address, int(cosigner.address, 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    wallet.functions.invoke0(data).transact({'from': accounts[1]})

    ##################################################

    # Step 5 Mallory sends the invoke2 to make her re-gain control of ac[7]

    assert wallet.functions.authorizations(
        (1 << 160) + int(accounts[7], 0)
    ).call() != int(mallory.address, 0), "Mallory already set"

    assert_tx_failed(wallet.functions.invoke2(
        [signed_original['v'], signed_original['v']],       # v
        [signed_original['r'].to_bytes(32, 'big'),          # r0
            signed_original['r'].to_bytes(32, 'big')],      # r1
        [signed_original['s'].to_bytes(32, 'big'),          # s0
            signed_original['s'].to_bytes(32, 'big')],      # s1
        0,                                                  # nonce
        cosigner.address,
        data_original                                       # Data
    ), {'from': mallory.address})

    assert wallet.functions.authorizations(
        (1 << 160) + int(accounts[7], 0)
    ).call() == int(cosigner.address, 0), "REPLAY SUCCEEDED: Mallory re-set"

    assert wallet.functions.authorizations(
        (1 << 160) + int(accounts[7], 0)
    ).call() != int(mallory.address, 0), "REPLAY SUCCEEDED: Mallory re-set"


def test_replay_money_send(
        fullwallet_deploy,
        accounts,
        invoke_data,
        invoke1_sign_data,
        assert_tx_failed,
        w3):
    """
    Depicts the scenario where a signer is authorized as both signer and
    cosigner and previous signed information can be replayed through invoke2
    to send eth to an account.
    """

    signer = Account.privateKeyToAccount('0xed765f17c0930ed68ae04a929548f4386d50236903016c0e01e191670543fab7')
    cosigner = Account.privateKeyToAccount('0x989dbcbd23972f521370a8b13462bf915489b24e11a1bb724935a19fff036fb5')
    trent = accounts[11]

    ##################################################

    # Step 1 make {signer: cosigner} authorized.

    (wallet, _, _) = fullwallet_deploy(
        accounts[1],
        accounts[1],
        accounts[3]
    )

    # initial balance as allocated by default by Ganache
    t_balance = w3.eth.getBalance(trent)

    # Add {signer: cosigner} to `authorized`
    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[signer.address, int(cosigner.address, 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    wallet.functions.invoke0(data).transact({'from': accounts[1]})

    # Fund the wallet
    wallet.fallback().transact({'from': cosigner.address, 'value': w3.toWei(10, 'ether')})

    ##################################################

    # Step 2 - send money to Trent

    data_to_replay = invoke_data(1, trent, w3.toWei(1, 'ether'), [])
    signer_nonce = wallet.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(wallet, signer_nonce, signer.address, data_to_replay)
    signed_original = cosigner.signHash(operation_data['hash'])

    wallet.functions.invoke1SignerSends(
        signed_original['v'],                        # v
        signed_original['r'].to_bytes(32, 'big'),    # r
        signed_original['s'].to_bytes(32, 'big'),    # s
        data_to_replay  # Data
    ).transact({'from': signer.address})

    assert w3.eth.getBalance(trent) == (t_balance + int(w3.toWei(1, 'ether'))), "Trents balance not incremented"

    ##################################################

    # Step 3 authorise {cosigner:cosigner}

    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[cosigner.address, int(cosigner.address, 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    wallet.functions.invoke0(data).transact({'from': accounts[1]})

    ##################################################

    # Step 4 - REPLAY

    trent_balance_prev = w3.eth.getBalance(trent)
    gas_price = w3.eth.gasPrice
    assert_tx_failed(wallet.functions.invoke2(
        [signed_original['v'], signed_original['v']],       # v
        [signed_original['r'].to_bytes(32, 'big'),          # r0
            signed_original['r'].to_bytes(32, 'big')],      # r1
        [signed_original['s'].to_bytes(32, 'big'),          # s0
            signed_original['s'].to_bytes(32, 'big')],      # s1
        0,                                                  # nonce
        cosigner.address,
        data_to_replay  # Data
    ), {'from': trent, 'gasPrice': gas_price})

    # Transaction above expected to fail, checks below no longer relevant

    # r_replay = w3.eth.getTransactionReceipt(t_replay.hex())
    # gas_price = w3.eth.gasPrice
    # final_expected = trent_balance_prev + w3.toWei(1, 'ether') - (r_replay['gasUsed']*gas_price)
    # # assert w3.eth.getBalance(trent) == (trent_balance_prev + int(w3.toWei(1, 'ether')) - r_replay['gasUsed']), "Trents balance not incremented"
    # #
    # assert w3.eth.getBalance(trent) == final_expected, "Final balance not as expected"
    # rounding error to fix


def test_can_deplete_wallet(
        fullwallet_deploy,
        accounts,
        invoke_data,
        invoke1_sign_data,
        assert_tx_failed,
        w3):
    """
    Depicts a scenario where an adversary is able to deplete a wallet by authorizing
    new accounts and replaying the message N times.
    """

    signer = Account.privateKeyToAccount('0xed765f17c0930ed68ae04a929548f4386d50236903016c0e01e191670543fab7')
    cosigner = Account.privateKeyToAccount('0x989dbcbd23972f521370a8b13462bf915489b24e11a1bb724935a19fff036fb5')
    adversary = accounts[15]

    ##################################################

    # Step 1 make {signer: cosigner} authorized.

    (wallet, _, _) = fullwallet_deploy(
        accounts[1],
        accounts[1],
        accounts[20]
    )

    # Add {signer: cosigner} to `authorized`
    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[signer.address, int(cosigner.address, 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    wallet.functions.invoke0(data).transact({'from': accounts[1]})

    # Fund the wallet
    wallet.fallback().transact({'from': cosigner.address, 'value': w3.toWei(10, 'ether')})

    ##################################################

    # Step 2 send money

    data_to_replay = invoke_data(0, adversary, w3.toWei(0.5, 'ether'), [])
    signer_nonce = wallet.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(wallet, signer_nonce, signer.address, data_to_replay)
    signed_original = cosigner.signHash(operation_data['hash'])

    wallet.functions.invoke1SignerSends(
        signed_original['v'],                        # v
        signed_original['r'].to_bytes(32, 'big'),    # r
        signed_original['s'].to_bytes(32, 'big'),    # s
        data_to_replay  # Data
    ).transact({'from': signer.address})

    ##################################################

    # Step 3 authorize {adversary:adversary}

    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[
            adversary,
            int(adversary, 0)
        ]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    wallet.functions.invoke0(data).transact({'from': accounts[1]})

    ##################################################

    # Step 4 repeatedly authorize {account[x]:cosigner} and replay!
    account_counter = 21
    print("Starting Replay: Wallet Balance {}".format(w3.eth.getBalance(wallet.address)))
    for account_counter in range(21,35):
    # while w3.eth.getBalance(wallet.address) > 0:
        prev_wallet = w3.eth.getBalance(wallet.address)
        prev_adversary = w3.eth.getBalance(adversary)
        current_account = accounts[account_counter]

        # Authorize Address
        args_encoded = wallet.encodeABI(
            fn_name='setAuthorized',
            args=[
                current_account,
                int(cosigner.address, 0)
            ]
        )

        data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
        wallet.functions.invoke0(data).transact({'from': adversary})

        assert_tx_failed(wallet.functions.invoke1SignerSends(
            signed_original['v'],                        # v
            signed_original['r'].to_bytes(32, 'big'),    # r
            signed_original['s'].to_bytes(32, 'big'),    # s
            data_to_replay  # Data
        ), {'from': current_account})

        assert w3.eth.getBalance(wallet.address) == prev_wallet, "Wallet balance decrementing"
        print("[Round: {}] Adversary Balance: {}, Wallet_Balance: {}".format(
            account_counter - 12,
            w3.eth.getBalance(adversary),
            w3.eth.getBalance(wallet.address)
        ))
        account_counter += 1

    assert w3.eth.getBalance(wallet.address) != 0, "Wallet depleted"

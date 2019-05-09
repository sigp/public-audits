from eth_account import Account

def test_gas_costs(
        walletfactory_deploy,
        fullwallet_deploy,
        accounts,
        zero_address,
        get_logs_for_event,
        invoke_data,
        invoke1_sign_data,
        erc20_deploy,
        erc223_deploy,
        erc721_mock_deploy,
        ready_invoke_chain,
        w3):

    signer = Account.privateKeyToAccount('0xed765f17c0930ed68ae04a929548f4386d50236903016c0e01e191670543fab7')
    cosigner = Account.privateKeyToAccount('0x989dbcbd23972f521370a8b13462bf915489b24e11a1bb724935a19fff036fb5')
    mallory = Account.privateKeyToAccount('0xd211dafb69b3338a8718f4fa92348db10ea293dfe863142762f62741704ca323')
    recipient = accounts[11]

    (cloneable, cloneable_r, factory, factory_r) = walletfactory_deploy()
    (fullwallet, fullwallet_r,  _) = fullwallet_deploy(accounts[1], accounts[1], accounts[3])

    # Factory Deploy Cloned Wallet
    tx = factory.functions.deployCloneWallet(
        accounts[1],        # RecoveryAddress
        accounts[2],        # AuthorizedAddress
        int(accounts[2],0), # CoSigner
    ).transact({'from': accounts[0]})

    event = get_logs_for_event(factory.events.WalletCreated, tx)[0]['args']

    cloned = w3.eth.contract(
        address=event['wallet'],
        abi=cloneable.abi
    )

    cloned_r = w3.eth.getTransactionReceipt(tx.hex())

    print("\n\nGas used to deploy CloneableWallet: {}".format(cloneable_r['gasUsed']))
    print("Gas used to deploy WalletFactory: {}".format(factory_r['gasUsed']))
    print("Gas used to deploy FullWallet: {}".format(fullwallet_r['gasUsed']))
    print("Gas used to deploy Cloned Wallet: {}".format(cloned_r['gasUsed']))

    # Fund wallets:
    print("\nFunding wallets...")
    fullwallet.fallback().transact({'from': accounts[0], 'value': w3.toWei(10, 'ether')})
    cloned.fallback().transact({'from': accounts[0], 'value': w3.toWei(10, 'ether')})

    # Let's figure out the cost of an invoke0 (setAuthorized)
    # Step A: setAuthorized
    print("\nGas cost for invoke 0:")
    print("\nStep A - `setAuthorized`:")
    args_encoded = fullwallet.encodeABI(
        fn_name='setAuthorized',
        args=[signer.address, int(signer.address, 0)]
    )

    args_encoded2 = cloned.encodeABI(
        fn_name='setAuthorized',
        args=[signer.address, int(signer.address, 0)]
    )
    data = invoke_data(1, fullwallet.address, 0, bytes.fromhex(args_encoded[2:]))
    tx = fullwallet.functions.invoke0(data).transact({'from': accounts[1]})
    invoke0full_r = w3.eth.getTransactionReceipt(tx.hex())

    data2 = invoke_data(1, cloned.address, 0, bytes.fromhex(args_encoded2[2:]))
    tx2 = cloned.functions.invoke0(data2).transact({'from': accounts[2]})
    invoke0cloned_r = w3.eth.getTransactionReceipt(tx2.hex())


    print("\n\nGas used to call `setAuthorized` via invoke0 on Full Wallet: {}".format(invoke0full_r['gasUsed']))
    print("Gas used to call `setAuthorized` via invoke0 on Cloned Wallet: {}".format(invoke0cloned_r['gasUsed']))

    # Step B: send Eth
    print("\nStep B - `send ETH`:")

    data3 = invoke_data(1, recipient, w3.toWei(1, 'ether'), [])
    tx = fullwallet.functions.invoke0(data3).transact({'from': signer.address})
    invoke0full_r2 = w3.eth.getTransactionReceipt(tx.hex())

    print("Gas used to call `ETH transfer` via invoke0 on Full Wallet: {}".format(invoke0full_r2['gasUsed']))

    tx = cloned.functions.invoke0(data3).transact({'from': signer.address})
    invoke0cloned_r2 = w3.eth.getTransactionReceipt(tx.hex())
    print("Gas used to call `ETH transfer` via invoke0 on Cloned Wallet: {}".format(invoke0cloned_r2['gasUsed']))

    # Let's figure out gas costs via invoke1*
    # Step A: 'setAuthorized'
    print("\nGas cost for invoke 1:")

    print("\nStep A - `setAuthorized`:")

    signer_nonce = fullwallet.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(fullwallet, signer_nonce, signer.address, data)
    signed_data = signer.signHash(operation_data['hash'])
    # tx = fullwallet.functions.invoke0(data).transact({'from': signer.address})
    tx = fullwallet.functions.invoke1SignerSends(
        signed_data['v'],                        # v
        signed_data['r'].to_bytes(32, 'big'),    # r
        signed_data['s'].to_bytes(32, 'big'),    # s
        data  # Data
    ).transact({'from': signer.address})
    invoke1full_r = w3.eth.getTransactionReceipt(tx.hex())
    print("Gas used to call `setAuthorized` via invoke1 on Full Wallet: {}".format(invoke1full_r['gasUsed']))

    signer_nonce = cloned.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(cloned, signer_nonce, signer.address, data2)
    signed_data2 = signer.signHash(operation_data['hash'])
    # tx = cloned.functions.invoke0(data2).transact({'from': signer.address})
    tx = cloned.functions.invoke1SignerSends(
        signed_data2['v'],                        # v
        signed_data2['r'].to_bytes(32, 'big'),    # r
        signed_data2['s'].to_bytes(32, 'big'),    # s
        data2  # Data
    ).transact({'from': signer.address})
    invoke1cloned_r = w3.eth.getTransactionReceipt(tx.hex())
    print("Gas used to call `setAuthorized` via invoke1 on Cloned Wallet: {}".format(invoke1cloned_r['gasUsed']))

    # Step B: 'ETH Transfer'
    print("\nStep B - `transfer ETH`:")

    signer_nonce = fullwallet.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(fullwallet, signer_nonce, signer.address, data3)
    signed_data4 = cosigner.signHash(operation_data['hash'])
    # tx = fullwallet.functions.invoke0(data3).transact({'from': signer.address})
    tx = fullwallet.functions.invoke1SignerSends(
        signed_data4['v'],                        # v
        signed_data4['r'].to_bytes(32, 'big'),    # r
        signed_data4['s'].to_bytes(32, 'big'),    # s
        data3  # Data
    ).transact({'from': signer.address})
    invoke1full_send_r = w3.eth.getTransactionReceipt(tx.hex())
    print("Gas used to send ETH via invoke1 on Full Wallet: {}".format(invoke1full_send_r['gasUsed']))

    signer_nonce = cloned.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(cloned, signer_nonce, signer.address, data3)
    signed_data5 = cosigner.signHash(operation_data['hash'])
    # tx = fullwallet.functions.invoke0(data3).transact({'from': signer.address})
    tx = cloned.functions.invoke1SignerSends(
        signed_data5['v'],                        # v
        signed_data5['r'].to_bytes(32, 'big'),    # r
        signed_data5['s'].to_bytes(32, 'big'),    # s
        data3  # Data
    ).transact({'from': signer.address})
    invoke1cloned_send_r = w3.eth.getTransactionReceipt(tx.hex())
    print("Gas used to send ETH via invoke1 on Cloned Wallet: {}".format(invoke1cloned_send_r['gasUsed']))

    # Let's figure out gas costs for invoke2
    # Step A: setAuthorized

    print("\nGas cost for invoke 2:")
    signer_nonce = fullwallet.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(fullwallet, signer_nonce, signer.address, data)
    signed_data = signer.signHash(operation_data['hash'])

    tx = fullwallet.functions.invoke2(
        [signed_data['v'], signed_data['v']],       # v
        [signed_data['r'].to_bytes(32, 'big'),          # r0
            signed_data['r'].to_bytes(32, 'big')],      # r1
        [signed_data['s'].to_bytes(32, 'big'),          # s0
            signed_data['s'].to_bytes(32, 'big')],      # s1
        signer_nonce,                                                  # nonce
        signer.address,
        data  # Data
    ).transact({'from': accounts[20], 'gas': 2000000})

    invoke2full_r = w3.eth.getTransactionReceipt(tx.hex())
    print("Gas used to call `setAuthorized` via invoke2 on Full Wallet: {}".format(invoke2full_r['gasUsed']))

    signer_nonce = cloned.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(cloned, signer_nonce, signer.address, data2)
    signed_data = signer.signHash(operation_data['hash'])

    tx = cloned.functions.invoke2(
        [signed_data['v'], signed_data['v']],       # v
        [signed_data['r'].to_bytes(32, 'big'),          # r0
            signed_data['r'].to_bytes(32, 'big')],      # r1
        [signed_data['s'].to_bytes(32, 'big'),          # s0
            signed_data['s'].to_bytes(32, 'big')],      # s1
        signer_nonce,                                                  # nonce
        signer.address,
        data2  # Data
    ).transact({'from': accounts[20], 'gas': 2000000})

    invoke2cloned_r = w3.eth.getTransactionReceipt(tx.hex())
    print("Gas used to call `setAuthorized` via invoke2 on Cloned Wallet: {}".format(invoke2cloned_r['gasUsed']))

    # Step B: send ETH
    # Full wallet
    signer_nonce = fullwallet.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(fullwallet, signer_nonce, signer.address, data3)
    signed_data = signer.signHash(operation_data['hash'])

    tx = fullwallet.functions.invoke2(
        [signed_data['v'], signed_data['v']],       # v
        [signed_data['r'].to_bytes(32, 'big'),          # r0
            signed_data['r'].to_bytes(32, 'big')],      # r1
        [signed_data['s'].to_bytes(32, 'big'),          # s0
            signed_data['s'].to_bytes(32, 'big')],      # s1
        signer_nonce,                                                  # nonce
        signer.address,
        data3  # Data
    ).transact({'from': accounts[20], 'gas': 2000000})

    invoke2full_send_r = w3.eth.getTransactionReceipt(tx.hex())
    print("Gas used to send ETH via invoke2 on Full Wallet: {}".format(invoke2full_send_r['gasUsed']))

    # Cloned wallet
    signer_nonce = cloned.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(cloned, signer_nonce, signer.address, data3)
    signed_data = signer.signHash(operation_data['hash'])

    tx = cloned.functions.invoke2(
        [signed_data['v'], signed_data['v']],       # v
        [signed_data['r'].to_bytes(32, 'big'),          # r0
            signed_data['r'].to_bytes(32, 'big')],      # r1
        [signed_data['s'].to_bytes(32, 'big'),          # s0
            signed_data['s'].to_bytes(32, 'big')],      # s1
        signer_nonce,                                                  # nonce
        signer.address,
        data3  # Data
    ).transact({'from': accounts[20], 'gas': 2000000})

    invoke2cloned_send_r = w3.eth.getTransactionReceipt(tx.hex())
    print("Gas used to send ETH via invoke2 on Cloned Wallet: {}".format(invoke2cloned_send_r['gasUsed']))

    # Token transfers!
    print("\n\nToken transfer benchmark\n")
    # Transfer ERC20 token with invoke0
    # Full wallet:

    (erc20, _) = erc20_deploy()
    (erc223,_) = erc223_deploy()

    # Send wallets some tokens
    initial_balance = 1000 * 10 ** 18
    erc20.functions.transfer(cloned.address, initial_balance).transact({'from': accounts[0]})
    erc20.functions.transfer(fullwallet.address, initial_balance).transact({'from': accounts[0]})

    erc223.functions.transfer(cloned.address, initial_balance).transact({'from': accounts[0]})
    erc223.functions.transfer(fullwallet.address, initial_balance).transact({'from': accounts[0]})

    assert erc20.functions.balanceOf(cloned.address).call() == initial_balance, "Wallet has not received tokens"
    assert erc223.functions.balanceOf(fullwallet.address).call() == initial_balance, "Wallet has not received tokens"

    # Perform 1 invoke0 ERC20 transfer on a Full Wallet and a Cloned Wallet

    amount = 5 * 10 ** 18
    recipient = accounts[5]
    args_erc20 = erc20.encodeABI(
            fn_name='transfer',
            args=[recipient, amount]
    )
    data_erc20 = invoke_data(1, erc20.address, 0, bytes.fromhex(args_erc20[2:]))

    # Full Wallet

    tx = fullwallet.functions.invoke0(data_erc20).transact({'from': signer.address})
    assert erc20.functions.balanceOf(recipient).call() == amount, "Recipient has not received tokens"
    invoke0_erc20_c = w3.eth.getTransactionReceipt(tx.hex())
    print("Gas used to send ERC20 via invoke0 on Full Wallet: {}".format(invoke0_erc20_c['gasUsed']))

    # Cloned Wallet

    tx = cloned.functions.invoke0(data_erc20).transact({'from': signer.address})
    assert erc20.functions.balanceOf(recipient).call() == 2*amount, "Recipient has not received tokens"
    invoke0_erc20_f = w3.eth.getTransactionReceipt(tx.hex())
    print("Gas used to send ERC20 via invoke0 on Cloned Wallet: {}".format(invoke0_erc20_f['gasUsed']))

    # Perform 1 invoke0 ERC223 safeTransferFrom on a Full Wallet and a Cloned Wallet

    amount = 5 * 10 ** 18
    args_erc223 = erc223.encodeABI(
        fn_name='transfer',
        args=[recipient, amount]
    )
    data_erc223 = invoke_data(1, erc223.address, 0, bytes.fromhex(args_erc223[2:]))

    # Full Wallet

    tx = fullwallet.functions.invoke0(data_erc223).transact({'from': signer.address})
    assert erc223.functions.balanceOf(recipient).call() == amount, "Recipient has not received tokens"
    invoke0_erc223_c = w3.eth.getTransactionReceipt(tx.hex())
    print("Gas used to send ERC223 via invoke0 on Full Wallet: {}".format(invoke0_erc223_c['gasUsed']))

    # Cloned Wallet

    tx = cloned.functions.invoke0(data_erc223).transact({'from': signer.address})
    assert erc223.functions.balanceOf(recipient).call() == 2*amount, "Recipient has not received tokens"
    invoke0_erc223_f = w3.eth.getTransactionReceipt(tx.hex())
    print("Gas used to send ERC223 via invoke0 on Cloned Wallet: {}".format(invoke0_erc223_f['gasUsed']))

    # Transfer ERC20 with invoke1


    signer_nonce = fullwallet.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(fullwallet, signer_nonce, signer.address, data_erc20)
    signed_data_erc20 = cosigner.signHash(operation_data['hash'])
    tx = fullwallet.functions.invoke1SignerSends(
        signed_data4['v'],                        # v
        signed_data4['r'].to_bytes(32, 'big'),    # r
        signed_data4['s'].to_bytes(32, 'big'),    # s
        data_erc20  # Data
    ).transact({'from': signer.address})
    invoke1_erc20_f = w3.eth.getTransactionReceipt(tx.hex())
    print("Gas used to send ERC20 via invoke1 on Full Wallet: {}".format(invoke1_erc20_f['gasUsed']))

    signer_nonce = cloned.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(cloned, signer_nonce, signer.address, data_erc20)
    signed_data_erc20 = cosigner.signHash(operation_data['hash'])
    tx = cloned.functions.invoke1SignerSends(
        signed_data5['v'],                        # v
        signed_data5['r'].to_bytes(32, 'big'),    # r
        signed_data5['s'].to_bytes(32, 'big'),    # s
        data3  # Data
    ).transact({'from': signer.address})
    invoke1_erc20_c = w3.eth.getTransactionReceipt(tx.hex())
    print("Gas used to send ERC20 via invoke1 on Cloned Wallet: {}".format(invoke1_erc20_c['gasUsed']))

    # Transfer ERC223 with invoke1
    signer_nonce = fullwallet.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(fullwallet, signer_nonce, signer.address, data_erc223)
    signed_data_erc223 = cosigner.signHash(operation_data['hash'])
    tx = fullwallet.functions.invoke1SignerSends(
        signed_data4['v'],                        # v
        signed_data4['r'].to_bytes(32, 'big'),    # r
        signed_data4['s'].to_bytes(32, 'big'),    # s
        data_erc223  # Data
    ).transact({'from': signer.address})
    invoke1_erc223_f = w3.eth.getTransactionReceipt(tx.hex())
    print("\nGas used to send ERC223 via invoke1 on Full Wallet: {}".format(invoke1_erc223_f['gasUsed']))

    signer_nonce = cloned.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(cloned, signer_nonce, signer.address, data_erc223)
    signed_data_erc223 = cosigner.signHash(operation_data['hash'])
    # tx = fullwallet.functions.invoke0(data3).transact({'from': signer.address})
    tx = cloned.functions.invoke1SignerSends(
        signed_data4['v'],                        # v
        signed_data4['r'].to_bytes(32, 'big'),    # r
        signed_data4['s'].to_bytes(32, 'big'),    # s
        data_erc223  # Data
    ).transact({'from': signer.address})
    invoke1_erc223_c = w3.eth.getTransactionReceipt(tx.hex())
    print("Gas used to send ERC223 via invoke1 on Cloned Wallet: {}".format(invoke1_erc223_c['gasUsed']))

    # Transfer ERC20 and ERC223 via invoke2

    ## ERC20
    # Full
    signer_nonce = fullwallet.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(fullwallet, signer_nonce, signer.address, data_erc20)
    signed_data_erc20 = signer.signHash(operation_data['hash'])
    tx = fullwallet.functions.invoke2(
        [signed_data_erc20['v'], signed_data_erc20['v']],       # v
        [signed_data_erc20['r'].to_bytes(32, 'big'),          # r0
            signed_data_erc20['r'].to_bytes(32, 'big')],      # r1
        [signed_data_erc20['s'].to_bytes(32, 'big'),          # s0
            signed_data_erc20['s'].to_bytes(32, 'big')],      # s1
        signer_nonce,                                                  # nonce
        signer.address,
        data_erc20  # Data
    ).transact({'from': signer.address, 'gas': 1000000})
    invoke2_erc20_f = w3.eth.getTransactionReceipt(tx.hex())
    print("\nGas used to send ERC20 via invoke2 on Full Wallet: {}".format(invoke2_erc20_f['gasUsed']))


    # Cloned
    signer_nonce = cloned.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(cloned, signer_nonce, signer.address, data_erc20)
    signed_data_erc20 = signer.signHash(operation_data['hash'])

    tx = cloned.functions.invoke2(
        [signed_data_erc20['v'], signed_data_erc20['v']],       # v
        [signed_data_erc20['r'].to_bytes(32, 'big'),          # r0
            signed_data_erc20['r'].to_bytes(32, 'big')],      # r1
        [signed_data_erc20['s'].to_bytes(32, 'big'),          # s0
            signed_data_erc20['s'].to_bytes(32, 'big')],      # s1
        signer_nonce,                                                  # nonce
        signer.address,
        data_erc20  # Data
    ).transact({'from': signer.address, 'gas': 1000000})
    invoke2_erc20_c = w3.eth.getTransactionReceipt(tx.hex())
    print("Gas used to send ERC20 via invoke2 on Cloned Wallet: {}".format(invoke2_erc20_c['gasUsed']))



    ## ERC223
    # Full
    signer_nonce = fullwallet.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(fullwallet, signer_nonce, signer.address, data_erc223)
    signed_data_erc223 = signer.signHash(operation_data['hash'])
    tx = fullwallet.functions.invoke2(
        [signed_data_erc223['v'], signed_data_erc223['v']],       # v
        [signed_data_erc223['r'].to_bytes(32, 'big'),          # r0
            signed_data_erc223['r'].to_bytes(32, 'big')],      # r1
        [signed_data_erc223['s'].to_bytes(32, 'big'),          # s0
            signed_data_erc223['s'].to_bytes(32, 'big')],      # s1
        signer_nonce,                                                  # nonce
        signer.address,
        data_erc223  # Data
    ).transact({'from': signer.address, 'gas': 1000000})
    invoke2_erc223_f = w3.eth.getTransactionReceipt(tx.hex())
    print("\nGas used to send ERC223 via invoke2 on Full Wallet: {}".format(invoke2_erc223_f['gasUsed']))


    # Cloned
    signer_nonce = cloned.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(cloned, signer_nonce, signer.address, data_erc223)
    signed_data_erc223 = signer.signHash(operation_data['hash'])

    tx = cloned.functions.invoke2(
        [signed_data_erc223['v'], signed_data_erc223['v']],       # v
        [signed_data_erc223['r'].to_bytes(32, 'big'),          # r0
            signed_data_erc223['r'].to_bytes(32, 'big')],      # r1
        [signed_data_erc223['s'].to_bytes(32, 'big'),          # s0
            signed_data_erc223['s'].to_bytes(32, 'big')],      # s1
        signer_nonce,                                                  # nonce
        signer.address,
        data_erc223  # Data
    ).transact({'from': signer.address, 'gas': 1000000})
    invoke2_erc223_c = w3.eth.getTransactionReceipt(tx.hex())
    print("Gas used to send ERC223 via invoke2 on Cloned Wallet: {}".format(invoke2_erc223_c['gasUsed']))



    # Test ERC721 token transfer. Note that we're using the ERC721TokenMock contract, which not compliant with ERC721 (see vulnerability DAP-02) for the purpose of this benchmark.

    (nft_c, _) = erc721_mock_deploy()
    # For invoke0
    nft_c.functions.mint(accounts[2], 1337).transact({'from': accounts[0]})
    nft_c.functions.mint(accounts[2], 13371337).transact({'from': accounts[0]})
    nft_c.functions.safeTransferFrom(accounts[2], fullwallet.address, 1337).transact({'from': accounts[2]})
    nft_c.functions.safeTransferFrom(accounts[2], cloned.address, 13371337).transact({'from': accounts[2]})

    # For invoke1
    nft_c.functions.mint(accounts[2], 11337).transact({'from': accounts[0]})
    nft_c.functions.mint(accounts[2], 113371337).transact({'from': accounts[0]})
    nft_c.functions.safeTransferFrom(accounts[2], fullwallet.address, 11337).transact({'from': accounts[2]})
    nft_c.functions.safeTransferFrom(accounts[2], cloned.address, 113371337).transact({'from': accounts[2]})

    # For invoke2
    nft_c.functions.mint(accounts[2], 21337).transact({'from': accounts[0]})
    nft_c.functions.mint(accounts[2], 213371337).transact({'from': accounts[0]})
    nft_c.functions.safeTransferFrom(accounts[2], fullwallet.address, 21337).transact({'from': accounts[2]})
    nft_c.functions.safeTransferFrom(accounts[2], cloned.address, 213371337).transact({'from': accounts[2]})

    # Transfer via invoke0

    # Full wallet

    args_erc721_f = nft_c.encodeABI(
        fn_name='safeTransferFrom',
        args=[fullwallet.address, accounts[5], 1337]
    )
    data_erc721_f = invoke_data(1, nft_c.address, 0, bytes.fromhex(args_erc721_f[2:]))
    tx = fullwallet.functions.invoke0(data_erc721_f).transact({'from': signer.address})
    invoke0_erc721_f = w3.eth.getTransactionReceipt(tx.hex())
    print("Gas used to send ERC721 via invoke0 on Full Wallet: {}".format(invoke0_erc721_f['gasUsed']))

    # Cloned wallet

    args_erc721_c = nft_c.encodeABI(
        fn_name='safeTransferFrom',
        args=[cloned.address, accounts[5], 13371337]
    )
    data_erc721_c = invoke_data(1, nft_c.address, 0, bytes.fromhex(args_erc721_c[2:]))
    tx = cloned.functions.invoke0(data_erc721_c).transact({'from': signer.address})
    invoke0_erc721_c = w3.eth.getTransactionReceipt(tx.hex())
    print("Gas used to send ERC721 via invoke0 on Cloned Wallet: {}".format(invoke0_erc721_c['gasUsed']))

    # Transfer via invoke1

    # Full wallet

    args_erc721_f = nft_c.encodeABI(
        fn_name='safeTransferFrom',
        args=[fullwallet.address, accounts[5], 11337]
    )
    data_erc721_f = invoke_data(1, nft_c.address, 0, bytes.fromhex(args_erc721_f[2:]))

    signer_nonce = fullwallet.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(fullwallet, signer_nonce, signer.address, data_erc721_f)
    signed_data_erc721 = cosigner.signHash(operation_data['hash'])
    tx = fullwallet.functions.invoke1SignerSends(
        signed_data_erc721['v'],                        # v
        signed_data_erc721['r'].to_bytes(32, 'big'),    # r
        signed_data_erc721['s'].to_bytes(32, 'big'),    # s
        data_erc721_f  # Data
    ).transact({'from': signer.address})
    invoke1_erc721_f = w3.eth.getTransactionReceipt(tx.hex())
    print("\nGas used to send ERC721 via invoke1 on Full Wallet: {}".format(invoke1_erc721_f['gasUsed']))

    # Cloned wallet

    assert nft_c.functions.ownerOf(113371337).call() == cloned.address,  "Contract doest have the right asset"

    args_erc721_c = nft_c.encodeABI(
        fn_name='safeTransferFrom',
        args=[cloned.address, accounts[5], 113371337]
    )
    data_erc721_c = invoke_data(1, nft_c.address, 0, bytes.fromhex(args_erc721_c[2:]))

    signer_nonce = cloned.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(cloned, signer_nonce, signer.address, data_erc721_c)
    signed_data_erc721_c = cosigner.signHash(operation_data['hash'])
    tx = cloned.functions.invoke1SignerSends(
        signed_data_erc721_c['v'],                        # v
        signed_data_erc721_c['r'].to_bytes(32, 'big'),    # r
        signed_data_erc721_c['s'].to_bytes(32, 'big'),    # s
        data_erc721_c  # Data
    ).transact({'from': signer.address, 'gas':1000000})
    invoke1_erc721_c = w3.eth.getTransactionReceipt(tx.hex())
    print("\nGas used to send ERC721 via invoke1 on Cloned Wallet: {}".format(invoke1_erc721_c['gasUsed']))

    # Invoke 2 - change Authorisations to make sure we have an actual cosigner for both wallets:
    args_encoded = fullwallet.encodeABI(
        fn_name='setAuthorized',
        args=[signer.address, int(cosigner.address, 0)]
    )

    args_encoded2 = cloned.encodeABI(
        fn_name='setAuthorized',
        args=[signer.address, int(cosigner.address, 0)]
    )
    data = invoke_data(1, fullwallet.address, 0, bytes.fromhex(args_encoded[2:]))
    tx = fullwallet.functions.invoke0(data).transact({'from': signer.address})

    data2 = invoke_data(1, cloned.address, 0, bytes.fromhex(args_encoded2[2:]))
    tx2 = cloned.functions.invoke0(data2).transact({'from': signer.address})

    auth_version = 1<<160
    assert fullwallet.functions.authorizations(auth_version + int(signer.address, 0)).call() == int(cosigner.address, 0), "Wrong cosigner for full wallet"
    assert cloned.functions.authorizations(auth_version + int(signer.address, 0)).call() == int(cosigner.address, 0), "Wrong cosigner for cloned wallet"

    # Full wallet

    args_erc721_f = nft_c.encodeABI(
        fn_name='safeTransferFrom',
        args=[fullwallet.address, accounts[5], 21337]
    )
    data_erc721_f = invoke_data(1, nft_c.address, 0, bytes.fromhex(args_erc721_f[2:]))
    signer_nonce = fullwallet.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(fullwallet, signer_nonce, signer.address, data_erc721_f)
    signed_data_signer = signer.signHash(operation_data['hash'])
    signed_data_cosigner = cosigner.signHash(operation_data['hash'])

    tx = fullwallet.functions.invoke2(
        [signed_data_signer['v'], signed_data_cosigner['v']],       # v
        [signed_data_signer['r'].to_bytes(32, 'big'),          # r0
            signed_data_cosigner['r'].to_bytes(32, 'big')],      # r1
        [signed_data_signer['s'].to_bytes(32, 'big'),          # s0
            signed_data_cosigner['s'].to_bytes(32, 'big')],      # s1
        signer_nonce,                                                  # nonce
        signer.address,
        data_erc721_f  # Data
    ).transact({'from': signer.address, 'gas': 1000000})

    invoke2erc721_f = w3.eth.getTransactionReceipt(tx.hex())
    print("\nGas used to send ERC721 via invoke2 on Full Wallet: {}".format(invoke2erc721_f['gasUsed']))

    # Cloned wallet
    args_erc721_c = nft_c.encodeABI(
        fn_name='safeTransferFrom',
        args=[cloned.address, accounts[5], 213371337]
    )
    data_erc721_c = invoke_data(1, nft_c.address, 0, bytes.fromhex(args_erc721_c[2:]))
    signer_nonce = cloned.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(cloned, signer_nonce, signer.address, data_erc721_c)
    signed_data_signer = signer.signHash(operation_data['hash'])
    signed_data_cosigner = cosigner.signHash(operation_data['hash'])

    tx = cloned.functions.invoke2(
        [signed_data_signer['v'], signed_data_cosigner['v']],       # v
        [signed_data_signer['r'].to_bytes(32, 'big'),          # r0
            signed_data_cosigner['r'].to_bytes(32, 'big')],      # r1
        [signed_data_signer['s'].to_bytes(32, 'big'),          # s0
            signed_data_cosigner['s'].to_bytes(32, 'big')],      # s1
        signer_nonce,                                                  # nonce
        signer.address,
        data_erc721_c  # Data
    ).transact({'from': signer.address, 'gas': 1000000})

    invoke2erc721_c = w3.eth.getTransactionReceipt(tx.hex())
    print("\nGas used to send ERC721 via invoke2 on Cloned Wallet: {}".format(invoke2erc721_c['gasUsed']))

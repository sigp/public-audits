from eth_account import Account

Signer = Account()


# these tests were used trying to chase a bug relating to who sent the authorisation, and mirror some of the scenarios
# in the big 'test_various_transfers' test

def _common_setup_code(fullwallet_deploy, accounts, invoke_data):
    full_wallet, fw_rcpt, fw_accounts = fullwallet_deploy()

    a_addr = accounts[4]
    new_cosigner_addr = a_addr
    random_addr = accounts[5]
    b_addr = accounts[6]

    # Let's try some common modifications

    # First do recovery to random without cosigner
    full_wallet.functions.emergencyRecovery(random_addr, int(random_addr, 0)).transact({'from': fw_accounts['recovery']})

    # Then set A as authorized (without cosign
    args_encoded = full_wallet.encodeABI(
        fn_name='setAuthorized',
        args=[a_addr, int(a_addr, 0)]
    )
    authorized_data = invoke_data(1, full_wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    full_wallet.functions.invoke0(authorized_data).transact({'from': random_addr})

    # Then  set Random to have A as cosigner
    # We call thrice.
    args_encoded = full_wallet.encodeABI(
        fn_name='setAuthorized',
        args=[random_addr, int(a_addr, 0)]
    )
    authorized_data = invoke_data(1, full_wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    full_wallet.functions.invoke0(authorized_data).transact({'from': random_addr})
    full_wallet.functions.invoke0(authorized_data).transact({'from': a_addr})
    full_wallet.functions.invoke0(authorized_data).transact({'from': a_addr})

    # Now we do recovery again, but setting 'b' as signer (without cosigner)
    full_wallet.functions.emergencyRecovery(b_addr, int(b_addr, 0)).transact({'from': fw_accounts['recovery']})

    # And now we set the recoveryAddress to what it already was.
    args_encoded = full_wallet.encodeABI(
        fn_name='setRecoveryAddress',
        args=[fw_accounts['recovery']]
    )
    authorized_data = invoke_data(1, full_wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    full_wallet.functions.invoke0(authorized_data).transact({'from': b_addr})

    # Then finally do another recovery
    full_wallet.functions.emergencyRecovery(random_addr, int(b_addr, 0)).transact({'from': fw_accounts['recovery']})

    # Now we get ready for the set authorization

    args_encoded = full_wallet.encodeABI(
        fn_name='setAuthorized',
        args=[fw_accounts['authorized'], int(new_cosigner_addr, 0)]
    )
    i_data = invoke_data(1, full_wallet.address, 0, bytes.fromhex(args_encoded[2:]))

    authed_accounts = {
        'signer': random_addr,
        'cosigner': b_addr
    }

    return full_wallet, authed_accounts, i_data


def test_set_authorized_from_signer(
        fullwallet_deploy,
        accounts,
        invoke_data,
        invoke1_sign_data,
        accounts_private_keys):

    full_wallet, authed_accounts, i_data = _common_setup_code(fullwallet_deploy, accounts, invoke_data)

    cosigner_nonce = full_wallet.functions.nonces(authed_accounts['cosigner']).call()
    data_to_sign = invoke1_sign_data(full_wallet, cosigner_nonce, authed_accounts['signer'], i_data)
    signed_data = Signer.signHash(data_to_sign['hash'], accounts_private_keys[authed_accounts['cosigner'].lower()])
    full_wallet.functions.invoke1SignerSends(
            signed_data['v'],
            signed_data['r'].to_bytes(32, 'big'),
            signed_data['s'].to_bytes(32, 'big'),
            i_data
        ).transact({'from': authed_accounts['signer']})


def test_set_authorized_from_cosigner(
        fullwallet_deploy,
        accounts,
        invoke_data,
        invoke1_sign_data,
        accounts_private_keys):

    full_wallet, authed_accounts, i_data = _common_setup_code(fullwallet_deploy, accounts, invoke_data)

    signer_nonce = full_wallet.functions.nonces(authed_accounts['signer']).call()
    data_to_sign = invoke1_sign_data(full_wallet, signer_nonce, authed_accounts['signer'], i_data)
    signed_data = Signer.signHash(data_to_sign['hash'], accounts_private_keys[authed_accounts['signer'].lower()])
    full_wallet.functions.invoke1CosignerSends(
            signed_data['v'],
            signed_data['r'].to_bytes(32, 'big'),
            signed_data['s'].to_bytes(32, 'big'),
            signer_nonce,
            authed_accounts['signer'],
            i_data
        ).transact({'from': authed_accounts['cosigner']})

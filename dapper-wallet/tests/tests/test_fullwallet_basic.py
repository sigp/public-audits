import pytest
from eth_account import Account
from .dapper_utils import INTERFACE_TYPES


def test_init(fullwallet_deploy, accounts, assert_tx_failed, get_logs_for_event):
    """
    Test that the `init` function works as expected
    """
    # Set up
    authorized = accounts[1]
    cosigner = accounts[2]
    recovery = accounts[3]

    auth_version = (1 << 160)

    # Test that it can deploy once and `init` is called.
    (wallet, receipt, _) = fullwallet_deploy(
        authorized,
        cosigner,
        recovery
    )

    # Check that all the correct information is initialized.
    assert wallet.functions.authVersion().call() == auth_version, 'AuthVersion not initialized as expected'
    assert wallet.functions.recoveryAddress().call() == recovery, 'RecoveryAddress not set correctly'
    assert (wallet.functions.authorizations(auth_version + int(accounts[1], 0)).call()) == int(cosigner, 0), 'Cosigner and authorizations not correctly set'

    # Check that the event was fired.
    events = get_logs_for_event(wallet.events.Authorized, receipt['transactionHash'].hex())

    assert events[0]['args']['authorizedAddress'] == authorized, '"Authorized" event does not emit correct address'
    assert events[0]['args']['cosigner'] == int(cosigner, 0), '"Authorized" event does not emit correct address'

    # Check that it "init" is "onlyOnce".
    assert_tx_failed(
        wallet.functions.init(
            accounts[1],
            int(accounts[2], 0),
            accounts[3]
        ),
        {'from': accounts[0]}
    )


def test_fallback_pay(fullwallet_deploy, accounts, assert_tx_failed, assert_sendtx_failed, get_logs_for_event, w3):
    """
    Test that the `fallback` function can accept payment and all requires work
    as expected.
    """
    # Set up
    authorized = accounts[1]
    cosigner = accounts[2]
    recovery = accounts[3]

    #Deploy Full Wallet
    (wallet, _, _) = fullwallet_deploy(
        authorized,
        cosigner,
        recovery
    )

    # Send ETH to wallet (call fackback function)
    tx = wallet.fallback.transact({'from': accounts[1], 'value': 10**6})

    # Check the event
    events = get_logs_for_event(wallet.events.Received, tx)

    assert len(events) > 0, "No events emitted"
    assert events[0]['args']['from'] == accounts[1], "Message sender not same"
    assert events[0]['args']['value'] == 10**6, "Value not same"

    # Ensure contract balance is updated

    assert w3.eth.getBalance(wallet.address) == 10**6, "Balance not updated from fallback"

    # Check condition value > 0. As of commit 2d6889702507efed3615504e69df1d20cf1ea311, the msg.value > 0 condition is left out of the `require` statement
    # When sent a 0 value transaction, the transaction should not revert and should not emit the `Received` event

    tx = wallet.fallback.transact({'from': accounts[1]})
    events = get_logs_for_event(wallet.events.Received, tx)
    assert len(events) == 0, "Events emitted"

    # assert_tx_failed(
    #     wallet.fallback,
    #     {'from': accounts[1]}
    # )

    # Check condition data == 0
    assert_sendtx_failed({
        'to': wallet.address,
        'from': accounts[1],
        'value': 10**6,
        'data': '0x123'
    })


def test_onlyInvoked_modifier(fullwallet_deploy, assert_tx_failed, accounts, get_logs_for_event):
    """
    Test the `onlyInvoked` modifier
    """
    # Set up
    authorized = accounts[1]
    cosigner = accounts[1]
    recovery = accounts[3]

    (wallet, _, _) = fullwallet_deploy(
        authorized,
        cosigner,
        recovery
    )

    # setRecoveryAddress
    assert_tx_failed(
        wallet.functions.setRecoveryAddress(accounts[2]),
        {'from': accounts[1]}
    )

    # setAuthorized
    assert_tx_failed(
        wallet.functions.setAuthorized(accounts[2], int(accounts[2], 0)),
        {'from': accounts[1]}
    )


def test_emergencyRecovery(
        fullwallet_deploy,
        assert_tx_failed,
        zero_address,
        accounts,
        get_logs_for_event):
    """
    Test the emergencyRecovery increments the auth level and resets the
    authorized.
    """
    # Set up
    authorized = accounts[1]
    cosigner = accounts[1]
    recovery = accounts[3]

    (wallet, _, _) = fullwallet_deploy(
        authorized,
        cosigner,
        recovery
    )

    # All good (auth and cosigner)
    tx_one = wallet.functions.emergencyRecovery(
        accounts[2],
        int(accounts[2], 0)
    ).transact({'from': recovery})

    events_one = get_logs_for_event(
        wallet.events.EmergencyRecovery,
        tx_one
    )

    assert wallet.functions.authVersion().call() == (2 << 160), "Auth Version not incremented."

    assert len(events_one) > 0, "EmergencyRecovery event not emitted"
    assert events_one[0]['args']['authorizedAddress'] == accounts[2], "EmergencyRecovery event contains invalid authorizedAddress"
    assert events_one[0]['args']['cosigner'] == int(accounts[2], 0), "EmergencyRecovery event contains invalid cosigner"

    # Modifier test (onlyRecoveryAddress)
    assert_tx_failed(
        wallet.functions.emergencyRecovery(
            accounts[2],
            int(accounts[2], 0)
        ),
        {'from': accounts[5]}
    )

    # Authorized address should not be 0
    assert_tx_failed(
        wallet.functions.emergencyRecovery(
            zero_address,
            int(accounts[2], 0)
        ),
        {'from': recovery}
    )

    # Authorized address should not be recovery
    assert_tx_failed(
        wallet.functions.emergencyRecovery(
            recovery,
            int(recovery, 0)
        ),
        {'from': recovery}
    )

    # Cosigner should not be zero
    assert_tx_failed(
        wallet.functions.emergencyRecovery(
            accounts[2],
            int(zero_address, 0)
        ),
        {'from': recovery}
    )


def test_invoke0_recovery(
        fullwallet_deploy,
        assert_tx_failed,
        accounts,
        get_logs_for_event,
        invoke_data,
        w3):
    """
    Test that invoke0 can call 'setRecoveryAddress'
    """

    # Set up
    authorized = accounts[1]
    cosigner = accounts[1]
    recovery = accounts[3]

    # Deploy Full Wallet
    (wallet, _, _) = fullwallet_deploy(
        authorized,
        cosigner,
        recovery
    )

    addr_encoded = wallet.encodeABI(fn_name='setRecoveryAddress', args=[accounts[2]])
    # Revert, To, Value, Data
    d = invoke_data(1, wallet.address, 0, bytes.fromhex(addr_encoded[2:]))
    tx = wallet.functions.invoke0(d).transact({'from': accounts[1]})

    # Check that the recovery was correctly set
    assert wallet.functions.recoveryAddress().call() == accounts[2], "Invoke0 Recovery not correctly set"

    # Check that events emitted
    events = get_logs_for_event(wallet.events.RecoveryAddressChanged, tx)

    assert len(events) > 0, "No event emitted for SetRecoveryAddress"
    assert events[0]['args']['previousRecoveryAddress'] == accounts[3], "PreviousRecoveryAddress in event incorrect"
    assert events[0]['args']['newRecoveryAddress'] == accounts[2], "newRecoveryAddress in event incorrect"

    # Check cannot set authorized address as recovery
    addr_encoded = wallet.encodeABI(fn_name='setRecoveryAddress', args=[accounts[1]])
    d = invoke_data(1, wallet.address, 0, bytes.fromhex(addr_encoded[2:]))
    assert_tx_failed(
        wallet.functions.invoke0(d),
        {'from': accounts[1]}
    )


def test_invoke0_setAuthorized(
        fullwallet_deploy,
        assert_tx_failed,
        accounts,
        get_logs_for_event,
        invoke_data,
        w3):
    """
    Test that invoke0 can `setAuthorized`.
    """
    # Set up
    authorized = accounts[1]
    cosigner = accounts[1]
    recovery = accounts[3]

    auth_version = (1 << 160)

    # Deploy full wallet
    (wallet, _, _) = fullwallet_deploy(
        authorized,
        cosigner,
        recovery
    )
    int(authorized, 0)
    # Make sure that accounts[2] is not authorized
    assert wallet.functions.authorizations(auth_version + int(accounts[2], 0)).call() == 0
    # Make sure that accounts[1] is authorized with no cosigner
    assert wallet.functions.authorizations(auth_version + int(authorized, 0)).call() == int(accounts[1], 0)

    # Encode arguments
    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[accounts[2], int(accounts[2], 0)]
    )
    # Construct the data passed to `invoke0`
    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    # Send transaction
    tx = wallet.functions.invoke0(data).transact({'from': accounts[1]})
    # Get event log
    events = get_logs_for_event(wallet.events.Authorized, tx)

    assert len(events) > 0, "Authorized Event was not emitted"
    assert events[0]['args']['authorizedAddress'] == accounts[2], '"Authorized" event does not emit correct address'
    assert events[0]['args']['cosigner'] == int(accounts[2], 0), '"Authorized" event does not emit correct address'
    assert (wallet.functions.authorizations(auth_version + int(accounts[2], 0)).call()) == int(accounts[2], 0), 'Cosigner and authorizations not correctly set'


@pytest.mark.parametrize(
    "interface_i, should_pass",
    [(i, True) for i in INTERFACE_TYPES.values()] + [  # Defined interface IDs should pass
        ('0xffffffff', False),  # Some fake IDs should fail
        ('0xdeadbeef', False),
        ('0x00000000', False),
    ]
)
def test_supports_interface(
        fullwallet_deploy,
        walletfactory_deploy,
        wallet_from_factory,
        interface_i,
        should_pass):
    """
    Test that the `supportsInterface` responds as expected.
    """

    # Get our full wallet and cloneable wallet
    (full_wallet, _, _) = fullwallet_deploy()
    (cloneable_wallet, cw_rcpt, factory_wallet, fw_rcpt) = walletfactory_deploy()

    # Actually create a cloned wallet from the wallet factory
    (cloned_wallet, _) = wallet_from_factory(factory_wallet, False)

    # Actually create a full wallet from the wallet factory
    (new_full_wallet, _) = wallet_from_factory(factory_wallet, True)

    for index, wallet in enumerate([full_wallet, cloneable_wallet, cloned_wallet, new_full_wallet]):
        ret = wallet.functions.supportsInterface(interface_i).call()
        assert ret == should_pass, "Interface: {} incorrect ({})".format(interface_i, index)


def test_recoverGas(
        fullwallet_deploy,
        assert_tx_failed,
        zero_address,
        accounts,
        invoke_data,
        get_logs_for_event,
        w3):

    """
    Test the `recoverGas` functionality.
    """
    # Set up
    authorized = accounts[1]
    cosigner = accounts[1]
    recovery = accounts[3]

    (wallet, _, _) = fullwallet_deploy(
        authorized,
        cosigner,
        recovery
    )

    # Authorize the address
    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[accounts[2], int(accounts[2], 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    wallet.functions.invoke0(data).transact({'from': accounts[1]})

    # Authorize a number of addresses
    for acc in accounts[4:40]:
        args_encoded = wallet.encodeABI(
            fn_name='setAuthorized',
            args=[acc, int(acc, 0)]
        )

        data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
        wallet.functions.invoke0(data).transact({'from': accounts[1]})

    # Version Not Changed - Cannot Recover
    assert_tx_failed(
        wallet.functions.recoverGas(
            1,
            [
                accounts[1]
            ]
        ),
        {
            'from': accounts[4],
        }
    )

    # All good (auth and cosigner)
    wallet.functions.emergencyRecovery(
        accounts[2],
        int(accounts[2], 0)
    ).transact({'from': recovery})

    # Make sure that the address is now authorized
    assert wallet.functions.authorizations((2 << 160) + int(accounts[2], 0)).call() == int(accounts[2], 0)

    # Check require( version > 0 )
    assert_tx_failed(
        wallet.functions.recoverGas(
            0,
            [
                accounts[2],
            ]
        ),
        {
            'from': accounts[4],
        }
    )

    # Check require( version < 0xffffffff )
    assert_tx_failed(
        wallet.functions.recoverGas(
            int('0xffffffff', 0),
            [
                accounts[2],
            ]
        ),
        {
            'from': accounts[4],
        }
    )

    # Check version < authVersion
    assert_tx_failed(
        wallet.functions.recoverGas(
            2,
            [
                accounts[2],
            ]
        ),
        {
            'from': accounts[4],
        }
    )

    print("\nPrinting gas costs:")
    # Check can recoverGas for 1 account
    tx = wallet.functions.recoverGas(1, [accounts[2]]).transact({'from': accounts[4]})

    print(w3.eth.getTransactionReceipt(tx.hex())['gasUsed'])

    tx = wallet.functions.recoverGas(1, [accounts[3]]).transact({'from': accounts[4]})

    print(w3.eth.getTransactionReceipt(tx.hex())['gasUsed'])

    # Check can recoverGas for multiple accounts
    tx = wallet.functions.recoverGas(1, accounts[10:40]).transact({'from': accounts[4], 'gas':500000})

    print(w3.eth.getTransactionReceipt(tx.hex())['gasUsed'])


# This test is no longer relevant as ERC725 is no longer supported in the version of the CoreWallet contract
#
# def test_key_has_purpose(
#         fullwallet_deploy,
#         assert_tx_failed,
#         zero_address,
#         accounts,
#         invoke_data,
#         get_logs_for_event,
#         w3):
#     """
#     Checks that the `keyHasPurpose` responds correctly and correct keys have
#     correct purpose.
#     """
#
#     # Get our full wallet and cloneable wallet
#     (wallet, _, accs) = fullwallet_deploy(
#         accounts[1],
#         accounts[1],
#         accounts[3]
#     )
#
#     # Ensure that the accounts is currently not 'authorized' is not a key.
#     initial_purpose = wallet.functions.keyHasPurpose(
#         '0x' + ('0' * 24) + accounts[2][2:],
#         2
#     ).call()
#     assert initial_purpose is False, "Key: {} already has a purpose.".format(accounts[2])
#
#     # Add the keys
#     args_encoded = wallet.encodeABI(
#         fn_name='setAuthorized',
#         args=[accounts[2], int(accounts[2], 0)]
#     )
#
#     data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
#     wallet.functions.invoke0(data).transact({'from': accounts[1]})
#
#     current_purpose = wallet.functions.keyHasPurpose(
#         '0x' + ('0' * 24) + accounts[2][2:],
#         2
#     ).call()
#
#     assert current_purpose is True, "Key: {} does not have correct purpose.".format(accounts[2])
#
#     # Assert false when PURPOSE != 1 or 2
#     assert False is wallet.functions.keyHasPurpose(
#         '0x' + ('0' * 24) + accounts[2][2:],
#         4
#     ).call(), "Purpose not 1 or 2 still True"
#
#     # Assert false when signed authorized is 0
#     args_encoded = wallet.encodeABI(
#         fn_name='setAuthorized',
#         args=[accounts[4], int(zero_address, 0)]
#     )
#
#     data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
#     wallet.functions.invoke0(data).transact({'from': accounts[1]})
#
#     assert False is wallet.functions.keyHasPurpose(
#         '0x' + ('0' * 24) + accounts[4][2:],
#         1
#     ).call(), "Zero Cosigner is True"
#

def test_invoke1_cosigner_sends(
        fullwallet_deploy,
        assert_tx_failed,
        zero_address,
        accounts,
        invoke_data,
        invoke1_sign_data,
        get_logs_for_event,
        w3):
    """
    Test to see if `invoke1CosignerSends` can:
        1. Invoke functions.
        2. React to incorrect signer/cosigner pairs.
    """

    # Create a new account
    new_account = Account.create('')

    (wallet, _, accs) = fullwallet_deploy(
        accounts[1],
        accounts[1],
        accounts[3]
    )

    # Authorize the new address with cosigner as accounts[2]
    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[new_account.address, int(accounts[2], 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    tx = wallet.functions.invoke0(data).transact({'from': accounts[1]})

    assert wallet.functions.authorizations((1 << 160) + int(new_account.address, 0)).call() == int(accounts[2], 0)

    # Goal: Set account[5] as authorized
    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[accounts[5], int(accounts[2], 0)]
    )

    data_one = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    nonce = wallet.functions.nonces(new_account.address).call()

    # databytes = b'' + 0x19.to_bytes(1, 'big') + 0x0.to_bytes(1, 'big') + bytes.fromhex(wallet.address[2:]) + nonce.to_bytes(32, 'big') + data_one

    operation_data = invoke1_sign_data(wallet, nonce, new_account.address, data_one)

    signed = new_account.signHash(operation_data['hash'])

    tx = wallet.functions.invoke1CosignerSends(
        signed['v'],   # v
        signed['r'].to_bytes(32, 'big'),   # r
        signed['s'].to_bytes(32, 'big'),   # s
        nonce,         # nonce
        new_account.address,
        data_one       # data
    ).transact({'from': accounts[2]})

    evs = get_logs_for_event(wallet.events.Authorized, tx.hex())

    # Ensure action happened
    assert len(evs) > 0, "Authorized Event was not emitted"
    assert evs[0]['args']['authorizedAddress'] == accounts[5], '"Authorized" event does not emit correct address'
    assert evs[0]['args']['cosigner'] == int(accounts[2], 0), '"Authorized" event does not emit correct address'
    assert (wallet.functions.authorizations((1 << 160) + int(accounts[5], 0)).call()) == int(accounts[2], 0), 'Cosigner and authorizations not correctly set'
    assert wallet.functions.nonces(new_account.address).call() == nonce + 1, 'Nonce not updated correctly'

    nonce += 1

    # Check that invalid 'data' produces incorrect signer.
    assert_tx_failed(
        wallet.functions.invoke1CosignerSends(
            signed['v'],   # v
            signed['r'].to_bytes(32, 'big'),   # r
            signed['s'].to_bytes(32, 'big'),   # s
            nonce,         # nonce
            accounts[5],
            data_one + b'\x00\x1a\x11'       # data
        ),
        {'from': accounts[2]}
    )

    # Check that incorrect nonce produces incorrect signer
    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[accounts[6], int(accounts[2], 0)]
    )

    data_two = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    operation_data = invoke1_sign_data(wallet, nonce, accounts[6], data_one)

    signed = new_account.signHash(operation_data['hash'])

    assert_tx_failed(
        wallet.functions.invoke1CosignerSends(
            signed['v'],   # v
            signed['r'].to_bytes(32, 'big'),   # r
            signed['s'].to_bytes(32, 'big'),   # s
            255,         # nonce
            accounts[6],
            data_two       # data
        ),
        {'from': accounts[2]}
    )

    # Ensure incorrect v is handled
    assert_tx_failed(
        wallet.functions.invoke1CosignerSends(
            nonce,   # v
            signed['r'].to_bytes(32, 'big'),   # r
            signed['s'].to_bytes(32, 'big'),   # s
            nonce,         # nonce
            accounts[6],
            data_two       # data
        ),
        {'from': accounts[2]}
    )

    # Incorrect cosigner
    assert_tx_failed(
        wallet.functions.invoke1CosignerSends(
            nonce,   # v
            signed['r'].to_bytes(32, 'big'),   # r
            signed['s'].to_bytes(32, 'big'),   # s
            nonce,         # nonce
            accounts[6],
            data_two       # data
        ),
        {'from': accounts[6]}
    )

    # Ensure signer and cosigner same address can invoke
    second_account = Account.privateKeyToAccount('0x989dbcbd23972f521370a8b13462bf915489b24e11a1bb724935a19fff036fb5')

    # Produce transaction
    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[second_account.address, int(second_account.address, 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    wallet.functions.invoke0(data).transact({'from': accounts[1]})

    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[accounts[7], int(accounts[2], 0)]
    )

    data_two = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    nonce_second = wallet.functions.nonces(second_account.address).call()

    # databytes = b'' + 0x19.to_bytes(1, 'big') + 0x0.to_bytes(1, 'big') + bytes.fromhex(wallet.address[2:]) + nonce.to_bytes(32, 'big') + data_one

    operation_data = invoke1_sign_data(wallet, nonce_second, second_account.address, data_two)

    signed = second_account.signHash(operation_data['hash'])

    # DEBUG:
    # print(operation_hash.hex())
    # print(signed)
    # print(Account.recoverHash(operation_hash, vrs=(
    #     signed['v'],
    #     signed['r'].to_bytes(32, 'big'),
    #     signed['s'].to_bytes(32, 'big')
    # )))
    # print(new_account.address)

    tx = wallet.functions.invoke1CosignerSends(
        signed['v'],   # v
        signed['r'].to_bytes(32, 'big'),   # r
        signed['s'].to_bytes(32, 'big'),   # s
        nonce_second,         # nonce
        second_account.address,
        data_two  # data
    ).transact({'from': second_account.address})

    evs = get_logs_for_event(wallet.events.Authorized, tx.hex())

    # Ensure action happened
    assert len(evs) > 0, "Authorized Event was not emitted"
    assert evs[0]['args']['authorizedAddress'] == accounts[7], '"Authorized" event does not emit correct address'
    assert evs[0]['args']['cosigner'] == int(accounts[2], 0), '"Authorized" event does not emit correct address'
    assert (wallet.functions.authorizations((1 << 160) + int(accounts[7], 0)).call()) == int(accounts[2], 0), 'Cosigner and authorizations not correctly set'
    assert wallet.functions.nonces(second_account.address).call() == nonce_second + 1, 'Nonce not updated correctly'


def test_invoke1_signer_sends(
        fullwallet_deploy,
        assert_tx_failed,
        zero_address,
        accounts,
        invoke_data,
        invoke1_sign_data,
        get_logs_for_event,
        w3):
    """
    Ensures that the `Invoke1SignerSends` operates correctly.
    """

    # Create a new account
    cosigner_account = Account.privateKeyToAccount('0x989dbcbd23972f521370a8b13462bf915489b24e11a1bb724935a19fff036fb5')

    (wallet, _, accs) = fullwallet_deploy(
        accounts[1],
        accounts[1],
        accounts[3]
    )

    # Accounts[2] has cosigner cosigner_account
    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[accounts[2], int(cosigner_account.address, 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    wallet.functions.invoke0(data).transact({'from': accounts[1]})

    # See if the Transaction can go through
    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[accounts[7], int(accounts[2], 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    signer_nonce = wallet.functions.nonces(accounts[2]).call()
    operation_data = invoke1_sign_data(wallet, signer_nonce, accounts[2], data)
    signed = cosigner_account.signHash(operation_data['hash'])

    tx = wallet.functions.invoke1SignerSends(
        signed['v'],                        # v
        signed['r'].to_bytes(32, 'big'),    # r
        signed['s'].to_bytes(32, 'big'),    # s
        data                                # Data
    ).transact({'from': accounts[2]})

    evs = get_logs_for_event(wallet.events.Authorized, tx.hex())
    assert len(evs) > 0, "Authorized Event was not emitted"
    assert evs[0]['args']['authorizedAddress'] == accounts[7], '"Authorized" event does not emit correct address'
    assert evs[0]['args']['cosigner'] == int(accounts[2], 0), '"Authorized" event does not emit correct address'
    assert (wallet.functions.authorizations((1 << 160) + int(accounts[7], 0)).call()) == int(accounts[2], 0), 'Cosigner and authorizations not correctly set'
    assert wallet.functions.nonces(accounts[2]).call() == signer_nonce + 1, 'Nonce not updated correctly'
    assert wallet.functions.nonces(cosigner_account.address).call() == 0, 'CoSigner nonce updated incorrectly'

    # Invalid V should fail
    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[accounts[8], int(accounts[2], 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    signer_nonce = wallet.functions.nonces(accounts[2]).call()
    operation_data = invoke1_sign_data(wallet, signer_nonce, accounts[8], data)
    signed = cosigner_account.signHash(operation_data['hash'])

    assert_tx_failed(
        wallet.functions.invoke1SignerSends(
            25,                                 # v
            signed['r'].to_bytes(32, 'big'),    # r
            signed['s'].to_bytes(32, 'big'),    # s
            data                                # Data
        ),
        {'from': accounts[2]}
    )

    operation_data = invoke1_sign_data(wallet, 21, accounts[7], data)
    signed = cosigner_account.signHash(operation_data['hash'])

    # Invalid nonce should fail (reusing the same transaction data)
    assert_tx_failed(
        wallet.functions.invoke1SignerSends(
            signed['v'],                        # v
            signed['r'].to_bytes(32, 'big'),    # r
            signed['s'].to_bytes(32, 'big'),    # s
            data                                # Data
        ),
        {'from': accounts[2]}
    )

    # Wrong signer should fail
    fake_signer = Account.create('')

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    signer_nonce = wallet.functions.nonces(accounts[2]).call()
    operation_data = invoke1_sign_data(wallet, signer_nonce, accounts[2], data)
    signed = fake_signer.signHash(operation_data['hash'])

    assert_tx_failed(
        wallet.functions.invoke1SignerSends(
            signed['v'],                        # v
            signed['r'].to_bytes(32, 'big'),    # r
            signed['s'].to_bytes(32, 'big'),    # s
            data                                # Data
        ),
        {'from': accounts[2]}
    )

    # Cosigner as Signer should allow

    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[cosigner_account.address, int(cosigner_account.address, 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    wallet.functions.invoke0(data).transact({'from': accounts[1]})

    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[accounts[8], int(cosigner_account.address, 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    cosigner_nonce = wallet.functions.nonces(cosigner_account.address).call()
    operation_data = invoke1_sign_data(wallet, cosigner_nonce, accounts[8], data)
    signed = cosigner_account.signHash(operation_data['hash'])

    tx = wallet.functions.invoke1SignerSends(
        signed['v'],                        # v
        signed['r'].to_bytes(32, 'big'),    # r
        signed['s'].to_bytes(32, 'big'),    # s
        data                                # Data
    ).transact({'from': cosigner_account.address})

    evs = get_logs_for_event(wallet.events.Authorized, tx.hex())
    assert len(evs) > 0, "Authorized Event was not emitted"
    assert evs[0]['args']['authorizedAddress'] == accounts[8], '"Authorized" event does not emit correct address'
    assert evs[0]['args']['cosigner'] == int(cosigner_account.address, 0), '"Authorized" event does not emit correct address'
    assert (wallet.functions.authorizations((1 << 160) + int(accounts[8], 0)).call()) == int(cosigner_account.address, 0), 'Cosigner and authorizations not correctly set'
    assert wallet.functions.nonces(cosigner_account.address).call() == cosigner_nonce + 1, 'Nonce not updated correctly'


def test_invoke2(
        fullwallet_deploy,
        assert_tx_failed,
        zero_address,
        accounts,
        invoke_data,
        invoke1_sign_data,
        get_logs_for_event,
        w3):
    """
    Check that `invoke2` can correctly invoke and check signatures.
    """

    # Set up the accounts
    signer = Account.privateKeyToAccount('0xed765f17c0930ed68ae04a929548f4386d50236903016c0e01e191670543fab7')
    cosigner = Account.privateKeyToAccount('0x989dbcbd23972f521370a8b13462bf915489b24e11a1bb724935a19fff036fb5')
    fake = Account.create('')

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

    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[accounts[8], int(cosigner.address, 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    signer_nonce = wallet.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(wallet, signer_nonce, signer.address, data)
    signed = {
        'signer': signer.signHash(operation_data['hash']),
        'cosigner': cosigner.signHash(operation_data['hash'])
    }

    tx = wallet.functions.invoke2(
        [signed['signer']['v'], signed['cosigner']['v']],
        [signed['signer']['r'].to_bytes(32, 'big'), signed['cosigner']['r'].to_bytes(32, 'big')],
        [signed['signer']['s'].to_bytes(32, 'big'), signed['cosigner']['s'].to_bytes(32, 'big')],
        signer_nonce,
        signer.address,
        data
    ).transact({'from': accounts[1]})  # Can send from different account

    evs = get_logs_for_event(wallet.events.Authorized, tx.hex())
    assert len(evs) > 0, "Authorized Event was not emitted"
    assert evs[0]['args']['authorizedAddress'] == accounts[8], '"Authorized" event does not emit correct address'
    assert evs[0]['args']['cosigner'] == int(cosigner.address, 0), '"Authorized" event does not emit correct address'
    assert (wallet.functions.authorizations((1 << 160) + int(accounts[8], 0)).call()) == int(cosigner.address, 0), 'Cosigner and authorizations not correctly set'
    assert wallet.functions.nonces(signer.address).call() == signer_nonce + 1, 'Nonce not updated correctly'

    # Invalid V should fail
    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[accounts[7], int(cosigner.address, 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    signer_nonce = wallet.functions.nonces(signer.address).call()
    operation_data = invoke1_sign_data(wallet, signer_nonce, signer.address, data)
    signed = {
        'signer': signer.signHash(operation_data['hash']),
        'cosigner': cosigner.signHash(operation_data['hash'])
    }

    assert_tx_failed(
        wallet.functions.invoke2(
            [25, signed['cosigner']['v']],
            [signed['signer']['r'].to_bytes(32, 'big'), signed['cosigner']['r'].to_bytes(32, 'big')],
            [signed['signer']['s'].to_bytes(32, 'big'), signed['cosigner']['s'].to_bytes(32, 'big')],
            signer_nonce,
            signer.address,
            data
        ),
        {'from': accounts[1]}
    )

    assert_tx_failed(
        wallet.functions.invoke2(
            [signed['cosigner']['v'], 25],
            [signed['signer']['r'].to_bytes(32, 'big'), signed['cosigner']['r'].to_bytes(32, 'big')],
            [signed['signer']['s'].to_bytes(32, 'big'), signed['cosigner']['s'].to_bytes(32, 'big')],
            signer_nonce,
            signer.address,
            data
        ),
        {'from': accounts[1]}
    )

    # Invalid Nonce should fail
    assert_tx_failed(
        wallet.functions.invoke2(
            [signed['cosigner']['v'], signed['cosigner']['v']],
            [signed['signer']['r'].to_bytes(32, 'big'), signed['cosigner']['r'].to_bytes(32, 'big')],
            [signed['signer']['s'].to_bytes(32, 'big'), signed['cosigner']['s'].to_bytes(32, 'big')],
            11,
            signer.address,
            data
        ),
        {'from': accounts[1]}
    )

    # Incorrect signer signs
    fake_signed = fake.signHash(operation_data['hash'])

    assert_tx_failed(
        wallet.functions.invoke2(
            [fake_signed['v'], signed['cosigner']['v']],
            [fake_signed['r'].to_bytes(32, 'big'), signed['cosigner']['r'].to_bytes(32, 'big')],
            [fake_signed['s'].to_bytes(32, 'big'), signed['cosigner']['s'].to_bytes(32, 'big')],
            signer_nonce,
            signer.address,
            data
        ),
        {'from': accounts[1]}
    )

    # If signer is both signer and cosigner
    # {cosigner: cosigner}
    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[cosigner.address, int(cosigner.address, 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    wallet.functions.invoke0(data).transact({'from': accounts[1]})

    args_encoded = wallet.encodeABI(
        fn_name='setAuthorized',
        args=[accounts[4], int(cosigner.address, 0)]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
    cosigner_nonce = wallet.functions.nonces(cosigner.address).call()
    operation_data = invoke1_sign_data(wallet, cosigner_nonce, cosigner.address, data)
    signed = cosigner.signHash(operation_data['hash'])

    tx = wallet.functions.invoke2(
        [signed['v'], signed['v']],
        [signed['r'].to_bytes(32, 'big'), signed['r'].to_bytes(32, 'big')],
        [signed['s'].to_bytes(32, 'big'), signed['s'].to_bytes(32, 'big')],
        cosigner_nonce,
        cosigner.address,
        data
    ).transact({'from': accounts[1]})  # Can send from different account

    evs = get_logs_for_event(wallet.events.Authorized, tx.hex())
    assert len(evs) > 0, "Authorized Event was not emitted"
    assert evs[0]['args']['authorizedAddress'] == accounts[4], '"Authorized" event does not emit correct address'
    assert evs[0]['args']['cosigner'] == int(cosigner.address, 0), '"Authorized" event does not emit correct address'
    assert (wallet.functions.authorizations((1 << 160) + int(accounts[4], 0)).call()) == int(cosigner.address, 0), 'Cosigner and authorizations not correctly set'
    assert wallet.functions.nonces(cosigner.address).call() == cosigner_nonce + 1, 'Nonce not updated correctly'

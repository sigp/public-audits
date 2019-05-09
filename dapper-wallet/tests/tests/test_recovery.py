

def test_emergencyRecovery_multiple_times(
        accounts,
        assert_tx_failed,
        zero_address,
        fullwallet_deploy,
        w3):
    """
    Check that can recover more than once
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

    wallet.functions.emergencyRecovery(
        accounts[2],
        int(accounts[2], 0)
    ).transact({'from': recovery})

    assert wallet.functions.authorizations((2 << 160) + int(accounts[2], 0)).call() == int(accounts[2], 0)

    wallet.functions.emergencyRecovery(
        accounts[2],
        int(accounts[2], 0)
    ).transact({'from': recovery})

    assert wallet.functions.authorizations((3 << 160) + int(accounts[2], 0)).call() == int(accounts[2], 0)


def test_all_events_omitted(
        accounts,
        assert_tx_failed,
        get_logs_for_event,
        zero_address,
        fullwallet_deploy,
        w3):
    """
    Check if wallet can be locked when providing invalid addresses.
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

    tx = wallet.functions.emergencyRecovery(
        accounts[2],
        int(accounts[2], 0)
    ).transact({'from': recovery})

    ev = get_logs_for_event(wallet.events.EmergencyRecovery, tx.hex())

    assert ev[0]['args']['authorizedAddress'] == accounts[2]
    assert ev[0]['args']['cosigner'] == int(accounts[2], 0)

    tx = wallet.functions.emergencyRecovery(
        accounts[2],
        int(accounts[2], 0)
    ).transact({'from': recovery})

    ev = get_logs_for_event(wallet.events.EmergencyRecovery, tx.hex())

    assert ev[0]['args']['authorizedAddress'] == accounts[2]
    assert ev[0]['args']['cosigner'] == int(accounts[2], 0)


def test_new_recovery_can_recover(
        accounts,
        assert_tx_failed,
        invoke_data,
        get_logs_for_event,
        zero_address,
        fullwallet_deploy,
        w3):
    """
    Check that the new recovery address can recover.
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

    # Emergency recover with current address
    tx = wallet.functions.emergencyRecovery(
        accounts[2],
        int(accounts[2], 0)
    ).transact({'from': recovery})

    ev = get_logs_for_event(wallet.events.EmergencyRecovery, tx.hex())

    assert ev[0]['args']['authorizedAddress'] == accounts[2]
    assert ev[0]['args']['cosigner'] == int(accounts[2], 0)

    # Change the recovery address to accounts[4]
    args_encoded = wallet.encodeABI(
        fn_name='setRecoveryAddress',
        args=[accounts[4]]
    )

    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))

    # Previous authorized cannot invoke
    assert_tx_failed(
        wallet.functions.invoke0(data),
        {'from': accounts[1]}
    )

    tx = wallet.functions.invoke0(data).transact({'from': accounts[2]})

    ev = get_logs_for_event(wallet.events.RecoveryAddressChanged, tx.hex())

    assert ev[0]['args']['previousRecoveryAddress'] == accounts[3]
    assert ev[0]['args']['newRecoveryAddress'] == accounts[4]

    tx = wallet.functions.emergencyRecovery(
        accounts[5],
        int(accounts[5], 0)
    ).transact({'from': accounts[4]})  # new recovery

    ev = get_logs_for_event(wallet.events.EmergencyRecovery, tx.hex())

    assert ev[0]['args']['authorizedAddress'] == accounts[5]
    assert ev[0]['args']['cosigner'] == int(accounts[5], 0)

    assert wallet.functions.authVersion().call() == (3 << 160)


def test_bug_cosigner_to_0(
    accounts,
    assert_tx_failed,
    fullwallet_deploy,
    zero_address,
    get_logs_for_event,
    invoke_data):
    """
    Deliberately break the setAuthorisation by setting cosigner = 0
    Attempt and fail invoke
    Recover Account
    """

    authorized = accounts[1]
    cosigner = accounts[1]
    recovery = accounts[3]
    authVersion = 1 << 160
    (wallet,_,_) = fullwallet_deploy(
        authorized,
        cosigner,
        recovery)

    args_encoded = wallet.encodeABI(
            fn_name='setAuthorized',
            args=[accounts[1], 0])
    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))

    tx = wallet.functions.invoke0(data).transact({'from': accounts[1]})

    events = get_logs_for_event(wallet.events.Authorized, tx)

    """
    Assertions that cosigner was able to be set to 0
    """
    assert len(events) > 0, "Auhtorized event failed to set cosigner to 0"
    assert events[0]['args']['authorizedAddress'] == accounts[1], "Authorized address is not account 1"
    assert events[0]['args']['cosigner'] == 0, "Cosigner in event not set to 0"
    assert wallet.functions.authorizations(authVersion + int(accounts[1], 0)).call() == 0, "Cosigner in the contract state is not set to 0"


    """
    # Check that calling invoke0 now fails
    """
    args_encoded = wallet.encodeABI(
            fn_name='setAuthorized',
            args=[accounts[1], int(accounts[1], 0)])
    data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))

    assert_tx_failed(wallet.functions.invoke0(data), {'from': accounts[1], 'gas': 3000000})


    """
    #Confirm that recovery of address is still possible
    """
    tx = wallet.functions.emergencyRecovery(accounts[2], int(accounts[2], 0)).transact({'from': accounts[3]})

    events = get_logs_for_event(wallet.events.Authorized, tx)

    authIncrementor = 1 << 160
    authVersion += authIncrementor

    assert wallet.functions.authorizations(authVersion + int(accounts[2], 0)).call() == int(accounts[2], 0)

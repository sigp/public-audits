def test_deploy(walletfactory_deploy, accounts, fullwallet_deploy, zero_address):

    # Estimate Block Gas Limit
    block_gas_limit = 7e6

    # Check the deploys
    (cloneable_c, cloneable_r, factory_c, factory_r) = walletfactory_deploy()
    (fullwallet_c, fullwallet_r, accs) = fullwallet_deploy()

    assert cloneable_c.address != 0, 'CloneableWallet Address Returned is 0x0'
    assert factory_c.address != 0, 'Factory Address Returned is 0x0'

    # Cloneable Wallet
    assert cloneable_c.functions.VERSION().call() == '1.0.0', 'Core Wallet `VERSION` not accessible.'
    assert cloneable_c.functions.authVersion().call() == 0, 'Core Wallet `authVersion` not accessible.'
    assert cloneable_c.functions.initialized().call() is True, 'Core Wallet `initialized` not set to True.'
    assert cloneable_c.functions.recoveryAddress().call() == zero_address, 'Core Wallet `recoveryAddress` not initialized to 0x0'

    # FullWallet
    assert fullwallet_c.functions.VERSION().call() == '1.0.0', 'Core Wallet `VERSION` not accessible.'
    assert fullwallet_c.functions.authVersion().call() == (1 << 160), 'Core Wallet `authVersion` not accessible.'
    assert fullwallet_c.functions.initialized().call() is True, 'Core Wallet `initialized` not set to True.'
    assert fullwallet_c.functions.recoveryAddress().call() == accounts[3], 'Core Wallet `recoveryAddress` not initialized to {}'.format(accounts[3])

    # Print Stats:
    print("")
    print("Gas used to deploy 'CloneableWallet': {}".format(
        cloneable_r['gasUsed']
    ))
    print("Gas used to deploy 'WalletFactory': {}".format(
        factory_r['gasUsed']
    ))
    print("Gas used to deploy 'FullWallet': {}".format(
        fullwallet_r['gasUsed']
    ))

    # Make sure they are below the gas limits
    assert cloneable_r['gasUsed'] < block_gas_limit
    assert factory_r['gasUsed'] < block_gas_limit
    assert fullwallet_r['gasUsed'] < block_gas_limit


def test_factory_deploys(
        walletfactory_deploy,
        fullwallet_deploy,
        accounts,
        zero_address,
        get_logs_for_event,
        w3):
    (cloned_c, _, factory, _) = walletfactory_deploy()

    # Factory Deploy Cloned Wallet
    tx = factory.functions.deployCloneWallet(
        accounts[1],  # RecoveryAddress
        accounts[2],  # AuthorizedAddress
        1000,
    ).transact({'from': accounts[0]})

    event = get_logs_for_event(factory.events.WalletCreated, tx)[0]['args']

    cloned = w3.eth.contract(
        address=event['wallet'],
        abi=cloned_c.abi
    )

    assert cloned.address == event['wallet'], 'Wallet address incorrect'
    assert cloned.functions.initialized().call() is True, 'Cloned Wallet Initialized False'
    assert cloned.functions.recoveryAddress().call() == accounts[1], 'Cloned Wallet Recovery Address not as specified'

    # Factory Deploy Full Wallet
    tx_two = factory.functions.deployFullWallet(
        accounts[1],  # RecoveryAddress
        accounts[2],  # AuthorizedAddress
        1000,
    ).transact({'from': accounts[0]})

    event_two = get_logs_for_event(factory.events.WalletCreated, tx_two)[0]['args']

    (fullwallet_c, _, _) = fullwallet_deploy()

    factory_full = w3.eth.contract(
        address=event_two['wallet'],
        abi=fullwallet_c.abi
    )

    # FullWallet
    assert factory_full.functions.VERSION().call() == '1.0.0', 'Core Wallet `VERSION` not accessible.'
    assert factory_full.functions.authVersion().call() == (1 << 160), 'Core Wallet `authVersion` not accessible.'
    assert factory_full.functions.initialized().call() is True, 'Core Wallet `initialized` not set to True.'
    assert factory_full.functions.recoveryAddress().call() == accounts[1], 'Core Wallet `recoveryAddress` not initialized to {}'.format(accounts[1])


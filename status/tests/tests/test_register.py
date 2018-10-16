################################################################################
# register()
################################################################################


def test_register_double(accounts, registrar_deploy, w3, assert_tx_failed):
    '''
    Tests register() should not double register
    '''

    # Deploy
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    # Label
    label = w3.soliditySha3(['string'], ['validuser'])

    # Activate
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    # Register account to label
    c.functions.register(
        label,
        accounts[1],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    assert_tx_failed(
        c.functions.register(
            label,
            accounts[1],
            w3.soliditySha3(['bytes32'], ['0x0']),
            w3.soliditySha3(['bytes32'], ['0x0']),
        ),
        {'from': accounts[0]}
    )


def test_register_two_people(accounts, registrar_deploy, w3, assert_tx_failed):
    '''
    Tests register() register the name to two people
    '''

    # Deploy
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    # Label
    label = w3.soliditySha3(['string'], ['validuser'])

    # Activate and Transfer
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})
    token_c.functions.transfer(accounts[2], w3.toInt(10e3)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[2]})

    # Register account to label
    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    assert_tx_failed(
        c.functions.register(
            label,
            accounts[2],
            w3.soliditySha3(['bytes32'], ['0x0']),
            w3.soliditySha3(['bytes32'], ['0x0']),
        ),
        {'from': accounts[2]}
    )


def test_register_empty(accounts, registrar_deploy, w3, assert_tx_failed, variables):
    '''
    Tests register() register the name to two people
    '''

    # Deploy
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    # Label
    label = w3.soliditySha3(['string'], [''])

    # Activate and Transfer
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})

    # send tokens to accounts[2]
    token_c.functions.transfer(accounts[2], w3.toInt(10e6)).transact({'from': accounts[0]})

    #assert token_c.functions.balanceOf(accounts[2]).call() == 0
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[2]})

    assert c.functions.getAccountOwner(label).call() == variables['zero_address'], "Correct owner returned"

    # Register account[2] to label
    c.functions.register(
        label,
        accounts[2],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[2]})

    assert c.functions.getAccountOwner(label).call() == accounts[2], "Correct owner returned"


def test_register_sub_user_as_single(accounts, registrar_deploy, w3, assert_tx_failed, variables):

    # Deploy
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    # Label
    label_one = w3.soliditySha3(['string'], ['hello'])
    label_two = w3.soliditySha3(['string'], ['sub.hello'])
    label_three = w3.soliditySha3(['string'], ['more.sub.hello'])

    # Activate and Transfer
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})
    token_c.functions.transfer(accounts[2], w3.toInt(10e3)).transact({'from': accounts[0]})
    token_c.functions.transfer(accounts[3], w3.toInt(10e3)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[2]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[3]})

    # Register account to label
    c.functions.register(
        label_one,
        resolver_c.address,
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[2]})

    assert c.functions.getAccountOwner(label_one).call() == accounts[2], "Correct owner returned"

    c.functions.register(
        label_two,
        resolver_c.address,
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[2]})

    assert c.functions.getAccountOwner(label_two).call() == accounts[2], "Correct owner returned"

    # Verify that account3 can't register label3
    c.functions.register(
        label_three,
        resolver_c.address,
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[3]})

    assert c.functions.getAccountOwner(label_three).call() == accounts[3], "Correct owner returned"

################################################################################
# release()
################################################################################


def test_no_early_release(accounts, registrar_deploy, w3, assert_tx_failed, variables, block_timestamp):
    # Deploy
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    # Label
    label = w3.soliditySha3(['string'], ['hello'])

    # Activate and Transfer
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    # Register account to label
    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    # Ensure release in the future
    assert c.functions.getReleaseTime(label).call() > block_timestamp(), "ExpirationTime Returned Correct"

    # Try to release early - should revert
    assert_tx_failed(c.functions.release(label), {'from': accounts[0]})


def test_no_other_release(accounts, registrar_deploy, w3, assert_tx_failed, variables, block_timestamp, ganache_set_time):
    # Deploy
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    # Label
    label = w3.soliditySha3(['string'], ['hello'])

    # Activate and Transfer
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    # Register account to label
    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    # Ensure release in the future
    assert c.functions.getReleaseTime(label).call() > block_timestamp(), "ExpirationTime Returned Correct"

    ganache_set_time(c.functions.getReleaseTime(label).call())

    # Try to release early - should revert
    assert_tx_failed(c.functions.release(label), {'from': accounts[2]})


def test_release_allowed(accounts, registrar_deploy, w3, get_logs_for_event, variables, block_timestamp, ganache_set_time, days):
    # Deploy
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    # Label
    label = w3.soliditySha3(['string'], ['hello'])
    namehash = w3.soliditySha3(['bytes32','bytes32'], [ens_node, label])

    # Activate and Transfer
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    # Register account to label
    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    # Ensure release in the future
    assert c.functions.getReleaseTime(label).call() > block_timestamp(), "ExpirationTime Returned Correct"

    ganache_set_time(c.functions.getReleaseTime(label).call() + days(2))

    # Release
    tx_event = get_logs_for_event(c.events.UsernameOwner, c.functions.release(label).transact({'from': accounts[0]}))

    # Check all correctly set
    assert tx_event[0]['args']['owner'] == variables['zero_address']

    # UsernaameOwner(label, 0) => namehash == label!!
    assert '0x' + tx_event[0]['args']['nameHash'].hex() == namehash.hex()


def test_no_double_release(accounts, registrar_deploy, w3, get_logs_for_event, variables, block_timestamp, ganache_set_time, days, assert_tx_failed):
    '''
    Test that a name cannot be double released
    '''

    # Deploy
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    # Label
    label = w3.soliditySha3(['string'], ['hello'])

    # Activate and Transfer
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    # Register account to label
    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    # Ensure release in the future
    assert c.functions.getReleaseTime(label).call() > block_timestamp(), "ExpirationTime Returned Correct"

    ganache_set_time(c.functions.getReleaseTime(label).call() + days(2))

    # Release
    c.functions.release(label).transact({'from': accounts[0]})

    assert_tx_failed(c.functions.release(label), {'from': accounts[0]})

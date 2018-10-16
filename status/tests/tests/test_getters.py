################################################################################
# getPrice
################################################################################


def test_get_price_uninitialised(registrar_deploy):
    '''
    Tests getPrice() with initialized value
    '''

    # Deploy Contract
    (c, _, _, _, _, _) = registrar_deploy()

    # GetPrice on deploy
    assert c.functions.getPrice().call() == 0, "GetPrice returns correct uninitialised price"


def test_get_price_updated(accounts, registrar_deploy, w3):
    '''
    Tests getPrice() with updated value
    '''

    # Deploy Contract
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 10

    # Activate the registry
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})

    # Check that getPrice returns correct price
    assert c.functions.getPrice().call() == new_price, "getPrice returns correct price"


def test_get_price_returns_same(accounts, registrar_deploy, w3):
    '''
    Tests getPrice() with updated value
    '''

    new_price = 1e10

    # Deploy Contract
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    # Activate the registry
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})

    # Check that getPrice returns correct price
    assert c.functions.getPrice().call() == c.functions.price().call(), "getPrice returns same as price"


################################################################################
# getAccountBalance
################################################################################


def test_get_account_balance_incorrect(accounts, registrar_deploy, assert_tx_failed, w3, variables):
    '''
    Tests getAccountBalance() for an incorrect label
    '''

    new_price = 1e1
    chosen_account = accounts[1]
    label = w3.soliditySha3(['string'], ["somethinglong"])
    incor = w3.soliditySha3(['string'], ['thisiswrong'])

    # Deploy
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    # Activate
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    # Register account to label
    c.functions.register(
        label,
        chosen_account,
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    # Check the correct account balance is returned
    assert c.functions.getAccountBalance(incor).call() == 0, 'Unregistered username returns 0 balance'


def test_get_account_balance_correct_label(accounts, registrar_deploy, w3):
    '''
    Tests getAccountBalance() for an existing label
    '''

    # Deploy
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    # Account and Label
    chosen_account = accounts[1]
    label = w3.sha3(text='somethinglong')

    # Activate
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    # Register account to label
    c.functions.register(
        label,
        chosen_account,
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    # Check the correct account balance is returned
    expected_balance = 1e2
    assert c.functions.getAccountBalance(label).call() == expected_balance, "Correct balance returned"


################################################################################
# getAccountOwner
################################################################################


def test_get_account_owner_incorrect(accounts, registrar_deploy, w3, variables):
    '''
    Tests getAccountOwner() for an incorrect label
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    # Account and Label
    chosen_account = accounts[1]
    label = w3.sha3(text='somethinglong')
    incor = w3.sha3(text='thiswrongone')

    # Activate
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})
    # Transfer
    token_c.functions.transfer(accounts[2], w3.toInt(10e3)).transact({'from': accounts[0]})
    token_c.functions.approve(accounts[2], w3.toInt(10e6)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[2]})

    # Register account to label
    c.functions.register(
        label,
        chosen_account,
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    # Check the correct owner is returned
    assert c.functions.getAccountOwner(incor).call() == variables['zero_address'], "Non-existing label returned expected behaviour for account owner"

    # Register second label
    c.functions.register(
        incor,
        chosen_account,
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[2]})

    # Owner returns correctly
    assert c.functions.getAccountOwner(incor).call() != accounts[1], "Label returned unexpected account"
    assert c.functions.getAccountOwner(incor).call() == accounts[2], "Label returned unexpected account"


def test_get_account_owner_correct_label(accounts, registrar_deploy, w3):
    '''
    Tests getAccountOwner() for an existing label
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    # Account and Label
    chosen_account = accounts[1]
    label = w3.sha3(text='somethinglong')

    # Activate
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})
    token_c.functions.transfer(chosen_account, w3.toInt(2e3)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': chosen_account})

    # Register
    c.functions.register(
        label,
        chosen_account,
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': chosen_account})

    # Check the correct account Owner
    assert c.functions.getAccountOwner(label).call() == chosen_account, "Correct owner returned"


################################################################################
# getCreationTime
################################################################################


def test_get_creation_time_incorrect(accounts, registrar_deploy, w3, block_timestamp, get_receipt):
    '''
    Test getCreationTime() for incorrect label
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    # Account and Label
    chosen_account = accounts[1]
    label = w3.sha3(text='somethinglong')

    # Activate
    new_price = 0
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})
    token_c.functions.transfer(chosen_account, w3.toInt(2e3)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': chosen_account})

    # Register
    tx = c.functions.register(
        label,
        chosen_account,
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': chosen_account})
    stamp = block_timestamp(get_receipt(tx)['blockNumber'])

    # Check the correct creation time
    assert c.functions.getCreationTime(w3.sha3(text='helloworld')).call() != stamp, "Non-existing label returned expected behaviour for creation time"
    assert c.functions.getCreationTime(w3.sha3(text='helloworld')).call() == 0, "Non-existing label returned expected behaviour for creation time"


def test_get_creation_time_correct(accounts, registrar_deploy, w3, block_timestamp, get_receipt):
    '''
    Tests getCreationTime() for an existing label
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    # Account and Label
    chosen_account = accounts[1]
    label = w3.sha3(text='somethinglong')

    # Activate
    new_price = 0
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})
    token_c.functions.transfer(chosen_account, w3.toInt(2e3)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': chosen_account})

    # Register
    tx = c.functions.register(
        label,
        chosen_account,
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': chosen_account})
    expected = block_timestamp(get_receipt(tx)['blockNumber'])

    # Check the correct creation time
    assert c.functions.getCreationTime(label).call() == expected, "Existing label returned unexpected behaviour for creation time"


################################################################################
# getExpirationTime
################################################################################


def test_get_expiration_time_incorrect(accounts, registrar_deploy, w3, days):
    '''
    Test getExpirationTime() for incorrect label
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    # Account and Label
    chosen_account = accounts[1]
    label = w3.sha3(text='somethinglong')

    # Activate
    new_price = 0
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})
    token_c.functions.transfer(chosen_account, w3.toInt(2e3)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': chosen_account})

    # Register
    c.functions.register(
        label,
        chosen_account,
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': chosen_account})

    # Check the correct creation time
    assert c.functions.getReleaseTime(w3.sha3(text='helloworld')).call() == 0, "Non-existing label returned unexpected behaviour for expiration time"


def test_get_expiration_time_correct(accounts, registrar_deploy, w3, days, block_timestamp, get_receipt):
    '''
    Tests getExpirationTime() for an existing label
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    # Account and Label
    chosen_account = accounts[1]
    label = w3.sha3(text='somethinglong')

    # Activate
    new_price = 0
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})
    token_c.functions.transfer(chosen_account, w3.toInt(2e3)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': chosen_account})

    # Register
    tx = c.functions.register(
        label,
        chosen_account,
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': chosen_account})
    expected = block_timestamp(get_receipt(tx)['blockNumber']) + days(365)

    # Check the correct account balance is returned
    assert c.functions.getReleaseTime(label).call() == expected, "Correct expiration time returned"

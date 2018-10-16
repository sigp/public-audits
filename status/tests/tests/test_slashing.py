################################################################################
# slashAddressLikeUsername()
################################################################################


def test_slash_address_like_username_unowned(accounts, registrar_deploy, w3, assert_tx_failed):
    '''
    Tests slashAddressLikeUsername of 0 owned address
    '''

    # Deploy Contract
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    uname = 'unowned'

    assert_tx_failed(c.functions.slashAddressLikeUsername(uname), {'from': accounts[0]})


def test_slash_address_like_username_usernameok(accounts, registrar_deploy, w3, assert_tx_failed):
    '''
    Tests slashAddressLikeUsername with length less than 12
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    # TODO register name
    uname = 'nottwelve'
    label = w3.sha3(text=uname)

    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    assert_tx_failed(c.functions.slashAddressLikeUsername(uname), {'from': accounts[0]})


def test_slash_address_like_username_startwithO(accounts, registrar_deploy, w3, assert_tx_failed):
    '''
    Tests slashAddressLikeUsername that starts wtih O instead of zero
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    uname = 'OxA11BABA'
    label = w3.sha3(text=uname)

    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    assert_tx_failed(c.functions.slashAddressLikeUsername(uname), {'from': accounts[0]})


def test_slash_address_like_username_capitalX(accounts, registrar_deploy, w3, assert_tx_failed):
    '''
    Tests slashAddressLikeUsername has capital X (case sensitivity)
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    uname = '0X1DEA70078'
    label = w3.sha3(text=uname)

    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    assert_tx_failed(c.functions.slashAddressLikeUsername(uname), {'from': accounts[0]})


def test_slash_address_like_username_0xnotaddress(accounts, registrar_deploy, w3, get_logs_for_event, variables):
    '''
    Test slashAddressLikeUsername username starting with 0x and > 12.
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    uname = '0xthisisnotanaddress'
    label = w3.sha3(text=uname)

    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    # Ensure the owner is currently account 0
    assert c.functions.getAccountOwner(label).call() == accounts[0], "Owner not associated"

    tx_event = get_logs_for_event(c.events.UsernameOwner, c.functions.slashAddressLikeUsername(uname).transact({'from': accounts[1]}))
    namehash = w3.soliditySha3(['bytes32', 'bytes32'], [c.functions.ensNode().call(), label]).hex()
    # Make sure it slashed
    assert '0x' + tx_event[0]['args']['nameHash'].hex() == namehash


def test_slash_address_like_username_isaddress(accounts, registrar_deploy, w3, get_logs_for_event):
    '''
    Test slashAddressLikeUsername username starting with 0x and > 12.
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})
    uname = '0x744d70fdbe2ba4cf95131626614a1763df805b9e'
    label = w3.sha3(text=uname)

    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    tx_event = get_logs_for_event(c.events.UsernameOwner, c.functions.slashAddressLikeUsername(uname).transact({'from': accounts[1]}))
    namehash = w3.soliditySha3(['bytes32', 'bytes32'], [c.functions.ensNode().call(), label]).hex()

    assert '0x' + tx_event[0]['args']['nameHash'].hex() == namehash, "Incorrect name slashed"


################################################################################
# slashInvalidUsername()
################################################################################


def test_slash_invalid_username_notinvalid(accounts, registrar_deploy, w3, assert_tx_failed):
    '''
    Test slashInvalidUsername on a valid username
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    uname = 'validname'
    label = w3.sha3(text=uname)

    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    assert_tx_failed(c.functions.slashInvalidUsername(bytes(uname, 'utf8'), w3.toInt(2)), {'from': accounts[0]})


def test_slash_invalid_username_invalid(accounts, registrar_deploy, w3, get_logs_for_event):
    '''
    Test slashInvalidUsername on a valid username
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    uname = 'mystΞry♦'
    label = w3.sha3(text=uname)

    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    tx_event = get_logs_for_event(c.events.UsernameOwner, c.functions.slashInvalidUsername(bytes(uname, 'utf8'), 4).transact({'from': accounts[1]}))
    namehash = w3.soliditySha3(['bytes32', 'bytes32'], [c.functions.ensNode().call(), label]).hex()

    assert '0x' + tx_event[0]['args']['nameHash'].hex() == namehash, "Incorrect name slashed"


################################################################################
# slashReservedUsername()
################################################################################

def test_slash_reserved_username_empty_reserved(accounts, registrar_deploy, w3, assert_tx_failed):
    '''
    Test slashReservedUsername with no reserved names
    '''

    # Create the tree
    left = 'validname'
    right = 'randomname'
    label_right = w3.soliditySha3(['string'], [right])
    label_left = w3.soliditySha3(['string'], [left])

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    c.functions.register(
        label_left,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    assert_tx_failed(c.functions.slashReservedUsername(bytes(left, 'utf8'), [label_right]), {'from': accounts[0]})


def test_slash_reserved_username_empty_proof(accounts, registrar_deploy, w3, assert_tx_failed):
    '''
    Test slashReservedUsername with an empty proof
    '''

    # Create the tree
    left = 'validname'
    right = 'randomname'
    label_right = w3.soliditySha3(['string'], [right])
    label_left = w3.soliditySha3(['string'], [left])
    root = w3.soliditySha3(['bytes32', 'bytes32'], [label_left, label_right])

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy(
        reserved_merkle_root=root
    )
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    c.functions.register(
        label_left,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    assert_tx_failed(c.functions.slashReservedUsername(bytes(left, 'utf8'), []), {'from': accounts[0]})


def test_slash_reserved_username_wrong_proof(accounts, registrar_deploy, w3, assert_tx_failed):
    '''
    Test slashReservedUsername with an incorrect proof
    '''

    # Create the tree
    left = 'validname'
    right = 'randomname'
    label_right = w3.soliditySha3(['string'], [right])
    label_left = w3.soliditySha3(['string'], [left])
    root = w3.soliditySha3(['bytes32', 'bytes32'], [label_left, label_right])

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy(
        reserved_merkle_root=root
    )
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    c.functions.register(
        label_left,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    assert_tx_failed(c.functions.slashReservedUsername(bytes(left, 'utf8'), [label_left]), {'from': accounts[0]})


def test_slash_reserved_username_upper(accounts, registrar_deploy, w3, assert_tx_failed):
    '''
    Test slashReservedUsername on an upper-case reserved name
    '''

    # Create the tree
    left = 'validname'
    right = 'randomname'
    label_right = w3.soliditySha3(['string'], [right])
    label_left = w3.soliditySha3(['string'], [left])
    root = w3.soliditySha3(['bytes32', 'bytes32'], [label_left, label_right])

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy(
        reserved_merkle_root=root
    )
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    c.functions.register(
        label_left,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    assert_tx_failed(c.functions.slashReservedUsername(bytes(left.upper(), 'utf8'), [label_right]), {'from': accounts[0]})


def test_slash_reserved_username_reserved_correct(accounts, registrar_deploy, w3, get_logs_for_event):
    '''
    Test slashReservedUsername on a valid username
    '''

    # Create the tree
    left = 'validname'
    right = 'randomname'
    label_right = w3.soliditySha3(['string'], [right])
    label_left = w3.soliditySha3(['string'], [left])
    root = w3.soliditySha3(['bytes32', 'bytes32'], [label_left, label_right])

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy(
        reserved_merkle_root=root
    )
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    c.functions.register(
        label_left,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    tx_event = get_logs_for_event(c.events.UsernameOwner, c.functions.slashReservedUsername(bytes(left, 'utf8'), [label_right]).transact({'from': accounts[1]}))
    namehash = w3.soliditySha3(['bytes32', 'bytes32'], [c.functions.ensNode().call(), label_left]).hex()

    assert '0x' + tx_event[0]['args']['nameHash'].hex() == namehash, "Incorrect name slashed"


################################################################################
# slashSmallUsername()
################################################################################


def test_slash_small_username_notsmall(accounts, registrar_deploy, w3, assert_tx_failed):
    '''
    Test slashSmallUsername() with a large username
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    uname = 'iamavalidname'
    label = w3.sha3(text=uname)

    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    assert_tx_failed(
        c.functions.slashSmallUsername(bytes(uname, 'utf8')),
        {'from': accounts[0]}
    )


def test_slash_small_username_exact(accounts, registrar_deploy, w3, assert_tx_failed):
    '''
    Test slashSmallUsername() with exact length username
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    uname = 'a' * 10
    label = w3.sha3(text=uname)

    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    assert_tx_failed(
        c.functions.slashSmallUsername(bytes(uname, 'utf8')),
        {'from': accounts[0]}
    )


def test_slash_small_username_small(accounts, registrar_deploy, w3, get_logs_for_event):
    '''
    Test slashSmallUsername() with small username (should get slashed)
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    uname = 'a' * 3
    label = w3.sha3(text=uname)

    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    tx_event = get_logs_for_event(
        c.events.UsernameOwner,
        c.functions.slashSmallUsername(bytes(uname, 'utf8'))
        .transact({'from': accounts[1]})
    )
    namehash = w3.soliditySha3(
        ['bytes32', 'bytes32'],
        [c.functions.ensNode().call(), label]
    ).hex()

    assert '0x' + tx_event[0]['args']['nameHash'].hex() == namehash, "Incorrect name slashed"

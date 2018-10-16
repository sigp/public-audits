################################################################################
# slashAddressLikeUsername()
################################################################################


def test_slash_address_with_no_reserve(accounts, registrar_deploy, w3, assert_tx_failed):
    '''
    Tests slashAddressLikeUsername without reserving the slashing
    '''

    # Deploy Contract
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    uname = '0x12345678945126'
    secret = 1e2
    assert_tx_failed(c.functions.slashAddressLikeUsername(uname, w3.toInt(secret)), {'from': accounts[0]})


def test_slash_address_like_username_usernameok(accounts, registrar_deploy, w3,
        assert_tx_failed, ganache_increase_time):
    '''
    Tests slashAddressLikeUsername with length less than 12
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    # TODO register name
    uname = '0x1234578945126abcde'
    secret = 15
    label = w3.sha3(text=uname)
    zero_address = "0x" + "00"*20
    namehash = w3.soliditySha3(['bytes32', 'bytes32'], [ens_node, label])

    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    reserve_slash = w3.soliditySha3(['bytes32','uint256', 'uint256'], [namehash, c.functions.getCreationTime(label).call(), secret])
    c.functions.reserveSlash(reserve_slash).transact({'from': accounts[1]})
    ganache_increase_time(1000)
    c.functions.slashAddressLikeUsername(uname, w3.toInt(secret)).transact({'from': accounts[1]})
    assert c.functions.getAccountOwner(label).call() == zero_address, "Accounts 0 was not slashed !"



def test_slash_address_like_username_startwithO(accounts, registrar_deploy, w3, assert_tx_failed, ganache_increase_time):
    '''
    Tests slashAddressLikeUsername that starts wtih O instead of zero
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    zero_address = "0x" + "00"*20
    uname = 'Ox1234567894565'
    label = w3.sha3(text=uname)
    secret = 123
    namehash = w3.soliditySha3(['bytes32', 'bytes32'], [ens_node, label])

    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    reserve_slash = w3.soliditySha3(['bytes32','uint256', 'uint256'], [namehash, c.functions.getCreationTime(label).call(), secret])

    c.functions.reserveSlash(reserve_slash).transact({'from': accounts[1]})
    ganache_increase_time(1000)
    assert_tx_failed(c.functions.slashAddressLikeUsername(uname, secret), {'from': accounts[1]})


def test_slash_address_like_username_capitalX(accounts, registrar_deploy, w3, assert_tx_failed, ganache_increase_time):
    '''
    Tests slashAddressLikeUsername has capital X (case sensitivity)
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    zero_address = "0x" + "00"*20
    uname = '0X1DEA70078'
    label = w3.sha3(text=uname)
    secret = 1337
    namehash = w3.soliditySha3(['bytes32', 'bytes32'], [ens_node, label])

    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    reserve_slash = w3.soliditySha3(['bytes32','uint256', 'uint256'], [namehash, c.functions.getCreationTime(label).call(), secret])
    c.functions.reserveSlash(reserve_slash).transact({'from': accounts[1]})
    ganache_increase_time(1000)
    assert_tx_failed(c.functions.slashAddressLikeUsername(uname, secret), {'from': accounts[1]})


def test_slash_address_like_username_0xnotaddress(accounts, registrar_deploy, w3, get_logs_for_event, variables, assert_tx_failed, ganache_increase_time):
    '''
    Test slashAddressLikeUsername username starting with 0x and > 12.
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    zero_address = "0x" + "00"*20
    uname = '0xthisisnotanaddress'
    label = w3.sha3(text=uname)
    secret = 13371337
    namehash = w3.soliditySha3(['bytes32', 'bytes32'], [ens_node, label])

    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    reserve_slash = w3.soliditySha3(['bytes32','uint256', 'uint256'], [namehash, c.functions.getCreationTime(label).call(), secret])

    c.functions.reserveSlash(reserve_slash).transact({'from': accounts[1]})
    ganache_increase_time(1000)

    # Ensure the owner is currently account 0
    assert c.functions.getAccountOwner(label).call() == accounts[0], "Owner not associated"

    assert_tx_failed(c.functions.slashAddressLikeUsername(uname, secret), {'from': accounts[1]})



def test_slash_address_like_username_isaddress(accounts, registrar_deploy, w3, get_logs_for_event, ganache_increase_time):
    '''
    Test slashAddressLikeUsername username starting with 0x and > 12.
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    zero_address = "0x" + "00"*20
    uname = '0x744d70fdbe2ba4cf95131626614a1763df805b9e'
    label = w3.sha3(text=uname)
    secret = 13371337
    namehash = w3.soliditySha3(['bytes32', 'bytes32'], [ens_node, label])

    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    reserve_slash = w3.soliditySha3(['bytes32','uint256', 'uint256'], [namehash, c.functions.getCreationTime(label).call(), secret])

    c.functions.reserveSlash(reserve_slash).transact({'from': accounts[1]})

    ganache_increase_time(1000)

    c.functions.slashAddressLikeUsername(uname, w3.toInt(secret)).transact({'from': accounts[1]})

    assert c.functions.getAccountOwner(label).call() == zero_address


################################################################################
# slashInvalidUsername()
################################################################################


def test_slash_invalid_username_notinvalid(accounts, registrar_deploy, w3, assert_tx_failed, ganache_increase_time):
    '''
    Test slashInvalidUsername on a valid username
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    zero_address = "0x" + "00"*20
    uname = 'avalidname'
    label = w3.sha3(text=uname)
    secret = 133713371337
    namehash = w3.soliditySha3(['bytes32', 'bytes32'], [ens_node, label])

    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    reserve_slash = w3.soliditySha3(['bytes32','uint256', 'uint256'], [namehash, c.functions.getCreationTime(label).call(), secret])

    c.functions.reserveSlash(reserve_slash).transact({'from': accounts[1]})

    ganache_increase_time(1000)

    assert_tx_failed(c.functions.slashAddressLikeUsername(uname, secret), {'from': accounts[1]})


def test_slash_invalid_username_invalid(accounts, registrar_deploy, w3, get_logs_for_event, ganache_increase_time):
    '''
    Test slashInvalidUsername on a valid username
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    zero_address = "0x" + "00"*20
    uname = 'mystΞry♦'
    label = w3.sha3(text=uname)
    secret = 133713371337
    namehash = w3.soliditySha3(['bytes32', 'bytes32'], [ens_node, label])

    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    reserve_slash = w3.soliditySha3(['bytes32','uint256', 'uint256'], [namehash, c.functions.getCreationTime(label).call(), secret])

    c.functions.reserveSlash(reserve_slash).transact({'from': accounts[1]})
    ganache_increase_time(1000)
    c.functions.slashInvalidUsername(uname, 4, w3.toInt(secret)).transact({'from': accounts[1]})
    assert c.functions.getAccountOwner(label).call() == zero_address, "Invalid username not slashed"


#
#
# ################################################################################
# # slashReservedUsername()
# ################################################################################
#
def test_slash_reserved_username_empty_reserved(accounts, registrar_deploy, w3,
        assert_tx_failed, ganache_increase_time):
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
    c.functions.activate(0).transact({'from': accounts[0]})

    secret = 15
    namehash = w3.soliditySha3(['bytes32', 'bytes32'], [ens_node, label_left])

    c.functions.register(
        label_left,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    reserve_slash = w3.soliditySha3(['bytes32','uint256', 'uint256'], [namehash,
            c.functions.getCreationTime(label_left).call(), secret])
    c.functions.reserveSlash(reserve_slash).transact({'from': accounts[1]})
    ganache_increase_time(1000)

    assert_tx_failed(c.functions.slashReservedUsername(left, [], secret), {'from': accounts[0]})


def test_slash_reserved_username_empty_proof(accounts, registrar_deploy, w3,
        assert_tx_failed, ganache_increase_time):
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
    c.functions.activate(0).transact({'from': accounts[0]})

    c.functions.register(
        label_left,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    secret = 15
    namehash = w3.soliditySha3(['bytes32', 'bytes32'], [ens_node, label_left])
    reserve_slash = w3.soliditySha3(['bytes32','uint256', 'uint256'], [namehash,
            c.functions.getCreationTime(label_left).call(), secret])
    c.functions.reserveSlash(reserve_slash).transact({'from': accounts[1]})
    ganache_increase_time(1000)

    assert_tx_failed(c.functions.slashReservedUsername(left, [], secret), {'from': accounts[0]})


def test_slash_reserved_username_wrong_proof(accounts, registrar_deploy, w3,
        assert_tx_failed, ganache_increase_time):
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
    c.functions.activate(0).transact({'from': accounts[0]})

    c.functions.register(
        label_left,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    secret = 15
    namehash = w3.soliditySha3(['bytes32', 'bytes32'], [ens_node, label_left])
    reserve_slash = w3.soliditySha3(['bytes32','uint256', 'uint256'], [namehash,
            c.functions.getCreationTime(label_left).call(), secret])
    c.functions.reserveSlash(reserve_slash).transact({'from': accounts[1]})
    ganache_increase_time(1000)

    assert_tx_failed(c.functions.slashReservedUsername(left, [label_left], secret), {'from': accounts[0]})

def test_slash_reserved_username_upper(accounts, registrar_deploy, w3,
        assert_tx_failed, ganache_increase_time):
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

    secret = 15
    namehash = w3.soliditySha3(['bytes32', 'bytes32'], [ens_node, label_left])
    reserve_slash = w3.soliditySha3(['bytes32','uint256', 'uint256'], [namehash,
            c.functions.getCreationTime(label_left).call(), secret])
    c.functions.reserveSlash(reserve_slash).transact({'from': accounts[1]})
    ganache_increase_time(1000)

    assert_tx_failed(c.functions.slashReservedUsername(left.upper(), [label_right], secret), {'from': accounts[0]})

def test_slash_reserved_username_reserved_correct(accounts, registrar_deploy,
        w3, get_logs_for_event, ganache_increase_time):
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

    secret = 15
    namehash = w3.soliditySha3(['bytes32', 'bytes32'], [ens_node, label_left])
    reserve_slash = w3.soliditySha3(['bytes32','uint256', 'uint256'], [namehash,
            c.functions.getCreationTime(label_left).call(), secret])
    c.functions.reserveSlash(reserve_slash).transact({'from': accounts[1]})
    ganache_increase_time(1000)

    tx_event = get_logs_for_event(c.events.UsernameOwner,
            c.functions.slashReservedUsername(left, [label_right], secret).transact({'from': accounts[1]}))
    namehash = w3.soliditySha3(['bytes32', 'bytes32'], [c.functions.ensNode().call(), label_left]).hex()

    assert '0x' + tx_event[0]['args']['nameHash'].hex() == namehash, "Incorrect name slashed"


# ################################################################################
# # slashSmallUsername()
# ################################################################################


def test_slash_small_username_notsmall(accounts, registrar_deploy, w3,
        assert_tx_failed, ganache_increase_time):
    '''
    Test slashSmallUsername() with a large username
    '''
    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    c.functions.activate(0).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    uname = "thisisavalidname"
    label = w3.sha3(text=uname)
    secret = 15
    zero_address = "0x" + "00"*20
    namehash = w3.soliditySha3(['bytes32', 'bytes32'], [ens_node, label])

    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    reserve_slash = w3.soliditySha3(['bytes32','uint256', 'uint256'], [namehash, c.functions.getCreationTime(label).call(), secret])
    c.functions.reserveSlash(reserve_slash).transact({'from': accounts[1]})
    ganache_increase_time(1000)

    assert_tx_failed(
        c.functions.slashSmallUsername(uname, secret),
        {'from': accounts[0]}
    )


def test_slash_small_username_exact(accounts, registrar_deploy, w3,
        assert_tx_failed, ganache_increase_time):
    '''
    Test slashSmallUsername() with exact length username
    '''

    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    c.functions.activate(0).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    uname = "a" * 10
    label = w3.sha3(text=uname)
    secret = 15
    zero_address = "0x" + "00"*20
    namehash = w3.soliditySha3(['bytes32', 'bytes32'], [ens_node, label])

    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    reserve_slash = w3.soliditySha3(['bytes32','uint256', 'uint256'], [namehash, c.functions.getCreationTime(label).call(), secret])
    c.functions.reserveSlash(reserve_slash).transact({'from': accounts[1]})
    ganache_increase_time(1000)

    assert_tx_failed(
        c.functions.slashSmallUsername(uname, secret),
        {'from': accounts[0]}
    )


def test_slash_small_username_small(accounts, registrar_deploy, w3,
        get_logs_for_event, ganache_increase_time):
    '''
    Test slashSmallUsername() with small username (should get slashed)
    '''
    # Initialize
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    c.functions.activate(0).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    uname = "a" * 3
    label = w3.sha3(text=uname)
    secret = 15
    zero_address = "0x" + "00"*20
    namehash = w3.soliditySha3(['bytes32', 'bytes32'], [ens_node, label])

    c.functions.register(
        label,
        accounts[0],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[0]})

    reserve_slash = w3.soliditySha3(['bytes32','uint256', 'uint256'], [namehash, c.functions.getCreationTime(label).call(), secret])
    c.functions.reserveSlash(reserve_slash).transact({'from': accounts[1]})
    ganache_increase_time(1000)

    tx_event = get_logs_for_event(
         c.events.UsernameOwner,
         c.functions.slashSmallUsername(uname, secret).transact({'from': accounts[1]}))

    assert '0x' + tx_event[0]['args']['nameHash'].hex() == namehash.hex(), "Incorrect name slashed"

    assert c.functions.getAccountOwner(label).call() == zero_address, "Accounts 0 was not slashed !"

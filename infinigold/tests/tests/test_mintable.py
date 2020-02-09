### Tests valid operations for setting, increasing, decreasing and removing minter limits
def test_minter_limit(
        accounts,
        token_proxy_initialize_and_deploy,
        get_logs_for_event):

    (token_proxy_as_impl, token_proxy) = token_proxy_initialize_and_deploy("Infinigold", "IFG", 2)

    # account[1] as MinterAdmin, accounts[2] as Minter
    token_proxy_as_impl.functions.addMinterAdmin(accounts[1]).transact({'from': accounts[0]})
    token_proxy_as_impl.functions.addMintLimiterAdmin(accounts[1]).transact({'from': accounts[0]})
    token_proxy_as_impl.functions.addMintLimiter(accounts[1]).transact({'from': accounts[1]})
    token_proxy_as_impl.functions.addMinter(accounts[2]).transact({'from': accounts[1]})

    # Set limit for accounts[2] to 1,000
    tx = token_proxy_as_impl.functions.setMintLimit(accounts[2], 1000).transact({'from': accounts[1]})
    assert token_proxy_as_impl.functions.mintLimitOf(accounts[2]).call() == 1000
    logs = get_logs_for_event(token_proxy_as_impl.events.MinterLimitUpdated, tx)
    assert logs[0]['args']['minter'] == accounts[2]
    assert logs[0]['args']['limit'] == 1000

    # Set limit for accounts[2] to 0
    tx = token_proxy_as_impl.functions.setMintLimit(accounts[2], 0).transact({'from': accounts[1]})
    assert token_proxy_as_impl.functions.mintLimitOf(accounts[2]).call() == 0
    logs = get_logs_for_event(token_proxy_as_impl.events.MinterLimitUpdated, tx)
    assert logs[0]['args']['minter'] == accounts[2]
    assert logs[0]['args']['limit'] == 0

    # Increase limit for accounts[2] to 2,000
    tx = token_proxy_as_impl.functions.increaseMintLimit(accounts[2], 2000).transact({'from': accounts[1]})
    assert token_proxy_as_impl.functions.mintLimitOf(accounts[2]).call() == 2000
    logs = get_logs_for_event(token_proxy_as_impl.events.MinterLimitUpdated, tx)
    assert logs[0]['args']['minter'] == accounts[2]
    assert logs[0]['args']['limit'] == 2000

    # Decrease limit for accounts[2] by 500 to 1,500
    tx = token_proxy_as_impl.functions.decreaseMintLimit(accounts[2], 500).transact({'from': accounts[1]})
    assert token_proxy_as_impl.functions.mintLimitOf(accounts[2]).call() == 1500
    logs = get_logs_for_event(token_proxy_as_impl.events.MinterLimitUpdated, tx)
    assert logs[0]['args']['minter'] == accounts[2]
    assert logs[0]['args']['limit'] == 1500

    # Remove accounts[2] as minter
    tx = token_proxy_as_impl.functions.removeMinter(accounts[2]).transact({'from': accounts[1]})
    assert token_proxy_as_impl.functions.mintLimitOf(accounts[2]).call() == 0
    logs = get_logs_for_event(token_proxy_as_impl.events.MinterLimitUpdated, tx)
    assert logs[0]['args']['minter'] == accounts[2]
    assert logs[0]['args']['limit'] == 0

### Tests invalid operations for setting, increasing, decreasing and removing minter limits
def test_minter_limit_invalid(
        accounts,
        token_proxy_initialize_and_deploy,
        assert_tx_failed,
        get_logs_for_event):

    (token_proxy_as_impl, token_proxy) = token_proxy_initialize_and_deploy("Infinigold", "IFG", 2)

    # account[1] as MinterAdmin, accounts[2] as Minter
    token_proxy_as_impl.functions.addMinterAdmin(accounts[1]).transact({'from': accounts[0]})
    token_proxy_as_impl.functions.addMintLimiterAdmin(accounts[1]).transact({'from': accounts[0]})
    token_proxy_as_impl.functions.addMintLimiter(accounts[1]).transact({'from': accounts[1]})
    token_proxy_as_impl.functions.addMinter(accounts[2]).transact({'from': accounts[1]})

    # Underflow in decreaseMintLimit
    assert_tx_failed(token_proxy_as_impl.functions.decreaseMintLimit(accounts[2], 50), {'from': accounts[1]})
    token_proxy_as_impl.functions.addMinter(accounts[4]).transact({'from': accounts[1]})
    token_proxy_as_impl.functions.setMintLimit(accounts[4], 49).transact({'from': accounts[1]})
    assert_tx_failed(token_proxy_as_impl.functions.decreaseMintLimit(accounts[4], 50), {'from': accounts[1]})

    # Overflow in increaseMintLimit
    max_uint256 = 2**256 - 1
    token_proxy_as_impl.functions.increaseMintLimit(accounts[2], max_uint256).transact({'from': accounts[1]})
    assert_tx_failed(token_proxy_as_impl.functions.increaseMintLimit(accounts[2], 1), {'from': accounts[1]})
    assert_tx_failed(token_proxy_as_impl.functions.increaseMintLimit(accounts[2], max_uint256), {'from': accounts[1]})

    # Owner is not MinterAdmin
    assert_tx_failed(token_proxy_as_impl.functions.addMinter(accounts[3]), {'from': accounts[0]})
    assert_tx_failed(token_proxy_as_impl.functions.removeMinter(accounts[3]), {'from': accounts[0]})
    assert_tx_failed(token_proxy_as_impl.functions.decreaseMintLimit(accounts[3], 50), {'from': accounts[0]})
    assert_tx_failed(token_proxy_as_impl.functions.increaseMintLimit(accounts[3], 1000), {'from': accounts[0]})
    assert_tx_failed(token_proxy_as_impl.functions.setMintLimit(accounts[3], 1250), {'from': accounts[0]})

    # Minter is not MinterAdmin
    assert_tx_failed(token_proxy_as_impl.functions.addMinter(accounts[2]), {'from': accounts[2]})
    assert_tx_failed(token_proxy_as_impl.functions.removeMinter(accounts[2]), {'from': accounts[2]})
    assert_tx_failed(token_proxy_as_impl.functions.decreaseMintLimit(accounts[2], 50), {'from': accounts[2]})
    assert_tx_failed(token_proxy_as_impl.functions.increaseMintLimit(accounts[2], 1000), {'from': accounts[2]})
    assert_tx_failed(token_proxy_as_impl.functions.setMintLimit(accounts[2], 1250), {'from': accounts[2]})

### Tests valid mint calls directly on TokenImpl
def test_mint(
        accounts,
        get_logs_for_event,
        set_minter_with_limit,
        token_proxy_initialize_and_deploy,
        zero_address):

    (token_proxy_as_impl, token_proxy) = token_proxy_initialize_and_deploy("Infinigold", "IFG", 2)

    # account[1] as MinterAdmin, accounts[2] as Minter with limit 1,000
    set_minter_with_limit(token_proxy_as_impl, 1000)

    # Mint 50 tokens to account[3]
    tx = token_proxy_as_impl.functions.mint(accounts[3], 50, 1).transact({'from': accounts[2]})
    assert token_proxy_as_impl.functions.balanceOf(accounts[3]).call() == 50
    assert token_proxy_as_impl.functions.totalSupply().call() == 50
    assert token_proxy_as_impl.functions.mintLimitOf(accounts[2]).call() == 950
    # ERC20.sol and Minter.sol Logs
    logs = get_logs_for_event(token_proxy_as_impl.events.Transfer, tx)
    assert logs[0]['args']['from'] == zero_address
    assert logs[0]['args']['to'] == accounts[3]
    assert logs[0]['args']['value'] == 50
    logs = get_logs_for_event(token_proxy_as_impl.events.Mint, tx)
    assert logs[0]['args']['minter'] == accounts[2]
    assert logs[0]['args']['to'] == accounts[3]
    assert logs[0]['args']['value'] == 50
    assert logs[0]['args']['mintId'] == 1

    # Mint remaining balance
    tx = token_proxy_as_impl.functions.mint(accounts[3], 950, 2).transact({'from': accounts[2]})
    assert token_proxy_as_impl.functions.balanceOf(accounts[3]).call() == 1000
    assert token_proxy_as_impl.functions.totalSupply().call() == 1000
    assert token_proxy_as_impl.functions.mintLimitOf(accounts[2]).call() == 0
    # ERC20.sol and Minter.sol Logs
    logs = get_logs_for_event(token_proxy_as_impl.events.Transfer, tx)
    assert logs[0]['args']['from'] == zero_address
    assert logs[0]['args']['to'] == accounts[3]
    assert logs[0]['args']['value'] == 950
    logs = get_logs_for_event(token_proxy_as_impl.events.Mint, tx)
    assert logs[0]['args']['minter'] == accounts[2]
    assert logs[0]['args']['to'] == accounts[3]
    assert logs[0]['args']['value'] == 950
    assert logs[0]['args']['mintId'] == 2

### Tests invalid mint calls directly on TokenImpl
def test_mint_invalid(
        accounts,
        assert_tx_failed,
        get_logs_for_event,
        set_minter_with_limit,
        token_proxy_initialize_and_deploy,
        zero_address):

    (token_proxy_as_impl, token_proxy) = token_proxy_initialize_and_deploy("Infinigold", "IFG", 2)

    # account[1] as MinterAdmin, accounts[2] as Minter with limit 1,000
    set_minter_with_limit(token_proxy_as_impl, 1000)

    # Not a Minter
    assert_tx_failed(token_proxy_as_impl.functions.mint(accounts[4], 100, 1), {'from':accounts[1]})
    assert_tx_failed(token_proxy_as_impl.functions.mint(accounts[4], 100, 2), {'from':accounts[3]})

    # Not enough balance
    assert_tx_failed(token_proxy_as_impl.functions.mint(accounts[4], 2000, 3), {'from':accounts[2]})
    assert_tx_failed(token_proxy_as_impl.functions.mint(zero_address, 2000, 4), {'from':accounts[2]})

    # Minter with no balance
    token_proxy_as_impl.functions.addMinter(accounts[5]).transact({'from': accounts[1]})
    assert_tx_failed(token_proxy_as_impl.functions.mint(accounts[4], 50, 5), {'from':accounts[5]})

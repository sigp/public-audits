################################################################################
# migrateDomain()
################################################################################

def test_migration_transfer_ownership(accounts, registrar_deploy, w3, assert_tx_failed):
    '''
    Tests Registrar Ownership Transfer:
    '''
    # Deploy Contracts

    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    (c2, r2, token_c2, ens_c2, resolver_c2, ens_node2) = registrar_deploy(parent_registry=c.address, ens_contract=ens_c, resolver_contract=resolver_c)

    init_price = 10
    erc_amount = 100

    # transfer tokens to the registry
    token_c.functions.transfer(c.address, w3.toInt(erc_amount)).transact({'from': accounts[0]})
    # Activate the first registry
    c.functions.activate(init_price).transact({'from': accounts[0]})
    # Move registrar from c to c2
    c.functions.moveRegistry(c2.address).transact({'from': accounts[0]})
    # Assert old registrar is moved
    assert c.functions.state().call() == 2, "Old Registrar is now moved"
    # Assert new registrar is Active
    assert c2.functions.state().call() == 1, "New Registrar still Inactive"


def test_user_migration_after_registrar_transfer(accounts, registrar_deploy, w3, assert_tx_failed, register_accounts, sha3):
    # Deploy Registrar contract #1
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    init_price = 10

    # Activate the first registry
    c.functions.activate(init_price).transact({'from': accounts[0]})

    # Register 10 accounts
    register_accounts(c, token_c)
    # Deploy Registrar contract #2 - with the same token contract as #1
    (c2, r2, token_c2, ens_c2, resolver_c2, ens_node2) = registrar_deploy(parent_registry=c.address, token_contract=token_c, ens_contract=ens_c, resolver_contract=resolver_c)

    erc_amount = 100
    zero_address = "0x" + "00"*20

    # transfer tokens to the registry
    token_c.functions.transfer(c.address, w3.toInt(erc_amount)).transact({'from': accounts[0]})

    # Assert adequate Registration
    for i in range(10):
        label = sha3(['string'], ["name" + str(i)])
        assert c.functions.getAccountOwner(label).call() == accounts[i], "Wrong owner"

    # Move registrar from c to c2
    c.functions.moveRegistry(c2.address).transact({'from': accounts[0]})
    # Assert Registrar has been moved
    assert c.functions.state().call() == 2, "Old Registrar not moved"
    # Half of the registered labels are moved, the other half are released
    for i in range(1,10):
        label = sha3(['string'], ["name" + str(i)])
        if i % 2 == 0:
            c.functions.moveAccount(label, c2.address).transact({'from': accounts[i]})
            assert token_c.functions.balanceOf(accounts[i]).call() == 0, "Incorrect price returned"
            assert c2.functions.getAccountOwner(label).call() == accounts[i], "Incorrect migrated owner returned"
        else:
            assert c.functions.getAccountOwner(label).call() == accounts[i], "Incorrect non-migrated owner returned"
            c.functions.release(label).transact({'from': accounts[i]})
            assert c.functions.getAccountOwner(label).call() == zero_address, "Incorrect new owner returned"
            assert token_c.functions.balanceOf(accounts[i]).call() == 10
    for i in range(1,10):
        label = sha3(['string'], ["name" + str(i)])
        namehash = sha3(['bytes32','bytes32'],[ens_node,label])
        if i % 2 == 0:
            c2.functions.updateAccountOwner(label).transact({'from': accounts[i]})
            # Assert Account owner updated
            assert c2.functions.getAccountOwner(label).call() == accounts[i]
        else:
            # Assert transaction fails for non account owners
            assert_tx_failed(c2.functions.updateAccountOwner(label), {'from': accounts[i]})

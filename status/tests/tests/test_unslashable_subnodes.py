################################################################################
# slashInvalidUsername()
################################################################################

def test_get_unslashable_subnode(accounts, registrar_deploy, w3, assert_tx_failed, register_accounts, sha3):
    '''
    Test unslashable subnodes
    '''
    # Deploy Registrar contract #1
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    init_price = 10
    erc_amount = 100
    zero_address = "0x" + "00"*20
    # transfer tokens to the registry
    token_c.functions.transfer(c.address, w3.toInt(erc_amount)).transact({'from': accounts[0]})
    token_c.functions.transfer(accounts[1], w3.toInt(erc_amount)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(init_price)).transact({'from': accounts[1]})
    c.functions.activate(init_price).transact({'from': accounts[0]})

    #Invalid 'SigmaPrime' username since it contains 2 upper case characters
    name = 'SigmaPrime'
    #Calculating the label for this name
    label = w3.sha3(text=name)

    #Invalid 'Permanent' username since it contains 1 upper case characters
    name2 = 'Permanent'
    label2 = w3.sha3(text=name2)

    # Computes the namehash for the SigmaPrime.status.eth subnode
    new_node = sha3(['bytes32','bytes32'],[ens_node,label])

    # Computes the namehash for the Permanent.SigmaPrime.status.eth
    immutable_node = sha3(['bytes32','bytes32'],[new_node,label2])

    # Registers SigmaPrime.status.eth
    c.functions.register(
        label,
        accounts[1],
        w3.soliditySha3(['bytes32'], ['0x0']),
        w3.soliditySha3(['bytes32'], ['0x0']),
    ).transact({'from': accounts[1]})

    # Assert that accounts[1] is the owner of SigmaPrime.status.eth
    assert c.functions.getAccountOwner(label).call() == accounts[1], "Incorrect owner returned"

    # Register Permanent.SigmaPrime.status.eth directly on the ENS registrar
    ens_c.functions.setSubnodeOwner(new_node, label2, accounts[1]).transact({'from': accounts[1]})
    #assert ens_c.owner(ens)

    # Let's slaaaash SigmaPrime.status.eth
    c.functions.slashInvalidUsername(bytes(name, 'utf8'),5).transact({'from': accounts[2]})

    # Assert that SigmaPrime was slashed
    assert c.functions.getAccountOwner(label).call() == zero_address, "Incorrect owner returned"

    # Assert that SigmaPrime.status.eth is no longer registered to accounts[1]
    assert ens_c.functions.owner(new_node).call() == zero_address, "SigmaPrime.status.eth is still registered to accounts[1]"

    # Assert that Permanent.SigmaPrime.status.eth is still registered to accounts[1]
    assert ens_c.functions.owner(immutable_node).call() == accounts[1], "Permanent.SigmaPrime.status.eth is not registered to account[1]:"

    # Assert that the attempted slashing of immutable_node fails
    assert_tx_failed(c.functions.slashInvalidUsername(bytes(name2, 'utf8'),1), {'from': accounts[2]})

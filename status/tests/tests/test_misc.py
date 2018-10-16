

def test_withdraw_wrong_node(accounts, registrar_deploy, w3, assert_tx_failed, register_accounts, sha3):

    # Deploy Registrar contract #1
    # root node is "status"
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    # Deploy Registrar contract #2
    (c2, _, _, _, _, ens_node2) = registrar_deploy(parent_registry=c.address,
            token_contract=token_c, resolver_contract=resolver_c,
            root_node_name="sigmaprime",ens_contract=ens_c)
    init_price = 10
    erc_amount = 100
    ens_label = sha3(['string'], ["sigmaprime"])

    # transfer tokens to the registry
    token_c.functions.transfer(c.address, w3.toInt(erc_amount)).transact({'from': accounts[0]})
    # Activate the first registry
    c.functions.activate(init_price).transact({'from': accounts[0]})

    ens_c.functions.setSubnodeOwner(bytes.fromhex('00'), ens_label, c2.address).transact({'from': accounts[0]})
    # set the owner of the "status" domain to the new contract.
    c.functions.moveRegistry(c2.address).transact({'from':accounts[0]})
    # now owner of "status" is c2.address, but c2 thinks "sigmaprime" is ENSNode.
    # now we should be able to call the withdrawWrongNode
    c2.functions.withdrawWrongNode(ens_node, accounts[1]).transact({'from':accounts[0]})
    assert ens_c.functions.owner(ens_node).call() == accounts[1], "Wrong owner"



def test_receive_approval(contract_factories, accounts, registrar_deploy, w3, assert_tx_failed, register_accounts, sha3):

    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    zero_bytes32 = "0x" + "00"*32

    username = "testsigmaprime"
    label = w3.sha3(text=username)

    # abi-encode data for register
    encoded_data = c.encodeABI(fn_name="register", args=[label, accounts[1],zero_bytes32,zero_bytes32])

    c.functions.activate(0).transact({'from': accounts[0]})

    token_c.functions.approveAndCall(c.address, 0, encoded_data).transact({'from':accounts[1]})

    assert c.functions.getAccountOwner(label).call() == accounts[1], "incorrect owner from approveAndCall"

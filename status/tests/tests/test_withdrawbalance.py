################################################################################
# withdrawExcessBalance()
################################################################################


def test_withdraw_excess_snt_balance(accounts, registrar_deploy, w3):
    '''
    Tests withdrawExcessBalance() #1 - Token used is SNT
    '''

    # Deploy Contract
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    erc_amount = 1000
    # transfer tokens to the registry
    token_c.functions.transfer(c.address, w3.toInt(erc_amount)).transact({'from': accounts[0]})
    # Activate the registry
    c.functions.withdrawExcessBalance(token_c.address, accounts[1]).transact({'from': accounts[0]})
    # Verify that the ERC20 token was transfered
    assert token_c.functions.balanceOf(accounts[1]).call() == 1000, "Wrong ERC20 account balance"


def test_withdraw_excess_other_balance(accounts, registrar_deploy, test_token_deploy, w3):
    '''
    Tests withdrawExcessBalance() #2 - Token used is not SNT
    '''

    # Deploy Registry Contract
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    # Deploy ERC20 Contract
    (c2, _) = test_token_deploy(initial_balance = 10000000000000000000)
    erc_amount = 10000
    # transfer tokens to the registry
    c2.functions.transfer(c.address, w3.toInt(erc_amount)).transact({'from': accounts[0]})
    # Activate the registry
    c.functions.withdrawExcessBalance(c2.address, accounts[2]).transact({'from': accounts[0]})
    # Verify that the ERC20 token was transfered
    assert c2.functions.balanceOf(accounts[2]).call() == 10000, "Wrong ERC20 account balance"

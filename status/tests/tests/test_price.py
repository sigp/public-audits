################################################################################
# withdrawExcessBalance()
################################################################################

import pytest

@pytest.mark.parametrize(
    "owners, price, should_transact",
    [
        (0, 1000, True),
        (1, 100, False),
        (2, 2000, False),
        (1, 100, False),
        (4, 10.2, False),
        (0, 100, True),
        (0, 2000, True),
        (3, 1000, False),
    ]
)
def test_update_price_wrong_owner(owners, price, should_transact, accounts, registrar_deploy, w3, assert_tx_failed):
    '''
    Tests update pricing:
    '''
    # Deploy Contract

    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    init_price = 10
    erc_amount = 100
    # transfer tokens to the registry
    token_c.functions.transfer(c.address, w3.toInt(erc_amount)).transact({'from': accounts[0]})
    # Activate the registry
    c.functions.activate(init_price).transact({'from': accounts[0]})
    # Verify that the ERC20 token was transfered
    if should_transact:
        c.functions.updateRegistryPrice(w3.toInt(price)).transact({'from': accounts[owners]})
        assert c.functions.getPrice().call() == price, "Wrong price"
    else:
        assert_tx_failed(c.functions.updateRegistryPrice(w3.toInt(price)), {'from': accounts[owners]})


def test_update_price_wrong_state(accounts, registrar_deploy, w3, assert_tx_failed):
    '''
    Tries to update the price on an "Inactive" registrar
    '''
    #Deploy Contract
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 10000
    erc_amount = 100
    token_c.functions.transfer(c.address, w3.toInt(erc_amount)).transact({'from': accounts[0]})
    assert_tx_failed(c.functions.updateRegistryPrice(w3.toInt(new_price)), {'from': accounts[0]})

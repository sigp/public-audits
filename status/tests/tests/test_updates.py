################################################################################
# updateRegistryPrice()
################################################################################


def test_update_registry_price_notcontroller(accounts, registrar_deploy, w3, assert_tx_failed):
    '''
    Tests updateRegistryPrice() should not update from non-controller
    '''

    # Deploy
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    # Activate
    new_price = 1e2
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    # Attempt to update the price with a non-controller account
    assert_tx_failed(
        c.functions.updateRegistryPrice(
            w3.toInt(1)
        ),
        {'from': accounts[1]}
    )


def test_update_registry_price_not_active(accounts, registrar_deploy, w3, assert_tx_failed):
    '''
    Tests updateRegistryPrice() should not update when inactive
    '''

    # Deploy
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    # Activate
    new_price = 1e2
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    # Attempt to update the price with a non-controller account
    assert_tx_failed(
        c.functions.updateRegistryPrice(
            w3.toInt(new_price)
        ),
        {'from': accounts[0]}
    )

def test_update_registry_price_active(accounts, registrar_deploy, w3, assert_tx_failed, get_logs_for_event):
    '''
    Tests updateRegistryPrice() works with controller in active state
    '''

    # Deploy
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    # Activate
    initial_price = 10
    new_price = 50
    c.functions.activate(w3.toInt(initial_price)).transact({'from': accounts[0]})
    token_c.functions.approve(c.address, w3.toInt(10e6)).transact({'from': accounts[0]})

    # Attempt to update the price with a non-controller account
    tx_event = get_logs_for_event(
            c.events.RegistryPrice,
            c.functions.updateRegistryPrice(new_price).transact({'from': accounts[0]})
    )
    (
        c.functions.updateRegistryPrice(
            w3.toInt(1)
        ),
        {'from': accounts[1]}
    )

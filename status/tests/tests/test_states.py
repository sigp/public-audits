################################################################################
# Activate
################################################################################


def test_activate_correctowner(accounts, registrar_deploy, w3):
    '''
    Tests activate() to ensure the state is correctly set
    '''

    # Deploy Contract
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    new_price = 10

    assert c.functions.state().call() == 0, "State initialised to Unactive"

    # Activate the registry
    c.functions.activate(w3.toInt(new_price)).transact({'from': accounts[0]})

    assert c.functions.state().call() == 1, "Active state set"
    assert c.functions.price().call() == new_price, 'Price set on active'

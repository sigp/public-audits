def test_deploy(registrar_deploy):
    # c: contract, r: tx_receipt
    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()
    print("Gas to deploy: {:,}".format(r.cumulativeGasUsed))


def test_params_instantiated(registrar_deploy, variables):

    # deploy with defaults
    (c, _, _, ens_c, resolver_c, _) = registrar_deploy()

    # shadow c to simplify following asserts
    c = c.functions

    print("Testing for constructor initial instantiation:")

    assert c.price().call() == 0, "Price is initialised"
    assert c.ensNode().call() == variables["ens_node"], "Wrong ENS node"
    assert c.ensRegistry().call() == ens_c.address, "Wrong ENS Registry "
    assert c.resolver().call() == resolver_c.address, "Wrong Resolver"
    assert c.usernameMinLength().call() == 10, "Wrong Minimum username length"
    assert c.reservedUsernamesMerkleRoot().call().hex() == "00"*32 , "Merkle root not initialised correctly"
    assert c.parentRegistry().call() == variables["zero_address"], "Wrong parent registry"


def test_activated(registrar_deploy):
    (c, _, _, _, _, _) = registrar_deploy()
    #assert(c.functions.RegistrarState().call() == "Active", "Registar is not active")


def test_expiration_time(registrar_deploy):
    (c, _, _, _, _, _) = registrar_deploy()

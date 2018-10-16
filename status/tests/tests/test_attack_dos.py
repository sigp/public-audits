

def test_attack_dos_all_users(
        accounts,
        registrar_deploy,
        register_accounts,
        dos_attack_deploy,
        assert_tx_failed,
        sha3
        ):

    (c, _, token_c, _, _, _) = registrar_deploy()

    register_accounts(c, token_c)

    # deploy malicious contract
    (dos_c, _) = dos_attack_deploy()

    # Migrate to our malicious contract
    c.functions.moveRegistry(dos_c.address).transact({'from': accounts[0]})
    label = sha3(['string'], ["name" + str(2)])
    assert_tx_failed(c.functions.release(label), {'from': accounts[2], 'gas':
                     2000000})

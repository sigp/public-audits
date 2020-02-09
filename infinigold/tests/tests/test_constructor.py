def test_constructor_values_from_delegate_call(
        token_proxy_initialize_and_deploy,
        accounts,
        assert_tx_failed,
        instantiate):

    # Deploy a TokenImpl and TokenProxy
    (token_proxy_impl, token_proxy) = token_proxy_initialize_and_deploy("Infinigold", "PMG", 2)

    assert token_proxy_impl.functions.name().call({'from':accounts[2]}) == "Infinigold"
    assert token_proxy_impl.functions.symbol().call({'from':accounts[2]}) == "PMG"
    assert token_proxy_impl.functions.decimals().call({'from':accounts[2]}) == 2

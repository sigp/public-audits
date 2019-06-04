def test_link_transfer(full_conversion_rate_deploy, multi_oracle_deploy, accounts, assert_tx_failed):

    # Deploys test rig (conversionrate, oracles and link contracts)
    (conversion_rate, conversion_rate_r, oracles, oracles_r, link, link_r) = full_conversion_rate_deploy(100,5,10)
    # Verify that account[0] has the entire balance
    assert link.functions.balanceOf(accounts[0]).call() == link.functions.totalSupply().call()

    # Send some LINK tokens to our ConversionRate contract
    link.functions.transfer(conversion_rate.address, 10000).transact({'from': accounts[0]})

    # Verify that the ConversionRate contract has now the adequate LINK balance
    assert link.functions.balanceOf(conversion_rate.address).call() == 10000

    # Call the transferLINK function on ConversionRate

    conversion_rate.functions.transferLINK(accounts[2], 500).transact({'from': accounts[0]})

    # Verify that account[2] has now the adequate LINK balance
    assert link.functions.balanceOf(accounts[2]).call() == 500

    # Verify that only the owner of the ConversionRate smart contract has the ability to call transferLINK
    assert_tx_failed(conversion_rate.functions.transferLINK(accounts[2], 500), {'from': accounts[1]})


def test_authorization(full_conversion_rate_deploy, multi_oracle_deploy, accounts, assert_tx_failed):

    # Deploys test rig (conversionrate, oracles and link contracts)
    (conversion_rate, conversion_rate_r, oracles, oracles_r, link, link_r) = full_conversion_rate_deploy(100,5,10)

    # Defines requesters
    requester = accounts[3]
    requester_2 = accounts[4]

    # Add accounts 3 as an authorised requester
    conversion_rate.functions.setAuthorization(requester, bool(1)).transact({'from': accounts[0]})
    assert conversion_rate.functions.authorizedRequesters(requester).call() == bool(1)

    # Verifies that only the owner can set the authorizations
    assert_tx_failed(conversion_rate.functions.setAuthorization(requester_2, bool(1)), {'from': accounts[1]})

    # Verifies that the owner can unset the authorisation for a requester
    conversion_rate.functions.setAuthorization(requester, bool(0)).transact({'from': accounts[0]})
    assert conversion_rate.functions.authorizedRequesters(requester).call() == bool(0)


def test_destroy(full_conversion_rate_deploy, multi_oracle_deploy, accounts, assert_tx_failed):

    # Deploys test rig (conversionrate, oracles and link contracts)
    (conversion_rate, conversion_rate_r, oracles, oracles_r, link, link_r) = full_conversion_rate_deploy(100,5,10)

    # Send some LINK tokens to our ConversionRate contract
    link.functions.transfer(conversion_rate.address, 10000).transact({'from': accounts[0]})

    # Verify that the ConversionRate contract has now the adequate LINK balance
    assert link.functions.balanceOf(conversion_rate.address).call() == 10000

    # Verifies that only the owner can call destroy
    assert_tx_failed(conversion_rate.functions.destroy(), {'from': accounts[1]})

    # Call destroy from owner
    conversion_rate.functions.destroy().transact({'from': accounts[0]})

    # Verify that the ConversionRate contract has no more LINK tokens
    assert link.functions.balanceOf(conversion_rate.address).call() == 0

    # Verify that the account owner retrieved the contract's LINK tokens
    assert link.functions.balanceOf(accounts[0]).call() == link.functions.totalSupply().call()


def test_ownership(full_conversion_rate_deploy, multi_oracle_deploy, accounts, assert_tx_failed):

    # Deploys test rig (conversionrate, oracles and link contracts)
    (conversion_rate, conversion_rate_r, oracles, oracles_r, link, link_r) = full_conversion_rate_deploy(100,5,10)

    # Transfer contract ownership
    conversion_rate.functions.transferOwnership(accounts[1]).transact({'from': accounts[0]})

    # Verify that contract owner is accounts[1]
    assert conversion_rate.functions.owner().call() == accounts[1]

    # Renounce Ownership
    conversion_rate.functions.renounceOwnership().transact({'from': accounts[1]})

    # Verify that onlyOwner functions are not callable
    requester = accounts[3]
    assert_tx_failed(conversion_rate.functions.setAuthorization(requester, bool(1)), {'from': accounts[1]})

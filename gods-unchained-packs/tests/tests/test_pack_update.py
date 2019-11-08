import pytest

def test_pack_update(accounts, pack_deploy, instantiate, get_logs_for_event, pack_types, pack_prices, assert_tx_failed):

    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # This should be invalid since the pack size is zero
    tx_hash = pack.functions.setPack(pack_types['Legendary'], pack_prices['Legendary'], "Legendary Bundle", "BNDL", 0, 30).transact({'from': accounts[0]})
    token = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(token.address, True).transact({'from': accounts[0]})


    # Now can't update pack
    assert_tx_failed(
        pack.functions.setPack(pack_types['Legendary'], pack_prices['Legendary'], "Legendary Bundle", "BNDL", 3, 0),
        {'from': accounts[0]}
    )

    # And can't use pack
    token.functions.purchaseFor(accounts[0], 1, accounts[1])\
        .transact({'from': accounts[0], 'value': pack_prices['Legendary']})



import pytest
import random
from web3.contract import ConciseContract

##########################
# VALID OPERATIONS
##########################

def test_predict_packs(
        accounts,
        assert_tx_failed,
        ganache_mine_block,
        get_logs_for_event,
        instantiate,
        pack_deploy,
        pack_prices,
        pack_types,
        w3,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # Create a card
    cards.functions.addSpell(0, 1, 0, 1, True).transact({'from': accounts[0]}) # Common
    cards.functions.addWeapon(1, 1, 0, 1, 1, 1, True).transact({'from': accounts[0]}) # Rare
    cards.functions.addWeapon(2, 1, 1, 1, 1, 1, True).transact({'from': accounts[0]}) # Epic
    cards.functions.addWeapon(3, 1, 2, 1, 1, 1, True).transact({'from': accounts[0]}) # Legendary
    cards.functions.addWeapon(4, 1, 3, 1, 1, 1, True).transact({'from': accounts[0]}) # Shiny

    # Set packs for purchase
    tx_hash = pack.functions.setPack(pack_types['Shiny'], pack_prices['Shiny'], "Rare bundle", "RB", 1, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    # Activate purchase with card index 0
    pack.functions.purchase(pack_types['Shiny'], 1, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Shiny'] * 1})
    pack.functions.callback(0).transact({'from': accounts[0]})

    prediction = pack.functions.predictPacks(0).call({'from': accounts[1]})
    tx = pack.functions.activateMultiple([0,0,0,0,0], [0,1,2,3,4]).transact({'from': accounts[0]})
    logs = get_logs_for_event(pack.events.CardActivated, tx)
    for i, log in enumerate(logs):
        assert log['args']['proto'] == prediction[0][i]
        assert log['args']['purity'] == prediction[1][i]


@pytest.mark.xfail
def test_predict_packs_gas(
        accounts,
        assert_tx_failed,
        ganache_mine_block,
        get_logs_for_event,
        instantiate,
        pack_deploy,
        pack_prices,
        pack_types,
        w3,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # Create a card
    cards.functions.addSpell(0, 1, 0, 1, True).transact({'from': accounts[0]}) # Common
    cards.functions.addWeapon(1, 1, 0, 1, 1, 1, True).transact({'from': accounts[0]}) # Rare
    cards.functions.addWeapon(2, 1, 1, 1, 1, 1, True).transact({'from': accounts[0]}) # Epic
    cards.functions.addWeapon(3, 1, 2, 1, 1, 1, True).transact({'from': accounts[0]}) # Legendary
    cards.functions.addWeapon(4, 1, 3, 1, 1, 1, True).transact({'from': accounts[0]}) # Shiny

    # Set packs for purchase
    tx_hash = pack.functions.setPack(pack_types['Shiny'], pack_prices['Shiny'], "Rare bundle", "RB", 1, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    # Activate purchase with card index 0
    purchase_count = 190
    pack.functions.purchase(pack_types['Shiny'], purchase_count, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Shiny'] * purchase_count})
    pack.functions.callback(0).transact({'from': accounts[0]})

    pack.functions.predictPacks(0).transact({'from': accounts[1]})

##########################
# INVALID OPERATIONS
##########################

def test_bad_index(
        accounts,
        assert_tx_failed,
        ganache_mine_block,
        get_logs_for_event,
        instantiate,
        pack_deploy,
        pack_prices,
        pack_types,
        w3,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # No index yet
    assert_tx_failed(pack.functions.predictPacks(0), {'from': accounts[1]})

    # Create a card
    cards.functions.addSpell(0, 1, 0, 1, True).transact({'from': accounts[0]}) # Common
    cards.functions.addWeapon(1, 1, 0, 1, 1, 1, True).transact({'from': accounts[0]}) # Rare
    cards.functions.addWeapon(2, 1, 1, 1, 1, 1, True).transact({'from': accounts[0]}) # Epic
    cards.functions.addWeapon(3, 1, 2, 1, 1, 1, True).transact({'from': accounts[0]}) # Legendary
    cards.functions.addWeapon(4, 1, 3, 1, 1, 1, True).transact({'from': accounts[0]}) # Shiny

    # Set packs for purchase
    tx_hash = pack.functions.setPack(pack_types['Shiny'], pack_prices['Shiny'], "Rare bundle", "RB", 1, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    # Activate purchase with card index 0
    pack.functions.purchase(pack_types['Shiny'], 1, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Shiny'] * 1})
    pack.functions.callback(0).transact({'from': accounts[0]})

    # Bad indices
    assert_tx_failed(pack.functions.predictPacks(1), {'from': accounts[1]})
    assert_tx_failed(pack.functions.predictPacks(2**256 - 1), {'from': accounts[1]})


def test_no_random(
        accounts,
        assert_tx_failed,
        ganache_mine_block,
        get_logs_for_event,
        instantiate,
        pack_deploy,
        pack_prices,
        pack_types,
        w3,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # Create a card
    cards.functions.addSpell(0, 1, 0, 1, True).transact({'from': accounts[0]}) # Common
    cards.functions.addWeapon(1, 1, 0, 1, 1, 1, True).transact({'from': accounts[0]}) # Rare
    cards.functions.addWeapon(2, 1, 1, 1, 1, 1, True).transact({'from': accounts[0]}) # Epic
    cards.functions.addWeapon(3, 1, 2, 1, 1, 1, True).transact({'from': accounts[0]}) # Legendary
    cards.functions.addWeapon(4, 1, 3, 1, 1, 1, True).transact({'from': accounts[0]}) # Shiny

    # Set packs for purchase
    tx_hash = pack.functions.setPack(pack_types['Shiny'], pack_prices['Shiny'], "Rare bundle", "RB", 1, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    # Activate purchase with card index 0
    pack.functions.purchase(pack_types['Shiny'], 1, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Shiny'] * 1})

    assert_tx_failed(pack.functions.predictPacks(0), {'from': accounts[1]})

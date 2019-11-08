import pytest
import random
from web3.contract import ConciseContract

##########################
# VALID OPERATIONS
##########################

def test_activate(
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
    pack.functions.purchase(pack_types['Shiny'], 1, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Shiny']})
    assert pack.functions.isActivated(0, 0).call() == False
    pack.functions.callback(0).transact({'from': accounts[0]})
    tx = pack.functions.activate(0, 0).transact({'from': accounts[1]})
    assert pack.functions.getStateBit(0, 0).call() == 1

    logs = get_logs_for_event(pack.events.CardActivated, tx)
    assert logs[0]['args']['purchaseID'] == 0, "Activate purcahseID"
    assert logs[0]['args']['cardIndex'] == 0, "Activate cardIndex"
    assert logs[0]['args']['cardID'] <= 4
    assert logs[0]['args']['proto'] >= 0
    assert logs[0]['args']['purity'] >= 0

    pack.functions.activate(0, 1).transact({'from': accounts[1]})
    assert pack.functions.getStateBit(0, 1).call() == 1
    pack.functions.activate(0, 2).transact({'from': accounts[1]})
    assert pack.functions.getStateBit(0, 2).call() == 1
    pack.functions.activate(0, 3).transact({'from': accounts[1]})
    assert pack.functions.getStateBit(0, 3).call() == 1
    pack.functions.activate(0, 4).transact({'from': accounts[1]})
    assert pack.functions.getStateBit(0, 4).call() == 1


##########################
# INVALID OPERATIONS
##########################

def test_activate_bad_index(
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

    # Set packs for purchase
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], "Rare bundle", "RB", 1, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})
    pack.functions.purchase(pack_types['Rare'], 1, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Rare']})
    pack.functions.callback(0).transact({'from': accounts[0]})

    # Create a cards
    cards.functions.addSpell(0, 1, 0, 1, True).transact({'from': accounts[0]}) # Common
    cards.functions.addWeapon(1, 1, 0, 1, 1, 1, True).transact({'from': accounts[0]}) # Rare
    cards.functions.addWeapon(2, 1, 1, 1, 1, 1, True).transact({'from': accounts[0]}) # Epic
    cards.functions.addWeapon(3, 1, 2, 1, 1, 1, True).transact({'from': accounts[0]}) # Legendary
    cards.functions.addWeapon(4, 1, 3, 1, 1, 1, True).transact({'from': accounts[0]}) # Mythic

    # Bad activation indices
    assert_tx_failed(pack.functions.activate(0, 6), {'from': accounts[1]})
    assert_tx_failed(pack.functions.activate(1, 0), {'from': accounts[1]})
    assert_tx_failed(pack.functions.activate(2**256 - 1, 2**256 - 1), {'from': accounts[1]})


def test_activate_already_active(
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

    # Set packs for purchase
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], "Rare bundle", "RB", 1, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})
    pack.functions.purchase(pack_types['Rare'], 1, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Rare']})
    pack.functions.callback(0).transact({'from': accounts[0]})

    # Create a cards
    cards.functions.addSpell(0, 1, 0, 1, True).transact({'from': accounts[0]}) # Common
    cards.functions.addWeapon(1, 1, 0, 1, 1, 1, True).transact({'from': accounts[0]}) # Rare
    cards.functions.addWeapon(2, 1, 1, 1, 1, 1, True).transact({'from': accounts[0]}) # Epic
    cards.functions.addWeapon(3, 1, 2, 1, 1, 1, True).transact({'from': accounts[0]}) # Legendary
    cards.functions.addWeapon(4, 1, 3, 1, 1, 1, True).transact({'from': accounts[0]}) # Mythic

    # Already Active
    pack.functions.activate(0, 0).transact({'from': accounts[1]})
    assert_tx_failed(pack.functions.activate(0, 0), {'from': accounts[1]})

def test_activate_no_randomness(
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

    # Set packs for purchase
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], "Rare bundle", "RB", 1, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})
    pack.functions.purchase(pack_types['Rare'], 1, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Rare']})

    # Create a cards
    cards.functions.addSpell(0, 1, 0, 1, True).transact({'from': accounts[0]}) # Common
    cards.functions.addWeapon(1, 1, 0, 1, 1, 1, True).transact({'from': accounts[0]}) # Rare
    cards.functions.addWeapon(2, 1, 1, 1, 1, 1, True).transact({'from': accounts[0]}) # Epic
    cards.functions.addWeapon(3, 1, 2, 1, 1, 1, True).transact({'from': accounts[0]}) # Legendary
    cards.functions.addWeapon(4, 1, 3, 1, 1, 1, True).transact({'from': accounts[0]}) # Mythic

    # Already Active
    assert_tx_failed(pack.functions.activate(0, 0), {'from': accounts[1]})

import pytest
import random
from web3.contract import ConciseContract

##########################
# VALID OPERATIONS
##########################

def test_callback(
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
    tx_hash = pack.functions.setPack(pack_types['Shiny'], pack_prices['Shiny'], "Rare bundle", "RB", 1, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})
    pack.functions.purchase(pack_types['Shiny'], 1, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Shiny']})

    assert pack.functions.purchases(0).call()[1] == 0 # Randomness is at index 1
    tx = pack.functions.callback(0).transact({'from': accounts[0]})
    assert pack.functions.purchases(0).call()[1] >= 0

    logs = get_logs_for_event(pack.events.CallbackMade, tx)
    assert logs[0]['args']['id'] == 0, "Activate purcahseID"
    assert logs[0]['args']['user'] == accounts[1], "Activate cardIndex"
    assert logs[0]['args']['count'] == 1
    assert logs[0]['args']['randomness'] >= 0

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

    # Set packs for purchase
    tx_hash = pack.functions.setPack(pack_types['Shiny'], pack_prices['Shiny'], "Rare bundle", "RB", 1, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})
    pack.functions.purchase(pack_types['Shiny'], 1, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Shiny']})

    assert_tx_failed(pack.functions.callback(1), {'from': accounts[0]})
    assert_tx_failed(pack.functions.callback(2**256 - 1), {'from': accounts[0]})

def test_already_set(
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
    tx_hash = pack.functions.setPack(pack_types['Shiny'], pack_prices['Shiny'], "Rare bundle", "RB", 1, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})
    pack.functions.purchase(pack_types['Shiny'], 1, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Shiny']})

    pack.functions.callback(0).transact({'from': accounts[0]})
    assert_tx_failed(pack.functions.callback(0), {'from': accounts[0]})

def test_purchased_256_blocks_ago(
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
    tx_hash = pack.functions.setPack(pack_types['Shiny'], pack_prices['Shiny'], "Rare bundle", "RB", 1, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})
    pack.functions.purchase(pack_types['Shiny'], 1, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Shiny']})

    ganache_mine_block(256)
    assert_tx_failed(pack.functions.callback(0), {'from': accounts[0]})

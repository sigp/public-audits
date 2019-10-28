import pytest
import random
from web3.contract import ConciseContract

##########################
# VALID OPERATIONS
##########################

def test_bundle_open_for(
        accounts,
        assert_tx_failed,
        get_logs_for_event,
        instantiate,
        pack_deploy,
        pack_prices,
        pack_types,
        w3,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # Purchase from accounts[1], approve accounts[2] as spender
    bundle_size = 3 # 3 packs of 5 cards in a bundle
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], "Rare bundle", "RB", bundle_size, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})
    rare_bundle.functions.purchase(1, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Rare'] * bundle_size})
    rare_bundle.functions.approve(accounts[2], 1).transact({'from': accounts[1]})

    # Accounts[2] opensFor(accounts[1])
    tx = rare_bundle.functions.openFor(accounts[1], 1).transact({'from': accounts[2]})

    logs = get_logs_for_event(pack.events.BundlesOpened, tx)
    assert logs[0]['args']['id'] == 0, "Bundle open id"
    assert logs[0]['args']['packType'] == 0, "Bundle open pack type"
    assert logs[0]['args']['user'] == accounts[1], "Bundle open user"
    assert logs[0]['args']['count'] == 1, "Bundle open count"
    assert logs[0]['args']['packCount'] == 3, "Bundle open packCount"

    logs = get_logs_for_event(pack.events.PurchaseRecorded, tx)
    assert logs[0]['args']['id'] == 0, "purchaseRecorded ID"
    assert logs[0]['args']['packType'] == pack_types['Rare'], "purchaseRecorded packType"
    assert logs[0]['args']['user'] == accounts[1], "purchaseRecorded user"
    assert logs[0]['args']['count'] == 3, "purchaseRecorded count"
    assert logs[0]['args']['lockup'] == 0, "purchaseRecorded lockup"

    logs = get_logs_for_event(rare_bundle.events.Transfer, tx)
    assert logs[0]['args']['from'] == accounts[1], "Burn from user"
    assert logs[0]['args']['to'] == '0x' + '00' * 20, "Burn to 0"
    assert logs[0]['args']['value'] == 1, "Burn x tokens"


def test_open_for_max_count(
        accounts,
        assert_tx_failed,
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
    bundle_size = 1
    num_bundles = 2**15 # 2 packs of 5 cards in a bundle
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], "Rare bundle", "RB", bundle_size, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})
    rare_bundle.functions.purchase(num_bundles, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Rare'] * bundle_size * num_bundles})

    rare_bundle.functions.open(num_bundles).transact({'from': accounts[1]})


@pytest.mark.xfail
def test_open_for_zero(
        accounts,
        assert_tx_failed,
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
    bundle_size = 1
    num_bundles = 2
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], "Rare bundle", "RB", bundle_size, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})
    rare_bundle.functions.purchase(num_bundles, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Rare'] * bundle_size * num_bundles})

    rare_bundle.functions.open(0).transact({'from': accounts[1]})


##########################
# INVALID OPERATIONS
##########################

def test_open_for_too_many(
        accounts,
        assert_tx_failed,
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
    bundle_size = 1
    num_bundles = 5
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], "Rare bundle", "RB", bundle_size, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})
    rare_bundle.functions.purchase(num_bundles, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Rare'] * bundle_size * num_bundles})
    rare_bundle.functions.approve(accounts[2], num_bundles).transact({'from': accounts[1]})

    # Open more than is approved
    assert_tx_failed(rare_bundle.functions.openFor(accounts[1], num_bundles + 1), {'from': accounts[2]})
    assert_tx_failed(rare_bundle.functions.openFor(accounts[1], 2**256 - 1), {'from': accounts[2]})
    assert_tx_failed(rare_bundle.functions.openFor(accounts[1], 2**16 - 1), {'from': accounts[2]})


def test_open_for_too_many_2(
        accounts,
        assert_tx_failed,
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
    bundle_size = 1
    num_bundles = 5
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], "Rare bundle", "RB", bundle_size, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})
    rare_bundle.functions.purchase(num_bundles * 2, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Rare'] * bundle_size * num_bundles * 2})
    rare_bundle.functions.approve(accounts[2], num_bundles).transact({'from': accounts[1]})

    # Allow open purchased bundles but fail if we try and open the same bundles again
    rare_bundle.functions.openFor(accounts[1], num_bundles).transact({'from': accounts[2]})
    assert_tx_failed(rare_bundle.functions.openFor(accounts[1], 1), {'from': accounts[2]})


def test_open_for_not_approved(
        accounts,
        assert_tx_failed,
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
    bundle_size = 1
    num_bundles = 5
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], "Rare bundle", "RB", bundle_size, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})
    rare_bundle.functions.purchase(num_bundles, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Rare'] * bundle_size * num_bundles})

    # Not approved
    assert_tx_failed(rare_bundle.functions.openFor(accounts[1], num_bundles), {'from': accounts[2]})

    # Only accounts[3] approved
    rare_bundle.functions.approve(accounts[3], num_bundles).transact({'from': accounts[1]})
    assert_tx_failed(rare_bundle.functions.openFor(accounts[1], num_bundles), {'from': accounts[2]})


def test_open_for_not_purchased(
        accounts,
        assert_tx_failed,
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
    bundle_size = 1
    num_bundles = 5
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], "Rare bundle", "RB", bundle_size, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    rare_bundle.functions.approve(accounts[2], num_bundles).transact({'from': accounts[1]})

    assert_tx_failed(rare_bundle.functions.openFor(accounts[1], num_bundles), {'from': accounts[2]})

def test_open_for_not_purchased_enough(
        accounts,
        assert_tx_failed,
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
    bundle_size = 1
    num_bundles = 5
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], "Rare bundle", "RB", bundle_size, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})
    rare_bundle.functions.purchase(1, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Rare'] * bundle_size * num_bundles})

    rare_bundle.functions.approve(accounts[2], num_bundles).transact({'from': accounts[1]})

    assert_tx_failed(rare_bundle.functions.openFor(accounts[1], num_bundles), {'from': accounts[2]})

import pytest
import random
from web3.contract import ConciseContract

##########################
# VALID OPERATIONS
##########################

def test_bundle_purchase(
        accounts,
        assert_tx_failed,
        instantiate,
        get_logs_for_event,
        pack_deploy,
        pack_prices,
        pack_types,
        w3,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # Set packs for purchase
    bundle_size = 3 # 3 packs of 5 cards in a bundle
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], 'Rare bundle', 'RB', bundle_size, 40).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    # purchase rare pack
    tx = rare_bundle.functions.purchase(1, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Rare'] * bundle_size})

    logs = get_logs_for_event(rare_bundle.events.BundlesPurchased, tx)
    assert logs[0]['args']['user'] == accounts[1], "purchaseRecorded user"
    assert logs[0]['args']['count'] == 1, "purchaseRecorded count"
    assert logs[0]['args']['referrer'] == accounts[2], "PaymentProcessed referrer"
    assert logs[0]['args']['paymentID'] == 0, "PackPurchased paymentID"

    logs = get_logs_for_event(processor.events.PaymentProcessed, tx)
    assert logs[0]['args']['id'] == 0, "PaymentProcessed purchaseID"
    assert logs[0]['args']['user'] == accounts[1], "PaymentProcessed user"
    assert logs[0]['args']['cost'] == pack_prices['Rare'] * bundle_size, "PaymentProcessed cost"
    assert logs[0]['args']['items'] == 1, "PaymentProcessed items"
    assert logs[0]['args']['referrer'] == accounts[2], "PaymentProcessed referrer"
    assert logs[0]['args']['toVault'] == pack_prices['Rare'] * 0.9 * bundle_size, "PaymentProcessed toVault"
    assert logs[0]['args']['toReferrer'] == pack_prices['Rare'] * 0.1 * bundle_size, "PaymentProcessed toReferrer"

    logs = get_logs_for_event(rare_bundle.events.Transfer, tx)
    assert logs[0]['args']['from'] == '0x' + '00' * 20, "Mint from"
    assert logs[0]['args']['to'] == accounts[1], "Mint to user"
    assert logs[0]['args']['value'] == 1, "Mint new token value"


def test_purchase_max_count(
        accounts,
        assert_tx_failed,
        instantiate,
        get_logs_for_event,
        pack_deploy,
        pack_prices,
        pack_types,
        w3,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # Set packs for purchase
    bundle_size = 2**15 # 2**15 packs of 5 cards in a bundle
    tx_hash = pack.functions.setPack(pack_types['Shiny'], pack_prices['Shiny'], 'Rare bundle', 'RB', bundle_size, 40).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    # Maximum count, this shouldn't fail
    rare_bundle.functions.purchase(1, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Shiny'] * bundle_size})


def test_bundle_purchase_discounted(
        accounts,
        assert_tx_failed,
        instantiate,
        get_logs_for_event,
        pack_deploy,
        pack_prices,
        pack_types,
        w3,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # Set packs for purchase
    bundle_size = 3 # 3 packs of 5 cards in a bundle
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], 'Rare bundle', 'RB', bundle_size, 40).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    # Set discount to 10 for accounts[2]
    referrals.functions.setSplit(10, 0).transact({'from': accounts[2]})

    # purchase rare pack
    tx = rare_bundle.functions.purchase(1, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Rare'] * bundle_size})


def test_purchase_referrer_zero(
        accounts,
        assert_tx_failed,
        instantiate,
        get_logs_for_event,
        pack_deploy,
        pack_prices,
        pack_types,
        w3,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # Set packs for purchase
    bundle_size = 3 # 3 packs of 5 cards in a bundle
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], 'Rare bundle', 'RB', bundle_size, 40).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    # purchase rare pack
    zero_address = '0x' + '00' * 20
    tx = rare_bundle.functions.purchase(1, zero_address).transact({'from': accounts[1], 'value': pack_prices['Rare'] * bundle_size})


##########################
# INVALID OPERATIONS
##########################

def test_purchase_not_enough_eth(
        accounts,
        assert_tx_failed,
        instantiate,
        get_logs_for_event,
        pack_deploy,
        pack_prices,
        pack_types,
        w3,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # Set packs for purchase
    bundle_size = 3 # 3 packs of 5 cards in a bundle
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], 'Rare bundle', 'RB', bundle_size, 40).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    assert_tx_failed(rare_bundle.functions.purchase(1, accounts[2]), {'from': accounts[1], 'value': pack_prices['Rare'] * bundle_size - 1})
    assert_tx_failed(rare_bundle.functions.purchase(1, accounts[2]), {'from': accounts[1], 'value': pack_prices['Rare']})
    assert_tx_failed(rare_bundle.functions.purchase(1, accounts[2]), {'from': accounts[1], 'value': 1})
    assert_tx_failed(rare_bundle.functions.purchase(1, accounts[2]), {'from': accounts[1], 'value': 0})



def test_purchase_buying_0_bundles(
        accounts,
        assert_tx_failed,
        instantiate,
        get_logs_for_event,
        pack_deploy,
        pack_prices,
        pack_types,
        w3,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # Set packs for purchase
    bundle_size = 3 # 3 packs of 5 cards in a bundle
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], 'Rare bundle', 'RB', bundle_size, 40).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    assert_tx_failed(rare_bundle.functions.purchase(0, accounts[2]), {'from': accounts[1], 'value': pack_prices['Rare'] * bundle_size})

def test_purchase_refer_self(
        accounts,
        assert_tx_failed,
        instantiate,
        get_logs_for_event,
        pack_deploy,
        pack_prices,
        pack_types,
        w3,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # Set packs for purchase
    bundle_size = 3 # 3 packs of 5 cards in a bundle
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], 'Rare bundle', 'RB', bundle_size, 40).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    assert_tx_failed(rare_bundle.functions.purchase(1, accounts[1]), {'from': accounts[1], 'value': pack_prices['Rare'] * bundle_size})

def test_purchase_exceed_cap(
        accounts,
        assert_tx_failed,
        instantiate,
        get_logs_for_event,
        pack_deploy,
        pack_prices,
        pack_types,
        w3,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # Set packs for purchase
    bundle_size = 3
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], 'Rare bundle', 'RB', bundle_size, 40).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    assert_tx_failed(rare_bundle.functions.purchase(41, accounts[2]), {'from': accounts[1], 'value': pack_prices['Rare'] * bundle_size})
    assert_tx_failed(rare_bundle.functions.purchase(2**256 - 1, accounts[2]), {'from': accounts[1], 'value': pack_prices['Rare'] * bundle_size})

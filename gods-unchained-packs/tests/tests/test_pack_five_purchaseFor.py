import pytest
import random
from web3.contract import ConciseContract

##########################
# VALID OPERATIONS
##########################

def test_purchase_for(
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

    # purchase rare pack
    tx = pack.functions.purchaseFor(pack_types['Rare'], accounts[3], 1, accounts[2], 0).transact({'from': accounts[1], 'value': pack_prices['Rare']})
    purchaseID = 0
    purchased = pack.functions.purchases(purchaseID).call()
    assert purchased[0] == 1, "count set to 1"
    assert purchased[1] == 0, "randomness set to 0 until callback"
    assert purchased[2] == pack_types['Rare'], "pack type not set correctly, or `current` is set"
    assert purchased[3] == w3.eth.getBlock('latest').number, "block height"
    assert purchased[4] == 0, "lockup should be 0"
    assert purchased[5] == False, "revoked should be false"
    assert purchased[6] == accounts[3], "purchaser is accounts[1]"

    logs = get_logs_for_event(pack.events.PurchaseRecorded, tx)
    assert logs[0]['args']['id'] == 0, "purchaseRecorded ID"
    assert logs[0]['args']['packType'] == pack_types['Rare'], "purchaseRecorded packType"
    assert logs[0]['args']['user'] == accounts[3], "purchaseRecorded user"
    assert logs[0]['args']['count'] == 1, "purchaseRecorded count"
    assert logs[0]['args']['lockup'] == 0, "purchaseRecorded lockup"

    logs = get_logs_for_event(pack.events.PacksPurchased, tx)
    assert logs[0]['args']['paymentID'] == 0, "PackPurchased paymentID"
    assert logs[0]['args']['id'] == 0, "PackPurchased purchaseID"
    assert logs[0]['args']['packType'] == pack_types['Rare'], "PackPurchase packType"
    assert logs[0]['args']['user'] == accounts[3], "PackPurchase user"
    assert logs[0]['args']['count'] == 1, "PackPurchase count"
    assert logs[0]['args']['lockup'] == 0, "PackPurchase lockup"

    logs = get_logs_for_event(processor.events.PaymentProcessed, tx)
    assert logs[0]['args']['id'] == 0, "PaymentProcessed purchaseID"
    assert logs[0]['args']['user'] == accounts[1], "PaymentProcessed user"
    assert logs[0]['args']['cost'] == pack_prices['Rare'], "PaymentProcessed cost"
    assert logs[0]['args']['items'] == 1, "PaymentProcessed items"
    assert logs[0]['args']['referrer'] == accounts[2], "PaymentProcessed referrer"
    assert logs[0]['args']['toVault'] == pack_prices['Rare'] * 0.9, "PaymentProcessed toVault"
    assert logs[0]['args']['toReferrer'] == pack_prices['Rare'] * 0.1, "PaymentProcessed toReferrer"


def test_purchase_for_max_count(
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
    tx_hash = pack.functions.setPack(pack_types['Shiny'], pack_prices['Shiny'], "Rare bundle", "RB", 1, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    # Maximum count, this shouldn't fail
    pack.functions.purchaseFor(pack_types['Shiny'], accounts[3], 2**15, accounts[2], 0).transact({'from': accounts[1], 'value': pack_prices['Shiny'] * 2**15})


def test_purchase_for_referrer_zero(
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
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], "Rare bundle", "RB", 1, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    # Referrer is 0
    zero_address = '0x' + '00' * 20
    tx = pack.functions.purchaseFor(pack_types['Rare'], accounts[3], 1, zero_address, 0).transact({'from': accounts[1], 'value': pack_prices['Rare']})
    logs = get_logs_for_event(processor.events.PaymentProcessed, tx)
    assert logs[0]['args']['cost'] == pack_prices['Rare'], "PaymentProcessed cost"
    assert logs[0]['args']['referrer'] == zero_address, "PaymentProcessed referrer"
    assert logs[0]['args']['toVault'] == pack_prices['Rare'], "PaymentProcessed toVault"
    assert logs[0]['args']['toReferrer'] == 0, "PaymentProcessed toReferrer"


def test_purchase_for_different_count_vs_bundle_size(
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
    tx_hash = pack.functions.setPack(pack_types['Epic'], pack_prices['Epic'], "Rare bundle", "RB", 2, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    # Allow purchase with different bundle size to pack count
    tx = pack.functions.purchaseFor(pack_types['Epic'], accounts[3], 1, accounts[2], 0).transact({'from': accounts[1], 'value': pack_prices['Epic'] * 1})

def test_purchase_for_refund(
        accounts,
        assert_tx_failed,
        get_balance,
        instantiate,
        get_logs_for_event,
        pack_deploy,
        pack_prices,
        pack_types,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # Set packs for purchase
    pack_cost = pack_prices['Rare']
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], "Rare bundle", "RB", 1, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    ac1_balance_pre = get_balance(accounts[1])
    ac3_balance_pre = get_balance(accounts[3])

    # Purchase Rare Pack and expect 5 eth change
    payment_amount = pack_cost + int(5e18)
    pack.functions.purchaseFor(pack_types['Rare'], accounts[3], 1, accounts[2], 0).transact({'from': accounts[1], 'value': payment_amount})

    assert ac3_balance_pre == get_balance(accounts[3]) # blance should not change
    # Assuming gas < 1eth refund correct user
    assert ac1_balance_pre - pack_cost - 1e18 < get_balance(accounts[1])


##########################
# INVALID OPERATIONS
##########################

def test_purchase_for_not_enough_eth(
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
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], "Rare bundle", "RB", 1, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    assert_tx_failed(pack.functions.purchaseFor(pack_types['Rare'], accounts[3], 1, accounts[2], 0), {'from': accounts[1], 'value': 1})
    assert_tx_failed(pack.functions.purchaseFor(pack_types['Rare'], accounts[3], 1, accounts[2], 0), {'from': accounts[1], 'value': 0})
    assert_tx_failed(pack.functions.purchaseFor(pack_types['Rare'], accounts[3], 1, accounts[2], 0), {'from': accounts[1], 'value': pack_prices['Rare'] - 1})


def test_purchase_for_buying_0_cards(
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
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], "Rare bundle", "RB", 1, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    assert_tx_failed(pack.functions.purchaseFor(pack_types['Rare'], accounts[3], 0, accounts[2], 0), {'from': accounts[1], 'value': pack_prices['Rare']})

def test_purchase_bad_pack_type(
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
    tx_hash = pack.functions.setPack(pack_types['Epic'], pack_prices['Epic'], "Rare bundle", "RB", 1, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    assert_tx_failed(pack.functions.purchaseFor(5, accounts[3], 1, accounts[2], 0), {'from': accounts[1], 'value': pack_prices['Rare']})
    assert_tx_failed(pack.functions.purchaseFor(0, accounts[3], 1, accounts[2], 0), {'from': accounts[1], 'value': pack_prices['Rare']})
    assert_tx_failed(pack.functions.purchaseFor(2**8 - 1, accounts[3], 1, accounts[2], 0), {'from': accounts[1], 'value': pack_prices['Rare']})


def test_purchaseFor_refer_self(
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
    tx_hash = pack.functions.setPack(pack_types['Epic'], pack_prices['Epic'], "Rare bundle", "RB", 1, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    assert_tx_failed(pack.functions.purchaseFor(pack_types['Rare'], accounts[3], 1, accounts[3], 0), {'from': accounts[1], 'value': pack_prices['Rare']})
    assert_tx_failed(pack.functions.purchaseFor(pack_types['Rare'], accounts[3], 1, accounts[3], 0), {'from': accounts[0], 'value': pack_prices['Rare']})

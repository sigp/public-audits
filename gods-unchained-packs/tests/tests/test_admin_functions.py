import pytest
import random
from web3.contract import ConciseContract

def test_set_can_lockup(
        accounts,
        assert_tx_failed,
        instantiate,
        pack_deploy,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # setCanLockup is an ownerOnly function (owner: accounts[0])
    assert not pack.functions.canLockup(accounts[1]).call(), "default priviledge should be false"
    pack.functions.setCanLockup(accounts[1], True).transact({'from': accounts[0]})
    assert pack.functions.canLockup(accounts[1]).call(), "priviledge won't set"

    # Remove lockup priviledge
    pack.functions.setCanLockup(accounts[1], False).transact({'from': accounts[0]})
    assert not pack.functions.canLockup(accounts[1]).call(), "priviledge should be removed"

    # Repeating setting priviledge access should be valid
    pack.functions.setCanLockup(accounts[1], False).transact({'from': accounts[0]})
    assert not pack.functions.canLockup(accounts[1]).call(), "priviledge should set twice set"

    ## Invalid operations
    # Not owner
    assert_tx_failed(pack.functions.setCanLockup(accounts[1], True), {'from': accounts[1]})
    assert_tx_failed(pack.functions.setCanLockup(accounts[1], True), {'from': accounts[2]})


def test_set_can_revoke(
        accounts,
        assert_tx_failed,
        instantiate,
        pack_deploy,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # setCanRevoke is an ownerOnly function (owner: accounts[0])
    assert not pack.functions.canRevoke(accounts[1]).call(), "default priviledge should be false"
    pack.functions.setCanRevoke(accounts[1], True).transact({'from': accounts[0]})
    assert pack.functions.canRevoke(accounts[1]).call(), "priviledge won't set"

    # Remove revoke priviledge
    pack.functions.setCanRevoke(accounts[1], False).transact({'from': accounts[0]})
    assert not pack.functions.canRevoke(accounts[1]).call(), "priviledge should be removed"

    # Repeating setting priviledge access should be valid
    pack.functions.setCanRevoke(accounts[1], False).transact({'from': accounts[0]})
    assert not pack.functions.canRevoke(accounts[1]).call(), "priviledge should set twice set"

    ## Invalid operations
    # Not owner
    assert_tx_failed(pack.functions.setCanRevoke(accounts[1], True), {'from': accounts[1]})
    assert_tx_failed(pack.functions.setCanRevoke(accounts[1], True), {'from': accounts[2]})


def test_set_commit_lag(
        accounts,
        assert_tx_failed,
        instantiate,
        pack_deploy,
        ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # setCommitLag is an ownerOnly function (owner: accounts[0])
    pack.functions.setCommitLag(3).transact({'from': accounts[0]})
    assert pack.functions.commitLag().call() == 3, "cannot set commit lag"

    pack.functions.setCommitLag(0).transact({'from': accounts[0]})
    assert pack.functions.commitLag().call() == 0, "cannot reset commit lag"

    ## Invalid operations
    # Not owner
    assert_tx_failed(pack.functions.setCommitLag(1), {'from': accounts[1]})


def test_set_activation_limit(
        accounts,
        assert_tx_failed,
        get_receipt,
        instantiate,
        pack_deploy,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # setActivationLimit is an ownerOnly function (owner: accounts[0])
    pack.functions.setActivationLimit(30).transact({'from': accounts[0]})
    assert pack.functions.activationLimit().call() == 30, "Set activation limit to 30"
    # This was removed.
    #assert pack.functions.getActivationLimit().call() == 30, "get activation limit"

    pack.functions.setActivationLimit(0).transact({'from': accounts[0]})
    assert pack.functions.activationLimit().call() == 0, "Set activation limit to 0"

    ## Invalid operations
    # Not owner
    assert_tx_failed(pack.functions.setActivationLimit(10), {'from': accounts[1]})

def test_set_pack(
        accounts,
        assert_tx_failed,
        instantiate,
        get_logs_for_event,
        pack_deploy,
        pack_prices,
        pack_types,
        ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # setPack is an ownerOnly function (owner: accounts[0]), use dummy token accounts[0]
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], "Rare bundle", "RB", 1, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})
    pack_instance = pack.functions.packs(pack_types['Rare']).call()
    assert pack_instance[0] == pack_prices['Rare'], "pack price set incorrectly"
    assert pack_instance[1] == 1, "pack size set incorrectly"
    assert pack_instance[2] == rare_bundle.address, "pack token set incorrectly"

    ## Invalid operations
    # Not owner
    assert_tx_failed(pack.functions.setPack(pack_types['Epic'], pack_prices['Epic'], "Rare bundle", "RB", 1, 0), {'from': accounts[1]})
    # Cannot reset packs, is this deliberate cause it leaves no room for error
    assert_tx_failed(pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], "asdf asdf", "ASD", 2, 0), {'from': accounts[0]})
    # Bad Pack.Type
    assert_tx_failed(pack.functions.setPack(7, pack_prices['Epic'], "asdf asdf", "ASD", 1, 0), {'from': accounts[0]})
    # Price can't be 0
    assert_tx_failed(pack.functions.setPack(pack_types['Epic'], 0, "asdf asdf", "ASD", 1, 0), {'from': accounts[0]})

    ## Set remaing pack types
    tx_hash = pack.functions.setPack(pack_types['Epic'], pack_prices['Epic'], "Rare bundle", "RB", 2, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})
    pack_instance = pack.functions.packs(pack_types['Epic']).call()
    assert pack_instance[0] == pack_prices['Epic'], "pack price set incorrectly"
    assert pack_instance[1] == 2, "pack size set incorrectly"
    assert pack_instance[2] == rare_bundle.address, "pack token set incorrectly"

    tx_hash = pack.functions.setPack(pack_types['Legendary'], pack_prices['Legendary'], "Rare bundle", "RB", 2, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})
    pack_instance = pack.functions.packs(pack_types['Legendary']).call()
    assert pack_instance[0] == pack_prices['Legendary'], "pack price set incorrectly"
    assert pack_instance[1] == 2, "pack size set incorrectly"
    assert pack_instance[2] == rare_bundle.address, "pack token set incorrectly"

    tx = tx_hash = pack.functions.setPack(pack_types['Shiny'], pack_prices['Shiny'], "Rare bundle", "RB", 2, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})
    pack_instance = pack.functions.packs(pack_types['Shiny']).call()
    assert pack_instance[0] == pack_prices['Shiny'], "pack price set incorrectly"
    assert pack_instance[1] == 2, "pack size set incorrectly"
    assert pack_instance[2] == rare_bundle.address, "pack token set incorrectly"


def test_set_activate(
        accounts,
        assert_tx_failed,
        pack_deploy,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # setActivate is an ownerOnly function (owner: accounts[0])
    assert pack.functions.canActivate().call(), "canActivaate default to true"
    pack.functions.setActivate(False).transact({'from': accounts[0]})
    assert not pack.functions.canActivate().call(), "set canActivate to false"

    pack.functions.setActivate(True).transact({'from': accounts[0]})
    assert pack.functions.canActivate().call(), "set canActivate to true again"

    ## Invalid operations
    # Not owner
    assert_tx_failed(pack.functions.setActivate(True), {'from': accounts[1]})
    assert_tx_failed(pack.functions.setActivate(False), {'from': accounts[1]})

def test_can_activate_purchase(
        accounts,
        assert_tx_failed,
        ganache_mine_block,
        instantiate,
        get_logs_for_event,
        pack_deploy,
        pack_prices,
        pack_types,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # Set packs for purchase (bundle size = 1 -> price = pack_price['Rare'])
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], "Rare bundle", "RB", 1, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    # Give accounts[1] permissions to lockup and revoke
    pack.functions.setCanLockup(accounts[1], True).transact({'from': accounts[0]})
    pack.functions.setCanRevoke(accounts[1], True).transact({'from': accounts[0]})

    ## Valid cases
    # canActivate && lockup == 0,
    pack.functions.purchase(pack_types['Rare'], 1, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Rare']})
    purchaseID = 0
    assert pack.functions.canActivatePurchase(purchaseID).call()

    # canActivate && lockup > 0 && lockup + commit < blockheight
    pack.functions.purchaseFor(pack_types['Rare'], accounts[2], 1, accounts[3], 2).transact({'from': accounts[1], 'value': pack_prices['Rare']})
    purchaseID = 1
    ganache_mine_block(3) # need to increase blockheight by 3 for lockup + commit < blockheight
    assert pack.functions.canActivatePurchase(purchaseID).call()

    ## Invalid cases
    # Bad id
    assert_tx_failed(pack.functions.canActivatePurchase(3), {'from': accounts[2]})

    # Revoked purchase
    pack.functions.purchaseFor(pack_types['Rare'], accounts[2], 1, accounts[3], 1).transact({'from': accounts[1], 'value': pack_prices['Rare']})
    purchaseID = 2
    pack.functions.revoke(2).transact({'from': accounts[1]}) # inLockupPeriod == true
    assert not pack.functions.canActivatePurchase(purchaseID).call() # inLockupPeriod == false

    # inLockupPeriod is true
    pack.functions.purchaseFor(pack_types['Rare'], accounts[2], 1, accounts[3], 4).transact({'from': accounts[1], 'value': pack_prices['Rare']})
    purchaseID = 3
    assert not pack.functions.canActivatePurchase(purchaseID).call()

    # canActivate is false
    pack.functions.purchase(pack_types['Rare'], 1, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Rare']})
    purchaseID = 4
    pack.functions.setActivate(False).transact({'from': accounts[0]})
    assert not pack.functions.canActivatePurchase(purchaseID).call()

def test_revoke(
        accounts,
        assert_tx_failed,
        ganache_mine_block,
        get_logs_for_event,
        instantiate,
        pack_deploy,
        pack_prices,
        pack_types,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # Set pack and revoke and lockup permissions for accounts[1]
    tx_hash = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], "Rare bundle", "RB", 1, 0).transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})
    pack.functions.setCanLockup(accounts[1], True).transact({'from': accounts[0]})
    pack.functions.setCanRevoke(accounts[1], True).transact({'from': accounts[0]})

    lockup_period = 10

    ## Valid cases
    # Valid revoke
    pack.functions.purchaseFor(pack_types['Rare'], accounts[2], 1, accounts[3], lockup_period).transact({'from': accounts[1], 'value': pack_prices['Rare']})
    purchaseID = 0
    tx = pack.functions.revoke(purchaseID).transact({'from': accounts[1]})
    logs = get_logs_for_event(pack.events.PurchaseRevoked, tx)
    assert logs[0]['args']['paymentID'] == 0, "PurchaseRevoked, paymentID emitted wrong"
    assert logs[0]['args']['revoker'] == accounts[1], "PurchaseRevoked, revoker emitted wrong"


    ## Invalid cases
    # Already revoked purchase
    assert_tx_failed(pack.functions.revoke(purchaseID), {'from': accounts[1]})

    # Bad id
    assert_tx_failed(pack.functions.revoke(purchaseID + 10), {'from': accounts[1]})

    # inLockupPeriod is finished (i.e. false)
    pack.functions.purchaseFor(pack_types['Rare'], accounts[2], 1, accounts[3], lockup_period).transact({'from': accounts[1], 'value': pack_prices['Rare']})
    ganache_mine_block(lockup_period + 1)
    purchaseID = 1
    assert_tx_failed(pack.functions.revoke(purchaseID), {'from': accounts[1]})

    # Does not have permission to revoke
    pack.functions.purchaseFor(pack_types['Rare'], accounts[2], 1, accounts[3], lockup_period).transact({'from': accounts[1], 'value': pack_prices['Rare']})
    purchaseID = 2
    assert_tx_failed(pack.functions.revoke(purchaseID), {'from': accounts[3]})

    # lockup not set
    pack.functions.purchase(pack_types['Rare'], 1, accounts[2]).transact({'from': accounts[1], 'value': pack_prices['Rare']})
    purchaseID = 3
    assert_tx_failed(pack.functions.revoke(purchaseID), {'from': accounts[1]})

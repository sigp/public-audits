import pytest
import random
from web3.contract import ConciseContract

def test_referrals_override_split_valid(
        accounts,
        assert_tx_failed,
        get_logs_for_event,
        pack_deploy,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    ## Valid cases
    assert referrals.functions.getSplit(accounts[1]).call() == [0, 10], "default split"
    tx = referrals.functions.overrideSplit(accounts[1], 5 , 5).transact({'from': accounts[0]})
    assert referrals.functions.getSplit(accounts[1]).call() == [5, 5], "new split"
    logs = get_logs_for_event(referrals.events.SplitChanged, tx)
    assert logs[0]['args']['user'] == accounts[1]
    assert logs[0]['args']['discount'] == 5, "Set discount to 5"
    assert logs[0]['args']['referrer'] == 5, "Set referrer to 5"

    tx = referrals.functions.overrideSplit(accounts[1], 0 , 0).transact({'from': accounts[0]})
    assert referrals.functions.getSplit(accounts[1]).call() == [0, 0], "no discount or referral"

    tx = referrals.functions.overrideSplit(accounts[1], 10 , 0).transact({'from': accounts[0]})
    assert referrals.functions.getSplit(accounts[1]).call() == [10, 0], "no referral"

    tx = referrals.functions.overrideSplit(accounts[1], 0 , 10).transact({'from': accounts[0]})
    assert referrals.functions.getSplit(accounts[1]).call() == [0, 10], "no referral"


def test_referrals_override_split_invalid(
        accounts,
        assert_tx_failed,
        get_logs_for_event,
        pack_deploy,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # Overflows
    assert_tx_failed(referrals.functions.overrideSplit(accounts[1], 2, 2**8 - 1), {'from': accounts[0]})
    assert_tx_failed(referrals.functions.overrideSplit(accounts[1], 2**8 - 1, 2), {'from': accounts[0]})
    assert_tx_failed(referrals.functions.overrideSplit(accounts[1], 2**7 + 1, 2**7 + 1), {'from': accounts[0]})
    assert_tx_failed(referrals.functions.overrideSplit(accounts[1], 2**7 - 1, 2**7 + 1), {'from': accounts[0]})
    assert_tx_failed(referrals.functions.overrideSplit(accounts[1], 2**7 + 1, 2**7 - 1), {'from': accounts[0]})

    # Above discount limit
    assert_tx_failed(referrals.functions.overrideSplit(accounts[1], 9, 9), {'from': accounts[0]})
    assert_tx_failed(referrals.functions.overrideSplit(accounts[1], 11, 11), {'from': accounts[0]})
    assert_tx_failed(referrals.functions.overrideSplit(accounts[1], 2**8 - 1, 0), {'from': accounts[0]})
    assert_tx_failed(referrals.functions.overrideSplit(accounts[1], 0, 2**8 - 1), {'from': accounts[0]})

    # Not owner
    assert_tx_failed(referrals.functions.overrideSplit(accounts[1], 2, 2), {'from': accounts[1]})

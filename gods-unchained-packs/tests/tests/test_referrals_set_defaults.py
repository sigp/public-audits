import pytest
import random
from web3.contract import ConciseContract

def test_referrals_set_defaults_valid(
        accounts,
        pack_deploy,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    ## Valid cases
    assert referrals.functions.getSplit(accounts[1]).call() == [0, 10], "default split"
    tx = referrals.functions.setDefaults(5 , 5).transact({'from': accounts[0]})
    assert referrals.functions.getSplit(accounts[1]).call() == [5, 5], "default split"

    tx = referrals.functions.setDefaults(0 , 0).transact({'from': accounts[0]})
    assert referrals.functions.getSplit(accounts[1]).call() == [0, 0], "no discount or referral"

    tx = referrals.functions.setDefaults(10 , 0).transact({'from': accounts[0]})
    assert referrals.functions.getSplit(accounts[1]).call() == [10, 0], "no referral"

    tx = referrals.functions.setDefaults(0 , 10).transact({'from': accounts[0]})
    assert referrals.functions.getSplit(accounts[1]).call() == [0, 10], "no referral"


def test_referrals_set_defaults_invalid(
        accounts,
        assert_tx_failed,
        pack_deploy,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # Overflows
    assert_tx_failed(referrals.functions.setDefaults(2, 2**8 - 1), {'from': accounts[0]})
    assert_tx_failed(referrals.functions.setDefaults(2**8 - 1, 2), {'from': accounts[0]})
    assert_tx_failed(referrals.functions.setDefaults(2**7 + 1, 2**7 + 1), {'from': accounts[0]})
    assert_tx_failed(referrals.functions.setDefaults(2**7 - 1, 2**7 + 1), {'from': accounts[0]})
    assert_tx_failed(referrals.functions.setDefaults(2**7 + 1, 2**7 - 1), {'from': accounts[0]})

    # Above discount limit
    assert_tx_failed(referrals.functions.setDefaults(9, 9), {'from': accounts[0]})
    assert_tx_failed(referrals.functions.setDefaults(11, 11), {'from': accounts[0]})
    assert_tx_failed(referrals.functions.setDefaults(2**8 - 1, 0), {'from': accounts[0]})
    assert_tx_failed(referrals.functions.setDefaults(0, 2**8 - 1), {'from': accounts[0]})

    # Only owner
    assert_tx_failed(referrals.functions.setDefaults(0, 2), {'from': accounts[1]})

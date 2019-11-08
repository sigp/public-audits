import pytest
import random
from web3.contract import ConciseContract

def test_referrals_set_discount_limit_valid(
        accounts,
        pack_deploy,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    ## Valid cases
    referrals.functions.setDiscountLimit(0).transact({'from': accounts[0]})
    referrals.functions.setDiscountLimit(100).transact({'from': accounts[0]})
    referrals.functions.setDiscountLimit(99).transact({'from': accounts[0]})
    referrals.functions.setDiscountLimit(1).transact({'from': accounts[0]})


def test_referrals_set_discount_limit_invalid(
        accounts,
        assert_tx_failed,
        pack_deploy,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # Above discount limit
    assert_tx_failed(referrals.functions.setDiscountLimit(101), {'from': accounts[0]})
    assert_tx_failed(referrals.functions.setDiscountLimit(2**8 - 1), {'from': accounts[0]})

    # Only owner
    assert_tx_failed(referrals.functions.setDiscountLimit(100), {'from': accounts[1]})

def test_referrals_set_discount_limit_decrease(
        accounts,
        assert_tx_failed,
        pack_deploy,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    referrals.functions.setSplit(10 , 0).transact({'from': accounts[1]})
    referrals.functions.setDiscountLimit(1).transact({'from': accounts[0]})
    assert referrals.functions.getSplit(accounts[1]).call() == [10, 0], "Should remain unchanged"

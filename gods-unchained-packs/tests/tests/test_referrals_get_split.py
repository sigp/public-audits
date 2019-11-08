import pytest
import random
from web3.contract import ConciseContract

def test_referrals_get_split(
        accounts,
        assert_tx_failed,
        get_logs_for_event,
        pack_deploy,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    ## Initial Values
    zero_address = '0x' + '00' * 20
    assert referrals.functions.getSplit(zero_address).call() == [0, 0], "zero address split"
    assert referrals.functions.getSplit(accounts[1]).call() == [0, 10], "default split"

    tx = referrals.functions.setSplit(5 , 5).transact({'from': accounts[1]})
    assert referrals.functions.getSplit(accounts[1]).call() == [5, 5], "no discount or referral"

def test_referrals_get_split_above_discount(
        accounts,
        assert_tx_failed,
        get_logs_for_event,
        pack_deploy,
    ):

    # Deploy a PackFive and required supporting contracts (processor, referral, cards, vault)
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    referrals.functions.setDiscountLimit(90).transact({'from': accounts[0]})
    referrals.functions.setSplit(45, 45).transact({'from': accounts[1]})
    referrals.functions.setDiscountLimit(10).transact({'from': accounts[0]})

    assert referrals.functions.getSplit(accounts[1]).call() == [45, 45], "split above discount limit"

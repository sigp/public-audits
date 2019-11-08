import pytest

def test_processor_discount(accounts, pack_deploy):

    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    # Works
    referrals.functions.setSplit(0, 0).transact({'from': accounts[0]})
    assert referrals.functions.getSplit(accounts[0]).call() == [0, 0], "incorrect discount or referral 0"
    assert processor.functions.getAllocations(20, 5, accounts[0]).call() == [100, 0], "Incorrect allocations 0"


    # Works
    referrals.functions.setSplit(0, 5).transact({'from': accounts[1]})
    assert referrals.functions.getSplit(accounts[1]).call() == [0, 5], "incorrect discount or referral 1"
    assert processor.functions.getAllocations(20, 5, accounts[1]).call() == [95, 5], "Incorrect allocations 1"


    # Didn't work
    referrals.functions.setSplit(5, 5).transact({'from': accounts[2]})
    assert referrals.functions.getSplit(accounts[2]).call() == [5, 5], "incorrect discount or referral 2"
    assert processor.functions.getAllocations(20, 5, accounts[2]).call() == [90, 5], "Incorrect allocations 2"




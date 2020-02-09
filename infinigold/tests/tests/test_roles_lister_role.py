##################################################
# Functions for testing ListerRole Directly
##################################################

def test_is_lister(accounts, address_list_initialize_and_deploy, get_logs_for_event):
    # Deploy an AddressList with account[0] as owner
    (lister_role, lister_role_r) = address_list_initialize_and_deploy("List")

    # Add account[1] as ListerAdmin
    lister_role.functions.addListerAdmin(accounts[1]).transact({'from': accounts[0]})

    # Add account[2] as Lister
    lister_role.functions.addLister(accounts[2]).transact({'from': accounts[1]})
    lister_role.functions.addLister(accounts[3]).transact({'from': accounts[1]})
    assert lister_role.functions.isLister(accounts[2]).call()
    assert lister_role.functions.isLister(accounts[3]).call()

    # Remove accounts[3]
    lister_role.functions.removeLister(accounts[3]).transact({'from': accounts[1]})
    assert lister_role.functions.isLister(accounts[2]).call()
    assert not lister_role.functions.isLister(accounts[3]).call()

def test_add_lister(accounts, address_list_initialize_and_deploy, assert_tx_failed, get_logs_for_event, zero_address):
    # Deploy an AddressList with account[0] as owner
    (lister_role, lister_role_r) = address_list_initialize_and_deploy("List")

    # Add account[1] as ListerAdmin
    lister_role.functions.addListerAdmin(accounts[1]).transact({'from': accounts[0]})

    # Add account[2] as Lister
    tx = lister_role.functions.addLister(accounts[2]).transact({'from': accounts[1]})
    assert lister_role.functions.isLister(accounts[2]).call()
    logs = get_logs_for_event(lister_role.events.ListerAdded, tx)
    assert logs[0]['args']['account'] == accounts[2]

    # Add account[3] as Lister
    tx = lister_role.functions.addLister(accounts[3]).transact({'from': accounts[1]})
    assert lister_role.functions.isLister(accounts[3]).call()
    logs = get_logs_for_event(lister_role.events.ListerAdded, tx)
    assert logs[0]['args']['account'] == accounts[3]

    # Add lister when not admin
    assert_tx_failed(lister_role.functions.addLister(accounts[0]), {'from': accounts[0]})
    assert_tx_failed(lister_role.functions.addLister(accounts[4]), {'from': accounts[2]})

    # Add lister when already added
    assert_tx_failed(lister_role.functions.addLister(accounts[2]), {'from': accounts[1]})
    assert_tx_failed(lister_role.functions.addLister(accounts[3]), {'from': accounts[1]})

    # Add zero_address
    assert_tx_failed(lister_role.functions.addLister(zero_address), {'from': accounts[1]})


def test_remove_lister(accounts, address_list_initialize_and_deploy, assert_tx_failed, get_logs_for_event):
    # Deploy an AddressList with account[0] as owner
    (lister_role, lister_role_r) = address_list_initialize_and_deploy("List")

    # Add account[1] as ListerAdmin
    lister_role.functions.addListerAdmin(accounts[1]).transact({'from': accounts[0]})

    # Add account[2 and 3] as Listers
    lister_role.functions.addLister(accounts[2]).transact({'from': accounts[1]})
    lister_role.functions.addLister(accounts[3]).transact({'from': accounts[1]})

    # Remove account[3] as Lister
    tx = lister_role.functions.removeLister(accounts[3]).transact({'from': accounts[1]})
    assert not lister_role.functions.isLister(accounts[3]).call()
    logs = get_logs_for_event(lister_role.events.ListerRemoved, tx)
    assert logs[0]['args']['account'] == accounts[3]

    # Remove lister when not admin
    assert_tx_failed(lister_role.functions.removeLister(accounts[2]), {'from': accounts[0]})
    assert_tx_failed(lister_role.functions.removeLister(accounts[2]), {'from': accounts[2]})

    # Remove account that is not a lister
    assert_tx_failed(lister_role.functions.removeLister(accounts[4]), {'from': accounts[1]})
    assert_tx_failed(lister_role.functions.removeLister(accounts[3]), {'from': accounts[1]})


def test_replace_lister(accounts, address_list_initialize_and_deploy, assert_tx_failed, get_logs_for_event):
    # Deploy an AddressList with account[0] as owner
    (lister_role, lister_role_r) = address_list_initialize_and_deploy("List")

    # Add account[1] as ListerAdmin
    lister_role.functions.addListerAdmin(accounts[1]).transact({'from': accounts[0]})

    # Add account[2 and 3] as Listers
    lister_role.functions.addLister(accounts[2]).transact({'from': accounts[1]})
    lister_role.functions.addLister(accounts[3]).transact({'from': accounts[1]})

    # Replace account[3] with accounts[4]
    tx = lister_role.functions.replaceLister(accounts[3], accounts[4]).transact({'from': accounts[1]})
    assert not lister_role.functions.isLister(accounts[3]).call()
    assert lister_role.functions.isLister(accounts[4]).call()
    logs = get_logs_for_event(lister_role.events.ListerRemoved, tx)
    assert logs[0]['args']['account'] == accounts[3]
    logs = get_logs_for_event(lister_role.events.ListerAdded, tx)
    assert logs[0]['args']['account'] == accounts[4]

    # Remove lister when not admin
    assert_tx_failed(lister_role.functions.replaceLister(accounts[4], accounts[5]), {'from': accounts[0]})

    # Replace account that is not a lister (accounts[3] is no longer a lister)
    assert_tx_failed(lister_role.functions.replaceLister(accounts[3], accounts[5]), {'from': accounts[1]})

    # Replace a lister with an account that is already a lister
    assert_tx_failed(lister_role.functions.replaceLister(accounts[5], accounts[4]), {'from': accounts[1]})

def test_size(accounts, address_list_initialize_and_deploy, assert_tx_failed, get_logs_for_event):
    # Deploy an AddressList with account[0] as owner
    (lister_role, lister_role_r) = address_list_initialize_and_deploy("List")

    # Add account[1] as ListerAdmin
    lister_role.functions.addListerAdmin(accounts[1]).transact({'from': accounts[0]})

    # Add account[2 and 3] as Listers
    assert lister_role.functions.numberOfListers().call() == 0
    lister_role.functions.addLister(accounts[2]).transact({'from': accounts[1]})
    assert lister_role.functions.numberOfListers().call() == 1
    lister_role.functions.addLister(accounts[3]).transact({'from': accounts[1]})
    assert lister_role.functions.numberOfListers().call() == 2

    lister_role.functions.replaceLister(accounts[3], accounts[4]).transact({'from': accounts[1]})
    assert lister_role.functions.numberOfListers().call() == 2
    lister_role.functions.removeLister(accounts[4]).transact({'from': accounts[1]})
    assert lister_role.functions.numberOfListers().call() == 1

def test_to_array(accounts, address_list_initialize_and_deploy):
    # Deploy an AddressList with account[0] as owner
    (lister_role, lister_role_r) = address_list_initialize_and_deploy("List")

    # Add account[1] as ListerAdmin
    lister_role.functions.addListerAdmin(accounts[1]).transact({'from': accounts[0]})

    # Linked list is empty
    assert lister_role.functions.listers().call() == []

    # Linked list accounts[2]
    lister_role.functions.addLister(accounts[2]).transact({'from': accounts[1]})
    assert lister_role.functions.listers().call() == [accounts[2]]

    # Linked list accounts[2, 3]
    lister_role.functions.addLister(accounts[3]).transact({'from': accounts[1]})
    assert lister_role.functions.listers().call() == [accounts[3], accounts[2]]

    # Linked list accounts[2, 3(inactive), 4]
    lister_role.functions.replaceLister(accounts[3], accounts[4]).transact({'from': accounts[1]})
    assert lister_role.functions.listers().call() == [accounts[4], accounts[2]]

    # Linked list accounts[2, 3, 4]
    lister_role.functions.addLister(accounts[3]).transact({'from': accounts[1]})
    assert lister_role.functions.listers().call() == [accounts[4], accounts[3], accounts[2]]

    # Linked list accounts[2, 3, 4(inactive)]
    lister_role.functions.removeLister(accounts[4]).transact({'from': accounts[1]})
    assert lister_role.functions.listers().call() == [accounts[3], accounts[2]]

def test_replace_all(accounts, address_list_initialize_and_deploy, get_logs_for_event):
    # Deploy an AddressList with account[0] as owner
    (lister_role, lister_role_r) = address_list_initialize_and_deploy("List")

    # Add account[1] as ListerAdmin
    lister_role.functions.addListerAdmin(accounts[1]).transact({'from': accounts[0]})

    # Setup linked list with accounts(2, 3(inactive), 4)
    lister_role.functions.addLister(accounts[2]).transact({'from': accounts[1]})
    lister_role.functions.addLister(accounts[3]).transact({'from': accounts[1]})
    lister_role.functions.replaceLister(accounts[3], accounts[4]).transact({'from': accounts[1]})

    # Replace all with empty
    tx = lister_role.functions.replaceAllListers([]).transact({'from': accounts[1]})
    assert lister_role.functions.numberOfListers().call() == 0
    logs = get_logs_for_event(lister_role.events.ListerRemoved, tx)
    assert logs[0]['args']['account'] == accounts[4]
    assert logs[1]['args']['account'] == accounts[2]

def test_replace_all_max(accounts, address_list_initialize_and_deploy, assert_tx_failed, get_logs_for_event, w3):
    # Deploy an AddressList with account[0] as owner
    (lister_role, lister_role_r) = address_list_initialize_and_deploy("List")

    # Add account[1] as ListerAdmin
    lister_role.functions.addListerAdmin(accounts[1]).transact({'from': accounts[0]})

    # Setup linked list with accounts(2, 3, ... 101) that is 100 accounts
    for i in range(0, 100):
        lister_role.functions.addLister(accounts[i + 2]).transact({'from': accounts[1]})

    # Replace all with empty
    tx = lister_role.functions.replaceAllListers([]).transact({'from': accounts[1]})
    lister_role.functions.numberOfListers().call() == 0
    logs = get_logs_for_event(lister_role.events.ListerRemoved, tx)
    assert len(logs) == 100
    # Ensure gas used is in valid range
    assert w3.eth.getTransactionReceipt(tx)['gasUsed'] < 8e6

def test_replace_all_gas_limit(accounts, address_list_initialize_and_deploy, assert_tx_gas_failed, w3):
    # Deploy an AddressList with account[0] as owner
    (lister_role, lister_role_r) = address_list_initialize_and_deploy("List")

    # Add account[1] as ListerAdmin
    lister_role.functions.addListerAdmin(accounts[1]).transact({'from': accounts[0]})

    # Setup linked list with accounts(2, 3, ... 100000001) that is 100 accounts
    lister_role.functions.addLister(accounts[2]).transact({'from': accounts[1]})
    for i in range(1, 372):
        lister_role.functions.addLister(accounts[i + 2]).transact({'from': accounts[1]})
        lister_role.functions.removeLister(accounts[i + 2]).transact({'from': accounts[1]})

    # Note the current gas limit is about 8 million which
    # it is reach when deleting around 450 nodes in the linked list
    assert_tx_gas_failed(lister_role.functions.replaceAllListers([]), {'from': accounts[1]})
    #assert w3.eth.getTransactionReceipt(tx)['gasUsed'] < 8e6

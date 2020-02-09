def test_address_list(
        token_impl_deploy,
        accounts,
        address_list_initialize_and_deploy,
        get_logs_for_event):

    # Deploy an AddressList with
    # accounts[0] as Owner, accounts[1] as ListerAdmin, accounts[2] as Lister
    (list, list_r) = address_list_initialize_and_deploy("list")
    list.functions.addListerAdmin(accounts[1]).transact({'from': accounts[0]})
    list.functions.addLister(accounts[2]).transact({'from': accounts[1]})
    list.functions.addUnlister(accounts[2]).transact({'from': accounts[1]})

    # Add accounts[3] to list
    tx = list.functions.addAddress(accounts[3]).transact({'from': accounts[2]})
    assert list.functions.onList(accounts[3]).call()
    logs = get_logs_for_event(list.events.AddressAdded, tx)
    assert logs[0]['args']['account'] == accounts[3]

    # Remove accounts[3] to list
    tx = list.functions.removeAddress(accounts[3]).transact({'from': accounts[2]})
    assert not list.functions.onList(accounts[3]).call()
    logs = get_logs_for_event(list.events.AddressRemoved, tx)
    assert logs[0]['args']['account'] == accounts[3]

    # Add the remove accounts[3] and accounts[4]
    tx = list.functions.addAddress(accounts[3]).transact({'from': accounts[2]})
    assert list.functions.onList(accounts[3]).call()
    tx = list.functions.addAddress(accounts[4]).transact({'from': accounts[2]})
    assert list.functions.onList(accounts[4]).call()
    tx = list.functions.removeAddress(accounts[3]).transact({'from': accounts[2]})
    assert not list.functions.onList(accounts[3]).call()
    tx = list.functions.removeAddress(accounts[4]).transact({'from': accounts[2]})
    assert not list.functions.onList(accounts[4]).call()

def test_address_list_invalid(
        token_impl_deploy,
        accounts,
        address_list_initialize_and_deploy,
        assert_tx_failed,
        get_logs_for_event):

    # Deploy an AddressList with
    # accounts[0] as Owner, accounts[1] as ListerAdmin, accounts[2] as Lister
    (list, list_r) = address_list_initialize_and_deploy("list")
    list.functions.addListerAdmin(accounts[1]).transact({'from': accounts[0]})
    list.functions.addLister(accounts[2]).transact({'from': accounts[1]})

    # Already on list
    list.functions.addAddress(accounts[3]).transact({'from': accounts[2]})
    assert_tx_failed(list.functions.addAddress(accounts[3]), {'from': accounts[2]})

    # Not a lister
    assert_tx_failed(list.functions.addAddress(accounts[4]), {'from': accounts[4]})

    # Not on the list
    assert_tx_failed(list.functions.removeAddress(accounts[4]), {'from': accounts[2]})

def test_address_list_name(
        token_impl_deploy,
        accounts,
        address_list_initialize_and_deploy,
        assert_tx_failed,
        get_logs_for_event):

    # Deploy an AddressList with
    # accounts[0] as Owner, accounts[1] as ListerAdmin, accounts[2] as Lister
    (list, list_r) = address_list_initialize_and_deploy('list')
    list.functions.addListerAdmin(accounts[1]).transact({'from': accounts[0]})

    assert list.functions.name().call() == 'list'

    # Update name
    list.functions.updateName('newName').transact({'from': accounts[1]})
    assert list.functions.name().call() == 'newName'

    # Not a listerAdmin
    assert_tx_failed(list.functions.updateName('Cheeky'), {'from': accounts[3]})

def test_address_list_replace(
        token_impl_deploy,
        accounts,
        address_list_initialize_and_deploy,
        assert_tx_failed,
        get_logs_for_event):

    # Deploy an AddressList with
    # accounts[0] as Owner, accounts[1] as ListerAdmin, accounts[2] as Lister and Unlister
    (list, list_r) = address_list_initialize_and_deploy("list")
    list.functions.addListerAdmin(accounts[1]).transact({'from': accounts[0]})
    list.functions.addLister(accounts[2]).transact({'from': accounts[1]})
    list.functions.addUnlister(accounts[2]).transact({'from': accounts[1]})

    # Adds accounts[3] to the list:

    list.functions.addAddress(accounts[3]).transact({'from': accounts[2]})

    # Replace accounts[3] with accounts[4]
    list.functions.replaceAddress(accounts[3], accounts[4]).transact({'from': accounts[2]})

    assert list.functions.onList(accounts[4]).call() == 1

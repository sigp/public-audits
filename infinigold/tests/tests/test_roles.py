### Contains tests for each role in TokenImpl, AddressList and BalanceSheet/AllowanceSheet

##################################################
# Functions for testing MinterRole and MinterAdmin
##################################################
def test_minter_admin_role(accounts, assert_tx_failed, get_logs_for_event, token_proxy_initialize_and_deploy):
    # Deploy a proxy of TokenImpl with account[0] as owner
    (token_proxy_as_impl, token_proxy) = token_proxy_initialize_and_deploy("Infinigold", "IFG", 2)

    ### Valid MinterAdminRole Operations
    # Add account[1] as MinterAdmin
    tx = token_proxy_as_impl.functions.addMinterAdmin(accounts[1]).transact({'from': accounts[0]})
    assert token_proxy_as_impl.functions.isMinterAdmin(accounts[1]).call()
    logs = get_logs_for_event(token_proxy_as_impl.events.MinterAdminAdded, tx)
    assert logs[0]['args']['account'] == accounts[1]

    # Remove minterAdminRole
    tx = token_proxy_as_impl.functions.removeMinterAdmin(accounts[1]).transact({'from': accounts[0]})
    assert not token_proxy_as_impl.functions.isMinterAdmin(accounts[1]).call()
    logs = get_logs_for_event(token_proxy_as_impl.events.MinterAdminRemoved, tx)
    assert logs[0]['args']['account'] == accounts[1]


    ### Invalid MinterAdminRole Operations
    token_proxy_as_impl.functions.addMinterAdmin(accounts[1]).transact({'from': accounts[0]})
    # Add MinterAdmin without permission
    assert_tx_failed(token_proxy_as_impl.functions.addMinterAdmin(accounts[1]), {'from': accounts[1]})

    # Remove MinterAdmin without permission
    assert_tx_failed(token_proxy_as_impl.functions.removeMinterAdmin(accounts[0]), {'from': accounts[1]})

def test_minter_role(token_proxy_initialize_and_deploy, accounts, assert_tx_failed, get_logs_for_event):
    # Deploy a proxy of TokenImpl with account[0] as owner
    (token_proxy_as_impl, token_proxy) = token_proxy_initialize_and_deploy("Infinigold", "IFG", 2)

    # Add account[1] as MinterAdmin
    token_proxy_as_impl.functions.addMinterAdmin(accounts[1]).transact({'from': accounts[0]})

    ### Valid MinterRole Operations
    # Add account[2] as Minter
    tx = token_proxy_as_impl.functions.addMinter(accounts[2]).transact({'from': accounts[1]})
    assert token_proxy_as_impl.functions.isMinter(accounts[2]).call()
    logs = get_logs_for_event(token_proxy_as_impl.events.MinterAdded, tx)
    assert logs[0]['args']['account'] == accounts[2]

    # Remove accounts[2] as Minter
    tx = token_proxy_as_impl.functions.removeMinter(accounts[2]).transact({'from': accounts[1]})
    assert not token_proxy_as_impl.functions.isMinter(accounts[2]).call()
    logs = get_logs_for_event(token_proxy_as_impl.events.MinterRemoved, tx)
    assert logs[0]['args']['account'] == accounts[2]


    ### Invalid MinterRole Opertaions
    # Add minter when not admin (including owner)
    assert_tx_failed(token_proxy_as_impl.functions.addMinter(accounts[0]), {'from': accounts[0]})
    assert_tx_failed(token_proxy_as_impl.functions.addMinter(accounts[2]), {'from': accounts[2]})

    # Remove minter when not admin (including owner)
    assert_tx_failed(token_proxy_as_impl.functions.removeMinter(accounts[1]), {'from': accounts[0]})
    assert_tx_failed(token_proxy_as_impl.functions.removeMinter(accounts[1]), {'from': accounts[2]})

##################################################
# Functions for testing PauserRole and PauserAdmin
##################################################
def test_pauser_admin_role(token_proxy_initialize_and_deploy, accounts, assert_tx_failed, get_logs_for_event):
    # Deploy a proxy of TokenImpl with account[0] as owner
    (token_proxy_as_impl, token_proxy) = token_proxy_initialize_and_deploy("Infinigold", "IFG", 2)

    ### Valid PauserAdminRole Operations
    # Add account[1] as PauserAdmin
    tx = token_proxy_as_impl.functions.addPauserAdmin(accounts[1]).transact({'from': accounts[0]})
    assert token_proxy_as_impl.functions.isPauserAdmin(accounts[1]).call()
    logs = get_logs_for_event(token_proxy_as_impl.events.PauserAdminAdded, tx)
    assert logs[0]['args']['account'] == accounts[1]

    tx = token_proxy_as_impl.functions.removePauserAdmin(accounts[1]).transact({'from': accounts[0]})
    assert not token_proxy_as_impl.functions.isPauserAdmin(accounts[1]).call()
    logs = get_logs_for_event(token_proxy_as_impl.events.PauserAdminRemoved, tx)
    assert logs[0]['args']['account'] == accounts[1]


    ### Invalid PauserAdminRole Operations
    token_proxy_as_impl.functions.addPauserAdmin(accounts[1]).transact({'from': accounts[0]})
    # Add PauserAdmin without permission
    assert_tx_failed(token_proxy_as_impl.functions.addPauserAdmin(accounts[1]), {'from': accounts[1]})

    # Remove PauserAdmin without permission
    assert_tx_failed(token_proxy_as_impl.functions.removePauserAdmin(accounts[0]), {'from': accounts[1]})

def test_pauser_role(token_proxy_initialize_and_deploy, accounts, assert_tx_failed, get_logs_for_event):
    # Deploy a proxy of TokenImpl with account[0] as owner
    (token_proxy_as_impl, token_proxy) = token_proxy_initialize_and_deploy("Infinigold", "IFG", 2)

    # Add account[1] as PauserAdmin
    token_proxy_as_impl.functions.addPauserAdmin(accounts[1]).transact({'from': accounts[0]})

    ### Valid PauserRole Operations
    # Add account[2] as Pauser
    tx = token_proxy_as_impl.functions.addPauser(accounts[2]).transact({'from': accounts[1]})
    assert token_proxy_as_impl.functions.isPauser(accounts[2]).call()
    logs = get_logs_for_event(token_proxy_as_impl.events.PauserAdded, tx)
    assert logs[0]['args']['account'] == accounts[2]

    # Remove accounts[2] as Pauser
    tx = token_proxy_as_impl.functions.removePauser(accounts[2]).transact({'from': accounts[1]})
    assert not token_proxy_as_impl.functions.isPauser(accounts[2]).call()
    logs = get_logs_for_event(token_proxy_as_impl.events.PauserRemoved, tx)
    assert logs[0]['args']['account'] == accounts[2]

    ### Invalid PauserRole Opertaions
    # Add pauser when not admin (including owner)
    assert_tx_failed(token_proxy_as_impl.functions.addPauser(accounts[0]), {'from': accounts[0]})
    assert_tx_failed(token_proxy_as_impl.functions.addPauser(accounts[2]), {'from': accounts[2]})

    # Remove pauser when not admin (including owner)
    assert_tx_failed(token_proxy_as_impl.functions.removePauser(accounts[1]), {'from': accounts[0]})
    assert_tx_failed(token_proxy_as_impl.functions.removePauser(accounts[1]), {'from': accounts[2]})

##################################################
# Functions for testing ListerRole and ListerAdmin
##################################################
def test_lister_admin_role(address_list_initialize_and_deploy, accounts, assert_tx_failed, get_logs_for_event):
    # Deploy an AddressList with account[0] as owner
    (address_list, address_list_r) = address_list_initialize_and_deploy("list")

    ### Valid ListerAdminRole Operations
    # Add account[1] as ListerAdmin
    tx = address_list.functions.addListerAdmin(accounts[1]).transact({'from': accounts[0]})
    assert address_list.functions.isListerAdmin(accounts[1]).call()
    logs = get_logs_for_event(address_list.events.ListerAdminAdded, tx)
    assert logs[0]['args']['account'] == accounts[1]

    tx = address_list.functions.removeListerAdmin(accounts[1]).transact({'from': accounts[0]})
    assert not address_list.functions.isListerAdmin(accounts[1]).call()
    logs = get_logs_for_event(address_list.events.ListerAdminRemoved, tx)
    assert logs[0]['args']['account'] == accounts[1]


    ### Invalid ListerAdminRole Operations
    address_list.functions.addListerAdmin(accounts[1]).transact({'from': accounts[0]})
    # Add ListerAdmin without permission
    assert_tx_failed(address_list.functions.addListerAdmin(accounts[1]), {'from': accounts[1]})

    # Remove ListerAdmin without permission
    assert_tx_failed(address_list.functions.removeListerAdmin(accounts[0]), {'from': accounts[1]})

def test_lister_role(address_list_initialize_and_deploy, accounts, assert_tx_failed, get_logs_for_event):
    # Deploy an AddressList with account[0] as owner
    (address_list, address_list_r) = address_list_initialize_and_deploy("Infinigold")

    # Add account[1] as ListerAdmin
    address_list.functions.addListerAdmin(accounts[1]).transact({'from': accounts[0]})

    ### Valid ListerRole Operations
    # Add account[2] as Lister
    tx = address_list.functions.addLister(accounts[2]).transact({'from': accounts[1]})
    assert address_list.functions.isLister(accounts[2]).call()
    logs = get_logs_for_event(address_list.events.ListerAdded, tx)
    assert logs[0]['args']['account'] == accounts[2]

    # Remove accounts[2] as Lister
    tx = address_list.functions.removeLister(accounts[2]).transact({'from': accounts[1]})
    assert not address_list.functions.isLister(accounts[2]).call()
    logs = get_logs_for_event(address_list.events.ListerRemoved, tx)
    assert logs[0]['args']['account'] == accounts[2]

    ### Invalid ListerRole Opertaions
    # Add lister when not admin (including owner)
    assert_tx_failed(address_list.functions.addLister(accounts[0]), {'from': accounts[0]})
    assert_tx_failed(address_list.functions.addLister(accounts[2]), {'from': accounts[2]})

    # Remove lister when not admin (including owner)
    assert_tx_failed(address_list.functions.removeLister(accounts[1]), {'from': accounts[0]})
    assert_tx_failed(address_list.functions.removeLister(accounts[1]), {'from': accounts[2]})

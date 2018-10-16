

def test_token_transfer(accounts, send_eth, get_balance,
                        deploy,
                        multisig_deploy,
                        multisig_submitTransaction,
                        multisig_confirmTransaction,
                        multisig_confirmationCount):

    owner_count = 1
    owners = accounts[0:owner_count]
    required_confirmations = owner_count
    value = 42
    token_owner = accounts[-1]
    recipient = accounts[-2]

    (c, _) = multisig_deploy(
        owners=owners,
        required=required_confirmations,
        recoveryModeTriggerTime=2 * 60**2   # 2 hours
    )

    (t, _) = deploy('ERC20', {'from': token_owner}, {
        '_initialAmount': 100 * 10**8,
        '_tokenName': "ERC20 Test Contract",
        '_decimalUnits': 8,
        '_tokenSymbol': "ERC"
    })

    # Transfer tokens to the contract
    t.functions.transfer(c.address, value).transact({'from': token_owner})
    assert t.functions.balanceOf(c.address).call() == value
    assert t.functions.balanceOf(recipient).call() == 0

    # Build the data required for an ERC20 transfer
    transfer_tx = t.functions.transfer(recipient, value).buildTransaction({
        'from': c.address
    })

    transaction = {
        'destination': t.address,
        'value': 0,
        'data': transfer_tx['data']
    }

    multisig_submitTransaction(
        contract=c,
        transaction=transaction,
        from_addr=accounts[0]
    )

    assert t.functions.balanceOf(c.address).call() == 0
    assert t.functions.balanceOf(recipient).call() == value

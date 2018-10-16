def test_deploys(accounts, deploy_multisig):
    # c: contract, r: tx_receipt
    (c, r) = deploy_multisig(
        owners=[accounts[0]],
        required=1,
        recoveryModeTriggerTime=1000
    )
    print("Gas to deploy: {:,}".format(r.cumulativeGasUsed))


def test_params_instantiated(accounts, deploy_multisig):
    owners = accounts[0:5]
    required = 3
    recover = 1234
    (c, _) = deploy_multisig(
        owners=owners,
        required=required,
        recoveryModeTriggerTime=recover
    )
    assert(c.functions.required().call() == required)
    assert(c.functions.recoveryModeTriggerTime().call() == recover)
    for (i, o) in enumerate(owners):
        assert(c.functions.owners(i).call() == o)


def test_wont_deploy_with_invalid_required_count(accounts, deploy_multisig,
                                                 assert_tx_failed):
    assert_tx_failed(
        lambda: deploy_multisig(
            owners=[accounts[0]],
            required=2,
            recoveryModeTriggerTime=100
        )
    )

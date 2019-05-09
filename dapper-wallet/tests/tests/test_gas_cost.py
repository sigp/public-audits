import pytest


@pytest.mark.parametrize(
    "num_remove",
    [
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
    ]
)
def test_gas_saving_with_account_clearing(
        fullwallet_deploy,
        accounts,
        invoke_data,
        gascheck_deploy,
        num_remove,
        w3):

    # Set up
    authorized = accounts[1]
    cosigner = accounts[1]
    recovery = accounts[3]

    (wallet, _, _) = fullwallet_deploy(
        authorized,
        cosigner,
        recovery
    )

    (gas_c, _) = gascheck_deploy(wallet.address)

    # Authorize a number of addresses
    for acc in accounts[10:21]:
        args_encoded = wallet.encodeABI(
            fn_name='setAuthorized',
            args=[acc, int(acc, 0)]
        )

        data = invoke_data(1, wallet.address, 0, bytes.fromhex(args_encoded[2:]))
        wallet.functions.invoke0(data).transact({'from': accounts[1]})

    # EmergencyRecover
    wallet.functions.emergencyRecovery(
        accounts[2],
        int(accounts[2], 0)
    ).transact({'from': recovery})

    # Ensure the version has changed to 2
    assert wallet.functions.authVersion().call() == (2 << 160)

    tx = gas_c.functions.useGas(accounts[10:10 + num_remove]).transact({'from': accounts[4]})
    tx_receipt = w3.eth.getTransactionReceipt(tx.hex())

    print("{} Accounts: {}".format(num_remove, tx_receipt['gasUsed']))

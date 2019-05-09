import pytest
from .conftest import ACCOUNTS

@pytest.mark.parametrize(
    "deployer_account, random_account",
    [
        (ACCOUNTS[0], ACCOUNTS[1]),
        (ACCOUNTS[0], ACCOUNTS[0])
    ]
)
def test_cloned_wallet_fails(
        cloneable_wallet_deploy,
        deployer_account,
        assert_sendtx_failed,
        assert_tx_failed,
        random_account,
        w3
    ):
    (wallet_c, wallet_r) = cloneable_wallet_deploy()

    # Double check it was cloned correctly
    assert wallet_c.functions.initialized().call() is True, "Cloneable wallet isn't `Initialized`"
    assert wallet_c.functions.VERSION().call() == '1.0.0', "Cloneable wallet `VERSION` is not correct"

    # Money in from deployer
    money_in_tx = w3.eth.sendTransaction({
        'to': wallet_c.address,
        'from': random_account,
        'value': w3.toWei(5, 'ether')})
    money_in_rcpt = w3.eth.waitForTransactionReceipt(money_in_tx)

    # Validate that the cloneable wallet's balance was increased by the value transfered
    assert w3.eth.getBalance(wallet_c.address) == 5*10**18

    # Money in from deployer (with data)
    assert_sendtx_failed({
         'to': wallet_c.address,
         'from': random_account,
         'value': w3.toWei(5, 'ether'),
         'data': w3.toHex(text='some data asdf')
    })

    assert_tx_failed(
        wallet_c.functions.init(deployer_account, int(deployer_account, 0),random_account),
        {'from': deployer_account}
    )
    assert_tx_failed(
        wallet_c.functions.init(deployer_account, int(random_account, 0), random_account),
        {'from': deployer_account}
    )
    assert_tx_failed(
        wallet_c.functions.init(random_account, int(random_account, 0), random_account),
        {'from': deployer_account}
    )
    assert_tx_failed(
        wallet_c.functions.init(random_account, int(deployer_account, 0), random_account),
        {'from': deployer_account}
    )




def test_clonable_wallet(
        cloneable_wallet_deploy,
        assert_tx_failed,
        accounts,
        zero_address,
        calc_func_sig):

    # Set up
    deployer = accounts[0]
    authorized = accounts[1]
    cosigner = accounts[1]
    recovery = accounts[3]

    (cloneable_c, rcpt) = cloneable_wallet_deploy()

    assert cloneable_c.functions.initialized().call() is True, "Cloneable wallet isn't `Initialized`"
    assert cloneable_c.functions.VERSION().call() == '1.0.0', "Cloneable wallet `VERSION` is not correct"
    assert cloneable_c.functions.authVersion().call() == 0, "Cloneable wallet `authVersion` should be zero"
    assert cloneable_c.functions.recoveryAddress().call() == zero_address, "Cloneable wallet should not have a recoveryAddress"

    # Should not be able to call any functions on the clonable instance
    assert_tx_failed(cloneable_c.functions.init(authorized, int(cosigner, 0), recovery), {'from': deployer})
    assert_tx_failed(cloneable_c.functions.init(authorized, int(cosigner, 0), recovery), {'from': authorized})
    assert_tx_failed(cloneable_c.functions.init(authorized, int(cosigner, 0), recovery), {'from': recovery})
    assert_tx_failed(cloneable_c.functions.setRecoveryAddress(recovery), {'from': deployer})
    assert_tx_failed(cloneable_c.functions.setRecoveryAddress(recovery), {'from': authorized})
    assert_tx_failed(cloneable_c.functions.emergencyRecovery(recovery, int(cosigner, 0)), {'from': deployer})
    assert_tx_failed(cloneable_c.functions.emergencyRecovery(recovery, int(cosigner, 0)), {'from': authorized})
    assert_tx_failed(cloneable_c.functions.setAuthorized(recovery, int(cosigner, 0)), {'from': authorized})
    assert_tx_failed(cloneable_c.functions.setAuthorized(cosigner, int(cosigner, 0)), {'from': authorized})
    assert_tx_failed(cloneable_c.functions.setAuthorized(recovery, int(recovery, 0)), {'from': authorized})
    assert_tx_failed(cloneable_c.functions.setAuthorized(cosigner, int(recovery, 0)), {'from': authorized})
    assert_tx_failed(cloneable_c.functions.setAuthorized(recovery, int(cosigner, 0)), {'from': recovery})
    assert_tx_failed(cloneable_c.functions.setAuthorized(cosigner, int(cosigner, 0)), {'from': recovery})
    assert_tx_failed(cloneable_c.functions.setAuthorized(recovery, int(recovery, 0)), {'from': recovery})
    assert_tx_failed(cloneable_c.functions.setAuthorized(cosigner, int(recovery, 0)), {'from': recovery})

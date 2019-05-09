import pytest
from eth_account import Account

# @pytest.mark.xfail(
#     strict=True,
#     reason="Wallet is not ERC165 Compliant"
# )
def test_erc165_compliance(
        fullwallet_deploy,
        accounts,
        erc165_checker_deploy,
        ready_invoke_chain,
        w3):
    """
    Verifies ERC standards compliance
    """

    (wallet, _, _) = fullwallet_deploy(
        accounts[1], # Signer
        accounts[1], # Cosigner
        accounts[3]  # Recovery Address
    )

    (checker, _) = erc165_checker_deploy()
    ERC165 = "0x01ffc9a7"
    ERC223 = "0xc0ee0b8a"
    ERC725_Core = "0xd202158d"
    ERC721 = "0x150b7a02" # Actual value based on latest standard version
    ERC721_Old = "0xf0b9e5ba"
    ERC1271 = "0x20c13b0b"

    assert checker.functions.doesContractImplementInterface(wallet.address, ERC165).call() == 1, "Wallet does not support ERC165"
    assert checker.functions.doesContractImplementInterface(wallet.address, ERC223).call() == 1, "Wallet does not support ERC223"

    # Wallet no longer supports ERC725 - assert below commented
    # assert checker.functions.doesContractImplementInterface(wallet.address, ERC725_Core).call() == 1, "Wallet does not support ERC725 Core"
    # This assert now passes as DAP-02 was fixed
    assert checker.functions.doesContractImplementInterface(wallet.address, ERC721).call() == 1, "Wallet does not support ERC721"

    # Check compliance as per standard:
    assert wallet.functions.supportsInterface(ERC165).call() == 1, "Wallet does not support ERC165"
    assert wallet.functions.supportsInterface(ERC223).call() == 1, "Wallet does not support ERC223"
    # Wallet no longer supports ERC725 - assert below commented
    # assert wallet.functions.supportsInterface(ERC725_Core).call() == 1, "Wallet does not support ERC725_Core"
    # This assert now passes as DAP-02 was fixed
    assert wallet.functions.supportsInterface(ERC721).call() == 1, "Wallet does not support ERC721"

    # Added tests to see if the old ERC721 standard is supported
    assert checker.functions.doesContractImplementInterface(wallet.address, ERC721_Old).call() == 1, "Wallet does not support the old ERC721"

    # Added tests to see if the ERC1271 standard is supported
    assert checker.functions.doesContractImplementInterface(wallet.address, ERC1271).call() == 1, "Wallet does not support ERC1271"

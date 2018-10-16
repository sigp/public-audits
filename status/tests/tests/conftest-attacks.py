import pytest
from web3 import Web3

zero_address = "0x" + "00"*20
zero_bytes32 = "0x" + "00"*32

default_beneficiary = Web3.toChecksumAddress("0x" + "0"*37 + "a9e")

@pytest.fixture
def reentrancy_attack_deploy(
        accounts,
        deploy,
        ):
    """
    Deploys an instance of the Reentrancy attack contract.
    """
    def method(
            username_registrar_contract,
            test_token,
            beneficiary=default_beneficiary):

        (c, r) = deploy(
                contract="ReentrancyAttack",
                transaction={
                    'from': accounts[0]
                    },
                args={
                    '_unr':
                    username_registrar_contract.address,
                    '_token': test_token.address,
                    '_beneficiary': beneficiary
                    }
                )

        return (c, r, beneficiary)
    return method


@pytest.fixture
def dos_attack_deploy(
        accounts,
        deploy,
        ):
    """
    Deploys an instance of the Reentrancy attack contract.
    """
    def method():

        (c, r) = deploy(
                contract="DOSAttack",
                transaction={
                    'from': accounts[0]
                    },
                args={
                    }
                )

        return (c, r)
    return method

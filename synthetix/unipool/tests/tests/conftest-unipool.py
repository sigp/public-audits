import pytest


@pytest.fixture
def snx_token_deploy(accounts, deploy):
    """
    Deploy the test SNX token.
    """
    def method():
        (c, r) = deploy(
            contract="SnxMock",
            transaction={
                'from': accounts[0],
            },
            args={}
        )
        return (c, r)
    return method


@pytest.fixture
def uni_token_deploy(accounts, deploy):
    """
    Deploy the test SNX token.
    """
    def method():
        (c, r) = deploy(
            contract="UniMock",
            transaction={
                'from': accounts[0],
            },
            args={}
        )
        return (c, r)
    return method


@pytest.fixture
def unipool_deploy(accounts, deploy):
    """
    Deploy Unipool instance
    """
    def method(uni, snx):
        (c, r) = deploy(
            contract="UnipoolMock",
            transaction={
                'from': accounts[0],
            },
            args={
                'uniToken': uni,
                'snxToken': snx
            }
        )
        return (c, r)
    return method

import pytest


@pytest.fixture
def link_token_deploy(accounts, deploy):
    """
    Deploy the test token.
    """
    def method():
        (c, r) = deploy(
            contract="LinkToken",
            transaction={
                'from': accounts[0],
            },
            args={}
        )
        return (c, r)
    return method


@pytest.fixture
def oracle_deploy(accounts, deploy, link_token_deploy):
    """
    Deploy an oracle and link token
    """
    def method():
        (link, link_r) = link_token_deploy()
        (oracle, oracle_r) = deploy(
            contract="Oracle",
            transaction={
                'from': accounts[0]
            },
            args={
                '_link': link.address,
            })
        return (link, oracle, link_r, oracle_r)
    return method


@pytest.fixture
def basic_consumer_deploy(accounts, deploy):
    """
    Deploy a basic Chainlinked consumer
    """
    def method(link, oracle, specId):
        (c, r) = deploy(
            contract="BasicConsumer",
            transaction={
                'from': accounts[0],
            },
            args={'_link': link,
                  '_oracle': oracle,
                  '_specId': specId}
        )
        return (c, r)
    return method


@pytest.fixture
def chainlinklib_test_deploy(accounts, deploy):
    """
    Deploy an instance of ChainlinkLibTest
    """
    def method():
        (c, r) = deploy(
            contract="ChainlinkLibTest",
            transaction={
                'from': accounts[0],
            },
            args={}
        )
        return (c, r)
    return method


@pytest.fixture
def chainlinked_test_deploy(accounts, deploy):
    """
    Deploy an instance of ChainlinkLibTest
    """
    def method(link, oracle):
        (c, r) = deploy(
            contract="ChainlinkedTest",
            transaction={
                'from': accounts[0],
            },
            args={'_link': link,
                  '_oracle': oracle}
        )
        return (c, r)
    return method


@pytest.fixture
def DOS_deploy(accounts, deploy):
    """
    Deploy an instance of DOSContract
    """
    def method():
        (c, r) = deploy(
            contract="DOSContract",
            transaction={
                'from': accounts[0],
            },
            args={}
        )
        return (c, r)
    return method

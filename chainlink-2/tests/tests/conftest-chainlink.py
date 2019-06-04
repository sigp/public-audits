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
def multi_oracle_deploy(accounts, deploy, link_token_deploy):
    """
    Deploy an oracle and link token
    """
    def method(n):
        oracles = ["0x0"] * n
        oracles_r = ["0x0"] * n
        (link, link_r) = link_token_deploy()
        for i in range(n):
            (oracles[i], oracles_r[i]) = deploy(
                contract="Oracle",
                transaction={
                    'from': accounts[0]
                },
                args={
                    '_link': link.address,
                })
        return (link, link_r, oracles, oracles_r)
    return method

@pytest.fixture
def full_conversion_rate_deploy(accounts, deploy, multi_oracle_deploy, link_token_deploy):
    """
    Deploy a ConversionRate contracts
    """
    def method(payment_amount, minimum_responses, num_oracles):
        (link, link_r, oracles, oracles_r) = multi_oracle_deploy(num_oracles)
        oracle_addresses = ["0x00"] * num_oracles
        for i in range(num_oracles):
            oracle_addresses[i] = oracles[i].address

        (conversion_rate, conversion_rate_r) = deploy(
            contract="ConversionRate",
            transaction={
                'from': accounts[0],
                'gas': 7999999,
            },
            args={
                '_link': link.address,
                '_paymentAmount': payment_amount,
                '_minimumResponses': minimum_responses,
                '_oracles': oracle_addresses,
                '_jobIds': ["0x01"] * num_oracles,
            }
        )

        return (conversion_rate, conversion_rate_r, oracles, oracles_r, link, link_r)
    return method

@pytest.fixture
def basic_conversion_rate_deploy(accounts, deploy):
    """
    Deploy a ConversionRate contracts
    """
    def method(link_address, payment_amount, minimum_responses, oracle_addresses, job_ids):
        (conversion_rate, conversion_rate_r) = deploy(
            contract="ConversionRate",
            transaction={
                'from': accounts[0]
            },
            args={
                '_link': link_address,
                '_paymentAmount': payment_amount,
                '_minimumResponses': minimum_responses,
                '_oracles': oracle_addresses,
                '_jobIds': ["0x01"] * len(oracle_addresses),
            }
        )
        return (conversion_rate, conversion_rate_r)
    return method

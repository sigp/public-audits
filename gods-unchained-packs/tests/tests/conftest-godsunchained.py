import pytest


@pytest.fixture
def pack_types():
    return {
        'Rare': 0,
        'Epic': 1,
        'Legendary': 2,
        'Shiny': 3
    }

@pytest.fixture
def pack_prices():
    return {
        'Rare':         12000000000000000,
        'Epic':         75000000000000000,
        'Legendary':    112000000000000000,
        'Shiny':       1000000000000000000
    }

@pytest.fixture
def card_types():
    return {
        'Common': 0,
        'Rare': 1,
        'Epic': 2,
        'Legendary': 3,
        'Mythic': 4
    }

@pytest.fixture
def referrals_deploy(accounts, deploy):
    """
    Deploy the Referrals contract
    """
    def method():
        (c, r) = deploy(
            contract="Referrals",
            transaction={
                'from': accounts[0],
            },
            args={
                '_discountLimit': 10,
                '_defaultDiscount': 0,
                '_defaultRefer': 10
            }
        )
        return (c, r)
    return method


@pytest.fixture
def processor_deploy(accounts, deploy, referrals_deploy, vault_deploy):
    """
    Deploy a processor and referrals
    """
    def method():
        (referrals, referrals_r) = referrals_deploy()
        (vault, vault_r) = vault_deploy()
        (processor, processor_r) = deploy(
            contract="Processor",
            transaction={
                'from': accounts[0]
            },
            args={
                '_vault': vault.address,
                '_referrals': referrals.address,
            })
        return (referrals, processor, vault, referrals_r, processor_r, vault_r)
    return method


@pytest.fixture
def pack_deploy(accounts, deploy, processor_deploy, cards_deploy):
    """
    Deploys the PackFive contract, alongide a processor, referrals, and cards
    """
    def method():
        (cards, cards_r) = cards_deploy()
        (referrals, processor, vault, referrals_r, processor_r, vault_r) = processor_deploy()
        (pack, pack_r) = deploy(
            contract="PackFive",
            transaction={
                'from': accounts[0],
            },
            args={'_cards': cards.address,
                  '_processor': processor.address
                  })
        processor.functions.setCanSell(pack.address, True).transact({'from': accounts[0]})
        return (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r)
    return method


@pytest.fixture
def cards_deploy(accounts, deploy):
    """
    Deploy an instance of CardIntegrationTwo
    """
    def method():
        (c, r) = deploy(
            contract="CardIntegrationTwo",
            transaction={
                'from': accounts[0],
            },
            args={}
        )
        return (c, r)
    return method


@pytest.fixture
def vault_deploy(accounts, deploy):
    """
    Deploy a Vault instance
    """
    def method():
        (c, r) = deploy(
            contract="CappedVault",
            transaction={
                'from': accounts[0],
            },
            args={}
        )
        return (c, r)
    return method



@pytest.fixture
def get_card_type_from_rand(card_types):

    def method(rand, min_rarity="Common"):

        if rand > 999999:
            raise Exception("Random value too large")
        elif rand == 999999:
            return "Mythic"
        elif min_rarity == "Common":
            if rand >= 998345:
                return "Legendary"
            elif rand >= 986765:
                return "Epic"
            elif rand >= 924890:
                return "Rare"
            else:
                return "Common"
        elif min_rarity == "Legendary":
            return "Legendary"
        elif rand > 981615:
            return "Legendary"
        elif min_rarity == "Epic":
            return "Epic"
        elif rand > 852940:
            return "Epic"
        elif min_rarity == "Rare":
            return "Rare"
        else:
            raise Exception("Unhandled rarity combo!")

    return method

@pytest.fixture
def extract_bytes():
    def method(value, length, start):
        return (((1 << (length*8)) - 1) & (value >> ((start - 1) * 8)))
    return method

@pytest.fixture
def get_randomness_components(extract_bytes):
    def method(random_val):
        return {
            'random': random_val,
            'rarity': extract_bytes(random_val, 4, 10) % 1000000,
            'quality': extract_bytes(random_val, 2, 4) % 1000,
            'purity': extract_bytes(random_val, 2, 6) % 1000,
            'proto': extract_bytes(random_val, 2, 8) % (2**16 - 1)
        }
    return method


@pytest.fixture
def calculate_purity():
    def method(randOne, randTwo, is_shiny=False):
        if randOne >= 998:
            return 3000 + randTwo
        elif randOne >= 988 or (is_shiny and randOne >= 748):
            return 2000 + randTwo
        elif randOne >= 938 or is_shiny:
            return 1000 + randTwo
        else:
            return randTwo
    return method

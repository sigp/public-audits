import pytest
from web3 import Web3

zero_address = "0x" + "00"*20
zero_bytes32 = "0x" + "00"*32


@pytest.fixture
def variables():
    ens_label = Web3.soliditySha3(['string'], ["status"])
    ens_node = Web3.soliditySha3(['bytes32', 'bytes32'],
                                 [zero_bytes32, ens_label])
    return {"zero_address": zero_address,
            "zero_bytes32": zero_bytes32,
            "ens_node": ens_node,
            "ens_label": ens_label
            }


@pytest.fixture
def deploy_registrar(registrar_deploy):
    """
    For legacy use
    """
    return registrar_deploy


@pytest.fixture
def registrar_deploy(
        accounts,
        deploy,
        resolver_deploy,
        test_token_deploy
        ):
    """
    Deploys an instance of the UsernameRegistrar contract.
    """
    def method(
            root_node_name="status",
            username_min_length=int(10),
            reserved_merkle_root="00",
            parent_registry=zero_address,
            initial_token_balance=int(10e6),
            token_contract=None,
            ens_contract=None,
            resolver_contract=None
            ):
        # Construct the public resolver.
        ens_label = Web3.soliditySha3(['string'], [root_node_name])
        ens_node = Web3.soliditySha3(['bytes32', 'bytes32'],
                                     [zero_bytes32, ens_label])
        ens_c = ens_contract
        resolver_c = resolver_contract
        if ens_contract is None or resolver_contract is None:
            # Deploy the public resolver and ENS
            (ens_c, _, resolver_c, _) = resolver_deploy(ens_label)

        test_c = token_contract
        if token_contract is None:
            (test_c, _) = test_token_deploy(initial_token_balance)

        # Deploy the username registrar
        (c, r) = deploy(
            contract="UsernameRegistrar",
            transaction={
                'from': accounts[0]
            },
            args={
                '_token': test_c.address,
                '_ensRegistry': ens_c.address,
                '_resolver': resolver_c.address,
                '_ensNode': ens_node,
                '_usernameMinLength': int(username_min_length),
                '_reservedUsernamesMerkleRoot': reserved_merkle_root,
                '_parentRegistry': parent_registry
            }
        )
        if parent_registry == zero_address:
            ens_c.functions.setSubnodeOwner(
                    bytes.fromhex('00'),
                    ens_label,
                    c.address).transact({'from': accounts[0]})
        return (c, r, test_c, ens_c, resolver_c, ens_node)
    return method


@pytest.fixture
def ens_deploy(accounts, deploy):
    """ Deploys ENS and registers a root node """

    def method(root_node):
        (c, r) = deploy(
                contract="ENSRegistry",
                transaction={
                    'from': accounts[0]
                    },
                args={}
                )

        c.functions.setSubnodeOwner(
                bytes.fromhex('00'),
                root_node,
                accounts[0]).transact({'from': accounts[0]})
        return (c, r)
    return method


@pytest.fixture
def test_token_deploy(accounts, deploy):
    """ Deploys the test token with an initial balance """
    def method(initial_balance):
        (c, r) = deploy(
                contract="TestToken",
                transaction={
                    'from': accounts[0]
                    },
                args={}
                )
        c.functions.mint(int(initial_balance)).transact({'from': accounts[0]})
        return (c, r)
    return method


@pytest.fixture
def resolver_deploy(accounts, deploy, ens_deploy):
    """ Deploys the test token with an initial balance """
    def method(root_node):
        # Deploy ENS as a dependency
        (ens_c, ens_r) = ens_deploy(root_node)
        (c, r) = deploy(
                contract="PublicResolver",
                transaction={
                    'from': accounts[0]
                    },
                args={
                    'ensAddr': ens_c.address
                    }
                )
        return (ens_c, ens_r, c, r)
    return method


@pytest.fixture
def register_accounts(accounts):

    def method(
            registrar_contract,
            token_contract,
            no_accounts=10,
            price=50
            ):

        # Check the state of the registrar. Activate if needed.
        current_state = registrar_contract.functions.state().call()
        if current_state == 0:  # Inactive
            # Activate with price
            registrar_contract.functions.activate(price).transact(
        {"from": accounts[0]})

        current_price = registrar_contract.functions.price().call()
        if current_price > 0:
            # Transfer tokens around
            for i in range(no_accounts):
                token_contract.functions.transfer(
                        accounts[i],
                        current_price).transact({"from": accounts[0]})
                token_contract.functions.approve(
                        registrar_contract.address,
                        current_price).transact({"from": accounts[i]})

        # Register the names
        for i in range(no_accounts):
            label = Web3.soliditySha3(['string'], ["name" + str(i)])
            print("Registering name: name" + str(i))
            registrar_contract.functions.register(
                    label,
                    zero_address,
                    zero_bytes32,
                    zero_bytes32).transact({"from": accounts[i]})

    return method

@pytest.fixture
def sha3():
    def method(
        type,
        label
    ):
        return Web3.soliditySha3(type, label)
    return method

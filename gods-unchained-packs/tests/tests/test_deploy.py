import pytest
import random
from web3.contract import ConciseContract

NUM_PACK_TYPES = 4

DEBUG = False

@pytest.mark.parametrize(
    "bundle_sizes, bundle_caps",
    [
        [[1,1,1,11], [2,2,2,5]],
        [[1,1,1,200], [2,2,2,2]],
        [[random.randint(1,100) for i in range(NUM_PACK_TYPES)], [random.randint(0,100) for i in range(NUM_PACK_TYPES)]],
        [[1]*NUM_PACK_TYPES, [0]*NUM_PACK_TYPES],
        [[5]*NUM_PACK_TYPES, [5]*NUM_PACK_TYPES],
        [[4*i + 1 + i for i in range(NUM_PACK_TYPES)], [5*i - i for i in range(NUM_PACK_TYPES)]],
        [[4*i + 1 - i for i in range(NUM_PACK_TYPES)], [5*i + i for i in range(NUM_PACK_TYPES)]],
        [[i+1 for i in range(NUM_PACK_TYPES)], [i for i in range(NUM_PACK_TYPES)]],
        [[50+i for i in range(NUM_PACK_TYPES)], [30+i for i in range(NUM_PACK_TYPES)]]
    ]
)

def test_deploy(
        pack_deploy,
        instantiate,
        accounts,
        assert_tx_failed,
        pack_types,
        pack_prices,
        get_receipt,
        get_logs_for_event,
        w3,
        #Parameters
        bundle_sizes,
        bundle_caps):

    BLOCK_GAS_LIMIT = 8e6  # Well over double this now, but a possible concern.

    # Deploy an oracle and a Link Token
    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()

    receipts = {
        "pack": (pack, pack_r),
        "processor": (processor, processor_r),
        "referrals": (referrals, referrals_r),
        "cards": (cards, cards_r),
        "vault": (vault, vault_r)
    }

    if DEBUG:
        print("")  # new line
    for name, r in receipts.items():
        if DEBUG:
            print("Gas used to deploy {}:\t{}".format(name, r[1]['gasUsed']))
        assert r[1]['gasUsed'] < BLOCK_GAS_LIMIT, "{} uses more gas than block_gas_limit!".format(name)
        assert r[0].address != 0, "Address returned not expected for {}".format(name)

    addPack = cards.functions.addPack(pack.address)
    assert_tx_failed(addPack, {'from': accounts[1]})
    addPack.transact({'from': accounts[0]})

    tokens = {}


    # Now each of the bundle tokens need to be deployed
    # For each, the pack has to be set to point to the bundle and stipulate it's price and size.
    for i, (rarity, rarity_value) in enumerate(pack_types.items()):

        setPack = pack.functions.setPack(
            rarity_value,
            pack_prices[rarity],
            "Genesis {} Bundle".format(rarity),
            "BND{}".format(rarity[0]),
            bundle_sizes[i],
            bundle_caps[i],
        )
        assert_tx_failed(setPack, {'from': accounts[1]})
        tx_hash = setPack.transact({'from': accounts[0]})
        rcpt = get_receipt(tx_hash)

        assert len(rcpt['logs']) == 1, "Should have one event emitted."
        assert rcpt['gasUsed'] < BLOCK_GAS_LIMIT, "Too much gas for block!"

        logs = get_logs_for_event(pack.events.PackAdded, tx_hash)

        tokens[rarity] = instantiate(logs[0]['args']['bundle'], abi=None, contract="Bundle")
        processor.functions.setCanSell(tokens[rarity].address, True).transact({'from': accounts[0]})

        if DEBUG:
            print("Created {} Bundles: Size: {}, Cap: {}, Gas: {}".format(
                rarity,
                bundle_sizes[i],
                bundle_caps[i],
                rcpt['gasUsed'])
            )

    print("Approval Statuses:")
    for address in accounts[:5]:
        print("{}: {}".format(address, processor.functions.approvedSellers(accounts[0]).call()))

    # For each of the tokens, check their variables and try to purchase a bunch of them,
    # making sure we can't purchase too many
    for i, (rarity, token) in enumerate(tokens.items()):
        c = ConciseContract(token)
        assert c.totalSupply() == 0, "{} tokens should start with supply of zero".format(rarity)
        assert c.balanceOf(accounts[0]) == 0, "No user should have balance before mint."
        assert c.balanceOf(accounts[1]) == 0, "No user should have balance before mint."
        assert c.name() == "Genesis {} Bundle".format(rarity), "Incorrect token name"
        assert c.symbol() == "BND{}".format(rarity[0]), "Incorrect token symbol"
        assert c.decimals() == 0, "Incorrect token decimals"
        assert c.cap() == bundle_caps[i], "Incorrect cap for token"
        assert c.packType() == pack_types[rarity], "Incorrect packType for token"

        BUNDLES_TO_BUY = 6

        for _ in range(bundle_caps[i] if bundle_caps[i] > 0 else BUNDLES_TO_BUY):
            # Shouldn't be able to buy if we send no money
            assert_tx_failed(
                token.functions.purchaseFor(accounts[0], 1, accounts[1]),
                {'from': accounts[0]}
            )
            assert processor.functions.approvedSellers(token.address).call(), "Bundle should be approved to sell."
            tx_hash = token.functions.purchaseFor(accounts[0], 1, accounts[1])\
                .transact({'from': accounts[0], 'value': pack_prices[rarity] * bundle_sizes[i]})
            rcpt = get_receipt(tx_hash)
            assert rcpt['gasUsed'] < BLOCK_GAS_LIMIT, "Too much gas for block!"
            if DEBUG:
                print("Account0 {} tokens: {}, vault: {} ({})".format(
                    rarity,
                    token.functions.balanceOf(accounts[0]).call(),
                    (vault.functions.total().call())/10**18,
                    w3.eth.getBalance(vault.address)/10**18))

        # Now there shouldn't be any more bundles available to buy
        if bundle_caps[i] > 0:
            assert_tx_failed(
                token.functions.purchaseFor(accounts[0], 1, accounts[1]),
                {'from': accounts[0]}
            )

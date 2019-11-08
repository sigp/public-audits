import pytest
from web3.contract import ConciseContract

DEBUG = False

MAX_PURITY = 4000

# The getCardDetails functions are all private now, so can't inspect them.
@pytest.mark.xfail
@pytest.mark.parametrize(
    "random_input",
    [
        "lolcats",
        "",
        "n7DUfYQ5EzwYjhMFXq9",
        "YRnj76dncgGVBtkMG7CSQi54",
        "0"
    ]
)
def test_card_details(
        pack_types,
        pack_prices,
        card_types,
        get_card_type_from_rand,
        get_randomness_components,
        calculate_purity,
        assert_tx_failed,
        accounts,
        w3,
        pack_deploy,
        get_logs_for_event,
        instantiate,
        #Parameters
        random_input):


    (pack, processor, referrals, cards, vault, pack_r, processor_r, referrals_r, cards_r, vault_r) = pack_deploy()




    pack_size = 5
    bundle_size = 3 # 3 packs of 5 cards in a bundle
    set_pack_fn = pack.functions.setPack(pack_types['Rare'], pack_prices['Rare'], "Rare bundle", "RB", bundle_size, 0)
    assert_tx_failed(set_pack_fn, {'from': accounts[1]})
    tx_hash = set_pack_fn.transact({'from': accounts[0]})
    rare_bundle = instantiate(get_logs_for_event(pack.events.PackAdded, tx_hash)[0]['args']['bundle'], abi=None, contract="Bundle")
    processor.functions.setCanSell(rare_bundle.address, True).transact({'from': accounts[0]})

    card_protos = {r: [] for r in card_types.keys()}

    # Create 6 cards for each of the 5 types.
    num_of_cards = 6
    for card_type, card_type_val in card_types.items():
        for n in range(num_of_cards):
            proto_id = 1337 + (num_of_cards * card_type_val) + n
            add_proto_fn = cards.functions.addProto(proto_id, 99, card_type_val, 99, 99, 99, 99, 99, True)
            assert_tx_failed(add_proto_fn, {'from': accounts[1]})
            add_proto_fn.transact({'from': accounts[0]})
            card_protos[card_type].append(proto_id)


    random_seed = int.from_bytes(bytes(random_input, 'utf8'), byteorder='big', signed=False)

    PackContract = ConciseContract(pack)
    card_detail_functions = {
        # Can't have shiny, it's internal.
        'Legendary': PackContract._getLegendaryCardDetails,
        'Epic': PackContract._getEpicCardDetails,
        'Rare': PackContract._getRareCardDetails,
    }

    for pack_type, pack_type_val in pack_types.items():
        for card_no in range(pack_size):
            random_val = int.from_bytes(w3.soliditySha3(['uint256', 'uint256'], [card_no, random_seed]), 'big')
            components = get_randomness_components(random_val)

            min_rarity = "Common"
            if pack_type == "Epic":
                if card_no == 4:
                    min_rarity = "Epic"
            elif pack_type in ("Legendary", "Shiny"):
                if card_no == 4:
                    min_rarity = "Legendary"
                elif card_no == 3:
                    min_rarity = "Rare"
            elif card_no == 4:
                min_rarity = "Rare"


            card_type = get_card_type_from_rand(components['rarity'], min_rarity)

            # Calculate what should be the value, called directly on each function and indirectly from getCardDetails
            # If statement skips the direct function for shiny because it's internal
            for (proto, purity) in [
                PackContract.getCardDetails(pack_type_val, card_no, random_seed),
                card_detail_functions[pack_type](card_no, random_seed)
                 ] if pack_type != "Shiny" else [PackContract.getCardDetails(pack_type_val, card_no, random_seed)]:
                if DEBUG:
                    print("{}:{}\t - {} ({})".format(pack_type, card_no, purity, proto))

                assert proto in card_protos[card_type], "Card proto {} not found in list of protos for {}".format(proto, card_type)
                assert proto == card_protos[card_type][components['proto'] % len(card_protos[card_type])], "Incorrect card proto for {}".format(card_type)
                assert purity == calculate_purity(
                    components['quality'],
                    components['purity'],
                    is_shiny=(pack_type == "Shiny" and card_no == 4)), "Purity incorrect for {}".format(card_type)
                assert purity < MAX_PURITY, "Unexpectedy large purity"






def test_extract_bytes(w3, extract_bytes):

    random_seed = int.from_bytes(bytes("lolcats", 'utf8'), byteorder='big', signed=False)
    random_bytes = w3.soliditySha3(['uint256', 'uint256'], [1, random_seed])
    random_val = int.from_bytes(random_bytes, 'big')
    if DEBUG:
        print()
        print('rand: {0:x}'.format(random_val))
        print('qual: {0}{1:x}'.format(" " * 4 * 2, extract_bytes(random_val, 2, 4)))
        print('prot: {0}{1:x}'.format(" " * 6 * 2, extract_bytes(random_val, 2, 6)))
        print('puri: {0}{1:x}'.format(" " * 8 * 2, extract_bytes(random_val, 2, 8)))
        print('rari: {0}{1:x}'.format(" " * 10 * 2, extract_bytes(random_val, 4, 10)))

    assert extract_bytes(random_val, 2, 4) == int.from_bytes(random_bytes[-5:-3], 'big'), "Extracted bytes should be equal"
    assert extract_bytes(random_val, 2, 6) == int.from_bytes(random_bytes[-7:-5], 'big'), "Extracted bytes should be equal"
    assert extract_bytes(random_val, 2, 8) == int.from_bytes(random_bytes[-9:-7], 'big'), "Extracted bytes should be equal"
    assert extract_bytes(random_val, 4, 10) == int.from_bytes(random_bytes[-13:-9], 'big'), "Extracted bytes should be equal"

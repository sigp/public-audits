# The vulnerability illustrated by this test has been closed as the onERC721Received function(s) do not emit events anymore

# def test_event_poisoning(
#         fullwallet_deploy,
#         accounts,
#         get_logs_for_event,
#         w3):
#     """
#     Illustrates that any address can trigger the wallet to emit the ERC721Received log
#     """
#
#     (wallet, _, _) = fullwallet_deploy(
#         accounts[1],
#         accounts[1],
#         accounts[3]
#     )
#     data = bytes("test", 'utf-8')
#     for i in range(10):
#         tx = wallet.functions.onERC721Received(accounts[10+i], i, data).transact({'from': accounts[20]})
#         event = get_logs_for_event(wallet.events.ERC721Received, tx)[0]['args']
#         assert event['_from'] == accounts[10+i]
#         assert event['_tokenId'] == i
#         assert event['_data'] == data

import sys

from ccql_node import ccql_node
from ccql_node import merkle_tree_hashing
from ccql_node import data_coding

from ccql_node import ccql_data

class CCQL_Node_Connector:

    node_connections = {}

    def __init__(self, blockchain, network, chain_descriptor):
        self.get_node_connection(blockchain, network, chain_descriptor)

    def get_block(self, chain_descriptor, block_descriptor, query_attributes):

        node = self.get_node_connection(chain_descriptor)

        block_limit = 99999
        block = node.get_block(block_descriptor, block_limit)

        tx_limit = 3

        is_query_for_tx = False
        
        # TODO: remove, legacy
        #for q in query_attributes:
        #    if q.startswith(ccql_data.TX):
        #        is_query_for_tx = True
        #        break
        # TODO: remove, legacy
        if is_query_for_tx:
            i = 0
            transaction_data = []
            for tx_id in block[ccql_data.BL_TRANSACTION_IDS]:
                tx = node.get_transaction(tx_id)
                #transaction_data.append(tx)
                block[ccql_data.BL_TRANSACTIONS][tx_id] = tx
                i += 1
                if i >= tx_limit:
                    break
            
        if block is None:
            print("Block not found, abort")
            sys.exit()

        return [block]
        # path = data_coding.decode_cid_bytes32(path_b)
        # path = data_coding.decode_str_bytes32(path_b)


    def get_account(self, chain_descriptor, account_descriptor, query_clause):

        node = self.get_node_connection(chain_descriptor)

        account = node.get_account(account_descriptor)

        if account is None:
            print("Account not found, abort")
            sys.exit()

        return [account]
        # path = data_coding.decode_cid_bytes32(path_b)
        # path = data_coding.decode_str_bytes32(path_b)


    def get_transaction(self, chain_descriptor, tx_descriptor, query_clause):

        node = self.get_node_connection(chain_descriptor)

        tx = node.get_transaction(tx_descriptor)

        if tx is None:
            print("Transaction not found, abort")
            sys.exit()

        return [tx]


    def get_node_connection(self, blockchain, network, chain_descriptor):

        node = None
        key = blockchain + "." + network + "." + chain_descriptor

        if key in CCQL_Node_Connector.node_connections.keys():
            node = CCQL_Node_Connector.node_connections[key]

        else:
            node = ccql_node.CCQL_Node() 

            if chain_descriptor == ccql_data.CH_DESCRIPTOR_ETH:
                identity = "0x0"
                print("Create connection to Web3 Ethereum node ...")
                node = ccql_node.Web3_Eth_Node(identity)

            if not node.is_connected():
                print("Node not connected for chain:", chain_descriptor)
                sys.exit()

            CCQL_Node_Connector.node_connections[chain_descriptor] = node

        return node


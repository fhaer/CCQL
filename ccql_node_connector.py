import sys

from ccql_node import ccql_node
from ccql_node import merkle_tree_hashing
from ccql_node import data_coding

from ccql_node import ccql_data

class CCQL_Node_Connector:

    # TODO remove
    node_connections = {}

    def __init__(self, blockchain, network, chain_descriptor):
        node = self.get_node_connection(blockchain, network, chain_descriptor)
        self.node = node

    def get_blocks(self, number_from, number_to):

        blocks = []
        linked_block = None

        for i in range(number_from, number_to+1):
            result_list = self.get_block(i, linked_block)
            if len(result_list) > 0:
                block_i = result_list[-1]
                blocks.append(block_i)
                linked_block = block_i

        return blocks

    def get_block(self, id, linked_block_desc=None):

        block_limit = 99999
        linked_block_desc = None
        block = self.node.get_block(id, linked_block_desc, block_limit)

        if block is None:
            print("Block not found, abort")
            sys.exit()

        return [block]
        # path = data_coding.decode_cid_bytes32(path_b)
        # path = data_coding.decode_str_bytes32(path_b)

    def get_account(self, id):

        account = self.node.get_account(id)

        if account is None:
            print("Account not found, abort")
            sys.exit()

        return [account]
        # path = data_coding.decode_cid_bytes32(path_b)
        # path = data_coding.decode_str_bytes32(path_b)


    def get_transaction(self, id):

        tx = self.node.get_transaction(id)

        if tx is None:
            print("Transaction not found, abort")
            sys.exit()

        return [tx]


    def get_node_connection(self, blockchain, network, chain_descriptor):

        node = None
        key = blockchain + ":" + network + ":" + chain_descriptor

        if key in CCQL_Node_Connector.node_connections.keys():
            node = CCQL_Node_Connector.node_connections[key]

        else:
            node = ccql_node.CCQL_Node() 

            bc = ccql_data.get_bc_by_id(blockchain, network, chain_descriptor)

            if not node is None and not bc is None:
                if bc.id == "eth":
                    identity = "0x0"
                    print("Create connection to Web3 Ethereum node ...")
                    node = ccql_node.Web3_Eth_Node(identity)
            if bc is None:
                print("No node connection available for", key)
            if not node.is_connected():
                print("Node not connected for chain:", bc)
                sys.exit()

            CCQL_Node_Connector.node_connections[key] = node

        return node

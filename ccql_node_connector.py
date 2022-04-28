import sys

from ccql_node import ccql_node
from ccql_node import merkle_tree_hashing
from ccql_node import data_coding

from ccql_node import ccql_data

class CCQL_Node_Connector:

    node_connections = {}

    def __init__(self, blockchain, network, chain_descriptor):
        node = self.get_node_connection(blockchain, network, chain_descriptor)
        self.node = node

    def get_class_name_from_type(self, obj_type_class):
        is_upper_case = True
        for c in obj_type_class.__name__:
            is_upper_case &= (c.upper() == c)
        if is_upper_case:
            return obj_type_class.__name__.lower()
        else:
            return obj_type_class.__name__[0].lower() + obj_type_class.__name__[1:]

    def flatten_object_type_res(self, obj, obj_type_class, result_list, result_list_type):

        if not obj is None:
            result_list.append(obj)
            type_attr_name = self.get_class_name_from_type(obj_type_class)
            if not result_list_type is None:
                object_type = getattr(obj, type_attr_name)
                if not object_type is None:
                    result_list_type.append(object_type)

    def flatten_list_type_res(self, list, obj_type_class, result_list, result_list_type):

        if not list is None and len(list) > 0:
            for obj in list:
                result_list.append(obj)
                type_attr_name = self.get_class_name_from_type(obj_type_class)
                if not result_list_type is None:
                    object_type = getattr(obj, type_attr_name)
                    if not object_type is None:
                        result_list_type.append(object_type)

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

        block_res = [block]

        # descriptor of block with status and linked blocks
        block_desc_res = []
        status_res = []
        linked_block_desc_res = []

        self.flatten_object_type_res(block.descriptor, ccql_data.Status, block_desc_res, status_res)
        self.flatten_list_type_res(block.linkedBlockDescriptor, ccql_data.Status, linked_block_desc_res, None)

        # descriptor of validation and validators        
        validation_desc_res = []
        val_desc_proposer_res = []
        val_desc_creator_res = []
        val_desc_attestations_res = []

        self.flatten_object_type_res(block.validationDescriptor, ccql_data.ValidationDescriptor, validation_desc_res, None)
        self.flatten_list_type_res(block.validationDescriptor.proposer, ccql_data.ValidatorDescriptor, val_desc_proposer_res, None)
        self.flatten_list_type_res(block.validationDescriptor.creator, ccql_data.ValidatorDescriptor, val_desc_creator_res, None)
        self.flatten_list_type_res(block.validationDescriptor.attestations, ccql_data.ValidatorDescriptor, val_desc_attestations_res, None)

        # transactions and accounts
        tx_res = []
        acc_res = []
        
        self.flatten_list_type_res(block.transactions, ccql_data.TransactionDescriptor, tx_res, None)
        self.flatten_list_type_res(block.accounts, ccql_data.AccountDescriptor, acc_res, None)

        return (block_res, block_desc_res, status_res, linked_block_desc_res, validation_desc_res, val_desc_proposer_res, val_desc_creator_res, val_desc_attestations_res, tx_res, acc_res)
        # path = data_coding.decode_cid_bytes32(path_b)
        # path = data_coding.decode_str_bytes32(path_b)

    def get_account(self, id):

        account = self.node.get_account(id)

        acc_res = []
        acc_desc_res = []

        if account is None:
            print("Account not found, abort")
            sys.exit()

        self.flatten_object_type_res(account, ccql_data.AccountDescriptor, acc_res, acc_desc_res)

        ass_res = []
        ass_type_res = []
        tok_res = []
        tok_type_res = []
        dat_res = []
        str_type_res = []

        self.flatten_list_type_res(account.assets, ccql_data.AssetType, ass_res, ass_type_res)
        self.flatten_list_type_res(account.tokens, ccql_data.TokenType, tok_res, tok_type_res)
        self.flatten_list_type_res(account.data, ccql_data.StorageType, dat_res, str_type_res)

        return (acc_res, acc_desc_res, ass_res, ass_type_res, tok_res, tok_type_res, dat_res, str_type_res)
        # path = data_coding.decode_cid_bytes32(path_b)
        # path = data_coding.decode_str_bytes32(path_b)

    def get_transaction(self, id):

        tx = self.node.get_transaction(id)

        if tx is None:
            print("Transaction not found, abort")
            sys.exit()

        tx_res = [tx]
        tx_desc_res = []
        tx_utxo_res = []

        self.flatten_list_type_res(tx.descriptor, ccql_data.UTXO, tx_desc_res, tx_utxo_res)

        return (tx_res, tx_desc_res, tx_utxo_res)


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
                if bc.id == "btc":
                    identity = "0x0"
                    print("Create connection to Bitcoin node ...")
                    node = ccql_node.Bitcoin_Node(identity)
                if bc.id == "ada":
                    identity = "0x0"
                    print("Create connection to Cardano node ...")
                    node = ccql_node.Cardano_Node(identity)
                if bc.id == "avax":
                    identity = "0x0"
                    print("Create connection to Avalanche node ...")
                    node = ccql_node.Web3_Avalanche_Node(identity)
            if bc is None:
                print("No node connection available for", key)
            if not node.is_connected():
                print("Node not connected for chain:", bc)
                sys.exit()

            CCQL_Node_Connector.node_connections[key] = node

        return node

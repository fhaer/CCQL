from web3.contract import Contract

# ID and descriptor attributes
ID = 'id'
DESC = 'desc'

# chain package classes
BLOCKCHAIN = 'Chain'
BLOCKCHAIN_S = 'C'
NETWORK = 'Network'
NETWORK_S = 'N'
CHAIN_DESC = 'ChainDesc'
CHAIN_DESC_S = 'D'
CHAIN_TYPE = 'ChainType'
CONSENSUS_TYPE = 'ConsensusType'
EXECUTION_TYPE = 'ExecutionType'

# block package classes
BLOCK = 'Block'
BLOCK_S = 'B'
BLOCK_DESC = 'BlockDesc'
BLOCK_STATUS = 'Status'
BLOCK_VALIDATION_DESC = 'ValidationDesc'
BLOCK_VALIDATOR_DESC = 'ValidatorDesc'

# transaction package classes
TRANSACTION = 'Transaction'
TRANSACTION_S = 'T'
TRANSACTION_DESC = 'TDesc'
TRANSACTION_UTXO = 'UTXO'
TRANSACTION_ADDRESS = 'Address'

# account package classes
ACCOUNT = 'Account'
ACCOUNT_S = 'A'
ACCOUNT_DESC = 'AccountDesc'
ACCOUNT_ASSET = 'Asset'
ACCOUNT_ASSET_S = 'AS'
ACCOUNT_ASSET_TYPE = 'AssetType'
ACCOUNT_TOKEN = 'Token'
ACCOUNT_TOKEN_S = 'TO'
ACCOUNT_TOKEN_TYPE = 'TokenType'
ACCOUNT_DATA = 'Data'
ACCOUNT_DATA_S = 'DT'
ACCOUNT_STORAGE_TYPE = 'StorageType'

# classes of all packages
CHAIN_PKG_CLASSES = [ BLOCKCHAIN, BLOCKCHAIN_S, NETWORK, NETWORK_S, CHAIN_DESC, CHAIN_DESC_S, CHAIN_TYPE, CONSENSUS_TYPE, EXECUTION_TYPE ]
BLOCK_PKG_CLASSES = [ BLOCK, BLOCK_S, BLOCK_DESC, BLOCK_VALIDATION_DESC, BLOCK_STATUS, BLOCK_VALIDATOR_DESC ]
TRANSACTION_PKG_CLASSES = [ TRANSACTION, TRANSACTION_S, TRANSACTION_DESC, TRANSACTION_UTXO, TRANSACTION_ADDRESS ]
ACCOUNT_PKG_CLASSES = [ ACCOUNT, ACCOUNT_S, ACCOUNT_DESC, ACCOUNT_ASSET, ACCOUNT_ASSET_S, ACCOUNT_ASSET_TYPE, ACCOUNT_TOKEN, ACCOUNT_TOKEN_S, ACCOUNT_TOKEN_TYPE, ACCOUNT_DATA, ACCOUNT_DATA_S, ACCOUNT_STORAGE_TYPE ]

# query statements
Q = "Q"
S = "S"
F = "F"
Q_CLAUSES = [ Q, S, F ]

CCQL_CLASSES = CHAIN_PKG_CLASSES + BLOCK_PKG_CLASSES + TRANSACTION_PKG_CLASSES + ACCOUNT_PKG_CLASSES

SOURCE_SPEC_OPTIONAL = [ BLOCK, BLOCK_S, TRANSACTION, TRANSACTION_S, ACCOUNT, ACCOUNT_S, ACCOUNT_ASSET, ACCOUNT_ASSET_S, ACCOUNT_TOKEN, ACCOUNT_TOKEN_S, ACCOUNT_DATA, ACCOUNT_DATA_S ]


# Data Model

class ChainType(object):
    def __init__(self):
        self.typeName = ""
        self.isMainNet = False
        self.isTestNet = False
        self.isSideChain = False
        self.chain = []
class ExecutionType(object):
    def __init__(self):
        self.typeName = ""
        self.isUtxoBased = ""
        self.isAccountBased = ""
        self.isEvmBased = False
        self.chainDescriptor = []
class Network(object):
    def __init__(self):
        self.id = ""
        self.name = ""
        self.chainDescriptors = []
        self.nodeURI = ""
        self.nodeCall = ""
        self.network = []
        self.network = None
class Blockchain(object):
    def __init__(self):
        self.id = ""
        self.name = ""
        self.networks = []
class ConsensusType(object):
    def __init__(self):
        self.typeName = ""
        self.name = ""
        self.implementation = ""
        self.chain = []
class ChainDescriptor(object):
    def __init__(self):
        self.id = ""
        self.name = ""
        self.chainType = []
        self.consensusType = None
        self.blocks = []
        self.executionType = None
        self.chain = None
        self.block = []
        self.executionType2 = None
        self.consensusType = None
        self.chainDescriptor = None
class Transaction(object):
    def __init__(self):
        self.id = ""
        self.descriptor = []
        self.fee = 0.
        self.feePrice = 0.
        self.feeUnit = ""
class UTXO(object):
    def __init__(self):
        self.id = 0
        self.transaction = None
        self.transactionDescriptor = None
class Address(object):
    def __init__(self):
        self.id = 0
        self.name = ""
        self.validatorDescriptor = []
        self.transactionDescriptor = []
        self.account = None
class TransactionDescriptor(object):
    def __init__(self):
        self.from_ = []
        self.to = []
        self.asset = None
        self.token = None
        self.data = None
        self.value = 0.
        self.script = ""
        self.utxo = None
class Data(object):
    def __init__(self):
        self.id = 0
        self.storageType = None
        self.stateId = ""
        self.transactionDescriptor = []
        self.storageType = None
        self.account = None
class Account(object):
    def __init__(self):
        self.id = ""
        self.descriptor = None
        self.assets = []
        self.tokens = []
        self.data = []
        self.accountDescriptor = None
        self.block = []
        self.data = []
        self.asset = []
        self.token = []
class Asset(object):
    def __init__(self):
        self.id = 0
        self.assetType = None
        self.utxo = []
        self.balance = 0.
        self.assetType = None
        self.transactionDescriptor = []
        self.account = None
class AssetType(object):
    def __init__(self):
        self.id = 0
        self.typeName = ""
        self.unit = ""
        self.asset = []
class AccountDescriptor(object):
    def __init__(self):
        self.isSmartContract = False
        self.isExternallyOwned = False
        self.addressType = ""
        self.accountDescriptor = None
        self.account = None
class StorageType(object):
    def __init__(self):
        self.id = 0
        self.typeName = ""
        self.IsBlobType = False
        self.isKeyValueType = False
        self.data = []
class TokenType(object):
    def __init__(self):
        self.id = 0
        self.typeName = ""
        self.standardRef = ""
        self.unit = ""
        self.token = []
class Token(object):
    def __init__(self):
        self.id = 0
        self.tokenType = None
        self.balance = 0.
        self.tokenType = None
        self.transactionDescriptor = []
        self.account = None
class Status(object):
    def __init__(self):
        self.isFinal = False
        self.isOrphan = False
        self.isOmmer = False
        self.blockDescriptor = []
class BlockDescriptor(object):
    def __init__(self):
        self.height = 0
        self.epoch = 0
        self.slot = 0
        self.creationData = ""
        self.timestamp = 0
        self.status = None
        self.dagSupport = False
        self.capacity = 0
        self.status2 = None
        self.block = None
class ValidatorDescriptor(object):
    def __init__(self):
        self.validator = []
        self.signature = []
        self.votes = []
        self.rewards = []
        self.address = []
        self.validationDescriptor = []
class Block(object):
    def __init__(self):
        self.id = ""
        self.descriptor = None
        self.linkedBlockDescriptor = []
        self.validationDescriptor = None
        self.transactions = []
        self.accounts = []
        self.chain = None
        self.validationDescriptor = None
        self.blockDescriptor = None
class ValidationDescriptor(object):
    def __init__(self):
        self.validationInput = ""
        self.validationCondition = ""
        self.hashValue = ""
        self.proposer = []
        self.creator = []
        self.attestations = []
        self.reward = 0.
        self.validatorDescriptor = []
        self.block = None
class Query(object):
    def __init__(self):
        self.network = []
        self.chain = []
        self.block = []
        self.account = []
        self.transaction = []
        self.account = []
        self.transaction = []
        self.block = []
        self.chain = []


D_MODEL = []

# supported blockchains
def init_bc(bc_id, bc_name, net_id, net_name, cd_id, cd_name):

    cd = ChainDescriptor()
    cd.id = str(cd_id)
    cd.name = cd_name

    net = Network()
    net.id = str(net_id)
    net.name = net_name
    net.chainDescriptors.append(cd)

    bc = Blockchain()
    bc.id = str(bc_id)
    bc.name = bc_name
    bc.networks.append(net)

    return bc


def init_d_model():

    btc = init_bc("btc", "Bitcoin", "main", "Bitcoin mainnet", 1, "Bitcoin chain")
    eth = init_bc("eth", "Ethereum", "main", "Ethereum mainnet", 1, "Ethereum chain")
    ada = init_bc("ada", "Cardano", "main", "Cardano mainnet", 1, "Cardano chain")
    sol = init_bc("sol", "Solana", "main", "Solana mainnet", 1, "Solana chain")
    avax_p = init_bc("avax", "Avalanche", "main", "Avalanche Primary Network", "p", "P-Chain")
    avax_x = init_bc("avax", "Avalanche", "main", "Avalanche Primary Network", "x", "X-Chain")
    avax_c = init_bc("avax", "Avalanche", "main", "Avalanche Primary Network", "c", "C-Chain")
    
    D_MODEL.extend([ btc, eth, ada, sol, avax_p, avax_x, avax_c])

init_d_model()

def get_bc_by_id(bc_id, net_id, cd_id):

    for bc in D_MODEL:
        if bc.id == bc_id:
            for net in bc.networks:
                if net.id == net_id:
                    for cd in net.chainDescriptors:
                        if cd.id == cd_id:
                            return bc

    return None

def print_obj(obj):
    cl = type(obj).__name__
    inst = ""
    if 'id' in dir(obj):
        inst = obj.id
    elif 'height' in dir(obj):
        inst = obj.name
    else:
        inst = obj
    print(cl, inst)
    for attr in dir(obj):
        val = str(getattr(obj, attr))
        if not attr.startswith("_"):
            print(" -", attr, val)

"""
D_MODEL = [ D_BLOCKCHAINS ]

def chain():
    chain = {
        ID: None,
        DESCRIPTOR: '',
        CH_IS_UTXO_BASED: False,
        CH_IS_ACCOUNT_BASED: False
    }
    return chain

def block():
    block = {
        ID: None, 
        DESCRIPTOR: '',
        BLOCK_TIMESTAMP: None,
        BLOCK_TRANSACTION_IDS: [],
        BLOCK_TRANSACTIONS: {}
    }
    return block

def transaction():
    transaction = {
        ID: None,
        DESCRIPTOR: '', 
        TX_ADDRESS_FROM: None,
        TX_ADDRESS_TO: None,
        TX_BLOCK_ID: None,
        TX_BLOCK_DESCRIPTOR: None,
        TX_BALANCE: None,
        TX_DATA: None,
        TX_IS_CONTRACT_CALL: None,
        TX_CONTRACT_METHOD: None,
        TX_CONTRACT_DATA: None
    }
    return transaction

def account():
    account = {
        ID: None,
        DESCRIPTOR: '', 
        ACC_BALANCE: None,
        ACC_STORAGE: None,
        ACC_IS_SMART_CONTRACT: None
    }
    return account
"""
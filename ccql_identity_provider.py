import sys
from ccql_identity import identity_web3

NODE_DATADIR = "geth-data"
KEYSTORE_DIR = NODE_DATADIR + "/keystore"

class CCQL_Identity_Provider:

    identity = None

    def __init__(self):
        CCQL_Identity_Provider.identity = self.get_identity()

    def create_identity(self):
        web3c = identity_web3.Web3Client(KEYSTORE_DIR)
        address_prvk = web3c.create_identity()
        return address_prvk

    def initialize_identity(self):
        print("Initialize identity ...")
        web3c = identity_web3.Web3Client(KEYSTORE_DIR)
        if len(web3c.read_keystore()) < 1:
            web3c.create_identity()
        address_prvk = web3c.get_first_identity()
        return address_prvk

    def get_identity(self):

        if CCQL_Identity_Provider.identity == None:
            print("Parsing Web3 identity ...")
            web3c = identity_web3.Web3Client(KEYSTORE_DIR)
            acc = web3c.get_first_identity()
            CCQL_Identity_Provider.identity = acc

        if CCQL_Identity_Provider.identity == None:
            print("Error: unable to get first identity, possibly no identity exists")
            sys.exit(1)

        return CCQL_Identity_Provider.identity  

import os
import sys
import subprocess
import re
import json
import datetime
from web3 import Web3

NODE_DATADIR = "geth-data"
KEYSTORE_DIR = NODE_DATADIR + "/keystore"

class Identity:
    
    def __init__(self, address, privatekey):
        self.address = address
        self.privatekey = privatekey

class IdentityClient:

    def __init__(self, working_dir):
        self.init_dir = os.getcwd()
        self.working_dir = working_dir

    def read_keystore(self):
        os.makedirs(self.working_dir, exist_ok=True)
        keystore_files = []
        return keystore_files

    def create_identity(self):
        os.makedirs(self.working_dir, exist_ok=True)

    def get_first_identity(self):
        os.makedirs(self.working_dir, exist_ok=True)

class Web3Client(IdentityClient):

    ZERO_ADDRESS = "0x0"
    PUBLIC_ACCESS_KEY = "Maw6hljwdc2fVQ6iCSoz"

    def __init__(self, working_dir):
        super().__init__(working_dir)
        self.w3 = Web3()

    def read_keystore(self):
        super().read_keystore()
        keyfiles = os.listdir(self.working_dir)
        keystore_files = []
        for f in keyfiles:
            keystore_files.append(self.working_dir + "/" + f)
        keystore_files.sort()
        return keystore_files
    
    def read_keyfile(self, keyfile):
        keyfile_json = ""
        print("Reading key file", keyfile)
        with open(keyfile) as f:
            keyfile_json = f.read()
            prvk = self.w3.eth.account.decrypt(keyfile_json, self.PUBLIC_ACCESS_KEY)
            account = self.w3.eth.account.privateKeyToAccount(prvk)
            id = Identity(account.address, bytes(prvk))
            return id
            #return (accounts[keyfiles], pk)
        print("Key file not readable", keyfile)
        sys.exit()

    def create_identity(self):
        super().create_identity()
        account = self.w3.eth.account.create()
        keystore = self.w3.eth.account.encrypt(account.privateKey, self.PUBLIC_ACCESS_KEY)
        address = keystore["address"]
        keyfile = self.working_dir + "/" + datetime.datetime.utcnow().strftime("UTC--%Y-%m-%dT%H-%M-%S.%f000Z--") + address
        print("Writing key file", keyfile)
        with open(keyfile, "w") as f:
            f.write(json.dumps(keystore))
        return self.read_keyfile(keyfile)

    def get_first_identity(self):
        super().get_first_identity()
        keystore_files = self.read_keystore()
        if len(keystore_files) > 0:
            keyfile = keystore_files[-1]
            return self.read_keyfile(keyfile)
        print("No key file found in", self.working_dir)
        sys.exit()

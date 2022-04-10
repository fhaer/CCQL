import os
import sys
import shutil
import subprocess
import requests
import json

from . import transfer_client as tc

class IpfsCient(tc.TransferClient):

    IPFS = "ipfs"

    def __init__(self, timestamp, protocol_name):
        super().__init__(timestamp, protocol_name)

    def copy_to_repository(self, files, repository_dir):
        print("\nCopy files to repository ...\n")
        os.chdir(self.init_dir)
        for f in files:
            if os.path.isfile(f):
                print("Copy", f, "to", repository_dir)
                shutil.copy(f, repository_dir)
            else:
                print("Error: file not found", f)
                sys.exit()

    def pin_file(self, hash_value):
        PINATA_BIN_BY_HASH_URL = "https://api.pinata.cloud/pinning/pinByHash";
        PINATA_REQ = {'hashToPin': hash_value }
        API_Key = '08cd66db588ec49824ab'
        API_Sec = 'f146f2c5390ca4b4e4a3c6c2e8693a61fca68f25ba5eef10bec443483f71be47'
        PINATA_HEADERS =  {
            'Content-Type': 'application/json',
            'pinata_api_key': API_Key,
            'pinata_secret_api_key': API_Sec
        }
        print("\nPinning file", hash_value)
        #requests.post(PINATA_BIN_BY_HASH_URL, data=PINATA_REQ, headers=PINATA_HEADERS)
        response = requests.post(PINATA_BIN_BY_HASH_URL, data=json.dumps(PINATA_REQ), headers=PINATA_HEADERS)
        print(response.text)
        #print(response.request.headers)

    def ipfs_init_add_files(self, files):
        print("\nIPFS add ...\n")
        os.chdir(self.repository_dir)
        print(os.getcwd())
        #subprocess.run([IPFS, "init", "--profile", "server"])
        cid_values = []
        cid_uris = []
        for f in files:
            print("add", f)
            res = subprocess.run([self.IPFS, "add", "-w", "-Q", os.path.basename(f)], stdout=subprocess.PIPE)
            cid = res.stdout.decode('utf-8').rstrip("\n")
            cid_uri = "ipfs:" + cid #+ "/" + os.path.basename(f)
            #cid_gateway_uri = "http://127.0.0.1:8080/ipfs/" + cid #+ "/" + os.path.basename(f)
            cid_values.append(cid)
            cid_uris.append(cid_uri)
        return cid_values, cid_uris

    def ipfs_init_add_directory(self, files):
        print("\nIPFS add ...\n")
        os.chdir(self.repository_dir)
        print(os.getcwd())
        #subprocess.run([self.IPFS, "init", "--profile", "server"])
        cid_values = []
        cid_uris = []
        print("add", self.repository_dir)
        res = subprocess.run([self.IPFS, "add", "-r", "-Q", "."], stdout=subprocess.PIPE)
        cid = res.stdout.decode('utf-8').rstrip("\n")
        cid_uri = "ipfs:" + cid #+ "/" + os.path.basename(f)
        #cid_gateway_uri = "http://127.0.0.1:8080/ipfs/" + cid #+ "/" + os.path.basename(f)
        cid_values.append(cid)
        cid_uris.append(cid_uri)
        return cid_values, cid_uris

    def distribute(self, files):
        print("\nDistribute using IPFS ...")
        super().distribute()
        self.repository_dir = os.getcwd()

        self.copy_to_repository(files, self.repository_dir)
        (cid_values, cid_uris) = self.ipfs_init_add_directory(files)

        print("\nPin IPFS CIDs ...\n")
        for cid in cid_values:
            self.pin_file(cid)
        print()

        os.chdir(self.init_dir)
        return cid_uris
    
    def ls_repository(self, repository_dir):
        files = []
        for f in os.listdir(repository_dir):
            files.append(repository_dir + "/" + f)
        return files

    def retrieve(self, repository_uri):
        print("\nRetrieve using IPFS from", repository_uri, "\n")
        super().retrieve()
        
        os.chdir(self.init_dir)
        subprocess.run([self.IPFS, "get", "-o", self.working_dir, repository_uri])
        return self.ls_repository(self.working_dir)

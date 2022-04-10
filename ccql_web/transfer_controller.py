import datetime

from .transfer import transfer_client
from .transfer import git
from .transfer import http
from .transfer import ipfs

def get_timestamp():
    return datetime.datetime.utcnow().strftime("UTC--%Y-%m-%dT%H-%M-%S.%f000Z")

def distribute_ipfs(file):
    timestamp = get_timestamp()
    transfer_client = ipfs.IpfsCient(timestamp, "ipfs")
    addresses = transfer_client.distribute(file)
    return addresses

def distribute_git(uri, file):
    timestamp = get_timestamp()
    transfer_client = git.GitClient(timestamp, "git")
    addresses = transfer_client.distribute(uri, file)
    return addresses

def distribute_http(uri, file):
    timestamp = get_timestamp()
    transfer_client = http.HttpClient(timestamp, "http")
    addresses = transfer_client.distribute(uri, file)
    return addresses

def retrieve(uri):

    files = []

    timestamp = get_timestamp()

    if (uri.startswith("http") and uri.endswith(".git")):
        transfer_client = git.GitClient(timestamp, "git")
        files = transfer_client.retrieve(uri)
    
    elif uri.startswith("http://127.0.0.1:8080/ipfs/"):
        transfer_client = ipfs.IpfsCient(timestamp, "ipfs")
        files = transfer_client.retrieve(uri[27:])

    elif uri.startswith("http"):
        transfer_client = http.HttpClient(timestamp, "http")
        files = transfer_client.retrieve(uri)

    elif uri.startswith("ipfs:"):
        transfer_client = ipfs.IpfsCient(timestamp, "ipfs")
        files = transfer_client.retrieve(uri[5:])
    
    return files
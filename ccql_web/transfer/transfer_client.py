import os 

class TransferClient:
    """Super class for all transfer clients offering distribute and retrieve functionality"""

    TRANSFER_DIR = "transfer_client"

    def __init__(self, timestamp, protocol_name):
        self.working_dir = self.TRANSFER_DIR + "/" + timestamp + "--" + protocol_name
        self.init_dir = os.getcwd()

    def distribute(self):
        os.makedirs(self.working_dir, exist_ok=True)
        os.chdir(self.working_dir)

    def retrieve(self):
        os.makedirs(self.working_dir, exist_ok=True)
        os.chdir(self.working_dir)

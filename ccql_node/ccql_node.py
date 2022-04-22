import os
import subprocess
import sys
import binascii
import requests
import json
from web3 import Web3

from . import ccql_data

LIMIT = 3

# for proof-of-authority geth nodes, development
#from web3.middleware import geth_poa_middleware

class CCQL_Node:

	def __init__(self):
		self.working_dir = "."

	def run_node(self):
		os.makedirs(self.working_dir, exist_ok=True)
		os.chdir(self.working_dir)

	def is_connected(self):
		return False

class Geth_Node(CCQL_Node):

	GETH = "geth"
	
	GETH_DATADIR = "geth-data"
	GETH_DATADIR_POA = "geth-data-poa"
	
	GETH_DATADIR_ANCIENT = "geth-data-ancient"
	GETH_DATADIR_ANCIENT_POA = "geth-data-ancient-poa"

	GETH_DAG_DIR = "geth-dag"

	def __init__(self, working_dir):
		super().__init__(working_dir)

	def run_node(self, account_address, account_password_file):
		super().run_node()
		subprocess.run([self.GETH, "--datadir", self.GETH_DATADIR, "datadir.ancient", self.GETH_DATADIR_ANCIENT, "--ethash.dagdir", self.GETH_DAG_DIR, "--cache", 4000, "--syncmode", "full", "--ws", "--ws.api", "eth,net,web3"])
	
	def run_node_poa_development(self, account_address, account_password_file):
		super().run_node()
		subprocess.run([self.GETH, "--datadir", self.GETH_DATADIR_POA, "datadir.ancient", self.GETH_DATADIR_ANCIENT_POA, "--cache", 4000, "--syncmode", "full", "--rpccorsdomain", "*", "networkid", 55194, "--nodiscover", "--vmdebug"])
		# --unlock "0xf7b13d6b33EC6492AfB9756205D1A9e58Bab70ee" -allow-insecure-unlock console

class Web3_Eth_Node(CCQL_Node):

	# Node Web Socket Connection
	#WEB3_ADDRESS = "ws://51.154.78.219:46804"
	WEB3_ADDRESS = "wss://mainnet.infura.io/ws/v3/5cc53e4f3f614825be68d6aae4897cf4"

	# Node HTTP Connection
	#WEB3_ADDRESS = "http://127.0.0.1:8545"
	#WEB3_ADDRESS = "https://mainnet.infura.io/v3/5cc53e4f3f614825be68d6aae4897cf4"

	def __init__(self, identity):
		if len(identity) > 0 and identity != "0x0":
			self.ci_account_address = Web3.toChecksumAddress(identity.address)
			self.ci_account_privatekey = identity.privatekey

		if self.WEB3_ADDRESS.startswith("ws"):
			provider = Web3.WebsocketProvider(self.WEB3_ADDRESS) #, websocket_timeout=3)
		else:
			provider = Web3.HTTPProvider(self.WEB3_ADDRESS)
		
		self.w3 = Web3(provider)

	def is_connected(self):
		return self.w3.isConnected()

	def get_block(self, block_id, linked_block_desc, limit):
		
		#print("block_id", block_id)

    	# block_id must be numberic, >=0 for block height, <0 for block depth
		if isinstance(block_id, int) or block_id.isnumeric():
			block_id = int(block_id)
		else:
			print("Error: block descriptor is not numeric")
			sys.exit()
		
		# construct block id for web3
		block_id_web3 = block_id
		if (block_id == -1):
			block_id_web3 = 'latest'
		elif (block_id_web3 < -1):
			tip = self.w3.eth.getBlockNumber()
			block_id_web3 = tip + block_id + 1

		web3_block = self.w3.eth.get_block(block_id_web3, True)
		#print(web3_block)

		block = ccql_data.Block()
		block_desc = ccql_data.BlockDescriptor()
		block.id = web3_block.hash.hex()
		
		block_desc.height = web3_block.number
		block_desc.timestamp = web3_block.timestamp
		block.descriptor = block_desc

		block.linkedBlockDescriptor = linked_block_desc

		i = 0
		for web3_tx in web3_block.transactions:

			tx = ccql_data.Transaction()
			tx_desc = ccql_data.TransactionDescriptor()

			tx.id = web3_tx.hash.hex()
			
			# Ethereum gas after London hardfork: maxFeePerGas, maxPriorityFeePerGas
			# Ethereum gas before London hardfork: gas, gasPrice
			if 'maxFeePerGas' in web3_tx and not web3_tx.maxFeePerGas is None:
				baseFeePerGas = web3_tx.maxFeePerGas - web3_tx.maxPriorityFeePerGas
				fee = baseFeePerGas * web3_tx.gas
				tx.fee = fee / 10**18
				tx.feeUnit = 'eth'
			elif 'gasPrice' in web3_tx and not web3_tx.gasPrice is None:
				fee = web3_tx.gasPrice * web3_tx.gas
				tx.fee = fee / 10**18
				tx.feeUnit = 'eth'

			tx_desc.from_.append(web3_tx['from'])
			tx_desc.to.append(web3_tx['to'])
			tx_desc.value = web3_tx.value / 10**18
			tx_desc.data = web3_tx.input

			tx.descriptor.append(tx_desc)
			block.transactions.append(tx)
			
			ccql_data.print_obj(tx)
			ccql_data.print_obj(tx_desc)
			#print(tx)
			#print(tx_desc)

			i += 1
			if i >= limit:
				break

		return block


	def get_blocks(self, block_id_list):
		blocks = []
		for block_id in block_id_list:
			blocks.append(self.get_block(block_id))
		return blocks


	def get_transaction(self, transaction_descriptor):

		if not isinstance(transaction_descriptor, str):
			print("Error: transaction descriptor is not a string")
			sys.exit()
		
		# construct block desciptor for web3
		transaction_descriptor_web3 = transaction_descriptor
		if (transaction_descriptor == "0x0"):
			transaction_descriptor_web3 = '0xa'

		web3_tx = self.w3.eth.getTransaction(transaction_descriptor_web3)
		
		tx = ccql_data.transaction()
		tx[ccql_data.ID] = transaction_descriptor_web3
		tx[ccql_data.TX_ADDRESS_FROM] = tx['from']
		tx[ccql_data.TX_ADDRESS_TO] = web3_tx.to
		tx[ccql_data.TX_BALANCE] = web3_tx.value * pow(10, -18) # convert wei to eth
		tx[ccql_data.TX_DATA] = web3_tx.input
		tx[ccql_data.TX_BLOCK_ID] = web3_tx.blockNumber
		tx[ccql_data.TX_block_id] = web3_tx.blockHash

		return tx


	def get_transactions(self, transaction_descriptor_list):
		transactions = []
		for transaction_descriptor in transaction_descriptor_list:
			transactions.append(self.get_transaction(transaction_descriptor))
		return transactions


	def get_account(self, account_descriptor):

		if not isinstance(account_descriptor, str):
			print("Error: account descriptor is not a string")
			sys.exit()
		
		# construct block desciptor for web3
		account_descriptor_web3 = account_descriptor
		if (account_descriptor == "0x0"):
			account_descriptor_web3 = '0xa'

		web3_tx = self.w3.eth.getBalance(account_descriptor_web3)

		ac = ccql_data.account()
		ac[ccql_data.ID] = account_descriptor_web3
		ac[ccql_data.DESCRIPTOR] = account_descriptor
		ac[ccql_data.AC_BALANCE] = web3_tx * pow(10, -18) # convert wei to eth

		return ac


	def get_accounts(self, account_descriptor_list):
		accounts = []
		for account_descriptor in account_descriptor_list:
			accounts.append(self.get_account(account_descriptor))
		return accounts


	def get_contract(self, address, abi):

		self.contract = None
		self.contract = self.w3.eth.contract(address=address, abi=abi)

		if self.contract is None:
			print("Contract not found, abort")
			sys.exit()
			
		return self.contract

	def call_contract(self, address, abi, function, parameters):
		
		self.get_contract()
			
		contract = self.get_attestation_contract()

		#merkle_root_bytes32 = data_coding.encode_binary_bytes32(merkle_root)
		#merkle_root_prime_bytes32 = data_coding.encode_binary_bytes32(merkle_root)

		# TODO: receipt = contract.functions.function(parameters).call()
		
		return None

	def get_current_gas_price(self):
		gas_price_api = "https://www.etherchain.org/api/gasPriceOracle"
		r = requests.get(gas_price_api).json()
		gas_price = Web3.toWei(r.fastest, 'gwei')

		if gas_price > 100000000000:
			print("Gas price exceeds 100 Gwei, abort")
			sys.exit()

		return gas_price

	def get_transaction_info(self):
		nonce = self.w3.eth.getTransactionCount(self.ci_account_address)
		#block = self.w3.eth.getBlock("latest")

		gas_price = self.get_current_gas_price()
		gas_limit = 300000

		tx = {
				"from": self.ci_account_address,
				"value": 0,
				'chainId': 1,
				'nonce': nonce,
				'gas': gas_limit,
				'gasPrice': gas_price
		}

		print("Gas limit:", gas_limit)
		print("Gas price:", gas_price)

		return tx

	def send_transaction(self, tx):
		tx_hash = ""
		pk_b = self.ci_account_privatekey
		signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=pk_b)
		print(signed_tx)
		#signed_tx.r / s / v
		tx_hash = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
		
		receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)

		return receipt #tx_hash

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
from web3.middleware import geth_poa_middleware

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

class Web3_Avalanche_Node(CCQL_Node):

	# Node Web Socket Connection
	#WEB3_ADDRESS = "ws://51.154.78.219:46804"
	WEB3_ADDRESS = "https://api.avax.network/ext/bc/C/rpc"

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

		self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

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
		status = ccql_data.Status()
		validationDesc = ccql_data.ValidationDescriptor()

		block.id = web3_block.hash.hex()
		block.validationDescriptor = validationDesc
		block.validationDescriptor.proposer = []
		block.validationDescriptor.creator = []
		block.validationDescriptor.attestations = []
		
		block_desc.height = web3_block.number
		block_desc.timestamp = web3_block.timestamp
		block_desc.status = status
		block.descriptor = block_desc

		block.linkedBlockDescriptor = linked_block_desc

		accounts = {}

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
				tx.feeUnit = "AVAX"
			elif 'gasPrice' in web3_tx and not web3_tx.gasPrice is None:
				fee = web3_tx.gasPrice * web3_tx.gas
				tx.fee = fee / 10**18
				tx.feeUnit = "AVAX"

			from_addr = ccql_data.Address()
			from_addr.id = web3_tx['from']
			to_addr = ccql_data.Address()
			to_addr.id = web3_tx['to']

			accounts[from_addr.id] = from_addr
			accounts[to_addr.id] = to_addr

			tx_desc.from_.append(from_addr)
			tx_desc.to.append(to_addr)

			tx_desc.value = web3_tx.value / 10**18
			tx_desc.unit = "AVAX"
			tx_desc.data = web3_tx.input

			tx.descriptor.append(tx_desc)
			block.transactions.append(tx)
			
			#ccql_data.print_obj(tx)
			#ccql_data.print_obj(tx_desc)
			#print(tx)
			#print(tx_desc)

			i += 1
			if i >= limit:
				break

		for a in accounts.keys():
			block.accounts.append(accounts[a])

		return block


	def get_blocks(self, block_id_list):
		blocks = []
		for block_id in block_id_list:
			blocks.append(self.get_block(block_id))
		return blocks


	def get_transaction(self, transaction_id):

		if not isinstance(transaction_id, str):
			print("Error: transaction descriptor is not a string")
			sys.exit()
		
		# construct block desciptor for web3
		transaction_id_web3 = transaction_id
		if (transaction_id == "0x0"):
			transaction_id_web3 = '0xa'

		web3_tx = self.w3.eth.getTransaction(transaction_id_web3)
		
		tx = ccql_data.Transaction()
		tx_desc = ccql_data.TransactionDescriptor()

		tx.id = web3_tx.hash.hex()
		
		# Ethereum gas after London hardfork: maxFeePerGas, maxPriorityFeePerGas
		# Ethereum gas before London hardfork: gas, gasPrice
		if 'maxFeePerGas' in web3_tx and not web3_tx.maxFeePerGas is None:
			baseFeePerGas = web3_tx.maxFeePerGas - web3_tx.maxPriorityFeePerGas
			fee = baseFeePerGas * web3_tx.gas
			tx.fee = fee / 10**18
			tx.feeUnit = "AVAX"
		elif 'gasPrice' in web3_tx and not web3_tx.gasPrice is None:
			fee = web3_tx.gasPrice * web3_tx.gas
			tx.fee = fee / 10**18
			tx.feeUnit = "AVAX"

		from_addr = ccql_data.Address()
		from_addr.id = web3_tx['from']
		to_addr = ccql_data.Address()
		to_addr.id = web3_tx['to']

		#tx[ccql_data.TX_BLOCK_ID] = web3_tx.blockNumber
		#tx[ccql_data.TX_block_id] = web3_tx.blockHash

		tx_desc.from_.append(from_addr)
		tx_desc.to.append(to_addr)

		tx_desc.value = web3_tx.value / 10**18
		tx_desc.unit = "AVAX"
		tx_desc.data = web3_tx.input

		tx.descriptor.append(tx_desc)

		return tx


	def get_transactions(self, transaction_id_list):
		transactions = []
		for transaction_id in transaction_id_list:
			transactions.append(self.get_transaction(transaction_id))
		return transactions


	def get_account(self, account_id):

		if not isinstance(account_id, str):
			print("Error: account descriptor is not a string")
			sys.exit()
		
		# construct block desciptor for web3
		account_id_web3 = account_id
		if (account_id == "0x0"):
			account_id_web3 = '0xa'
		else:
			account_id_web3 = self.w3.toChecksumAddress(account_id)

		ac = ccql_data.Account()
		ac_desc = ccql_data.AccountDescriptor()

		ac.id = account_id

		# Avalanche supports the "AVAX/AVAX" asset only
		as_avax = ccql_data.Asset()
		as_type = ccql_data.AssetType()

		as_type.id = 1
		as_type.typeName = "AVAX"
		as_type.unit = "AVAX"

		as_avax.id = 1
		as_avax.assetType = as_type

		# Balance returned in 10^⁻18 Eth (Wei)
		web3_balance = self.w3.eth.getBalance(account_id_web3)
		as_avax.balance = web3_balance * pow(10, -18)

		ac.accountDescriptor = ac_desc
		ac.assets.append(as_avax)

		return ac


	def get_accounts(self, account_id_list):
		accounts = []
		for account_id in account_id_list:
			accounts.append(self.get_account(account_id))
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
		status = ccql_data.Status()
		validationDesc = ccql_data.ValidationDescriptor()

		block.id = web3_block.hash.hex()
		block.validationDescriptor = validationDesc
		block.validationDescriptor.proposer = []
		block.validationDescriptor.creator = []
		block.validationDescriptor.attestations = []
		
		block_desc.height = web3_block.number
		block_desc.timestamp = web3_block.timestamp
		block_desc.status = status
		block.descriptor = block_desc

		block.linkedBlockDescriptor = linked_block_desc

		accounts = {}

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
				tx.feeUnit = "ETH"
			elif 'gasPrice' in web3_tx and not web3_tx.gasPrice is None:
				fee = web3_tx.gasPrice * web3_tx.gas
				tx.fee = fee / 10**18
				tx.feeUnit = "ETH"

			from_addr = ccql_data.Address()
			from_addr.id = web3_tx['from']
			to_addr = ccql_data.Address()
			to_addr.id = web3_tx['to']

			accounts[from_addr.id] = from_addr
			accounts[to_addr.id] = to_addr

			tx_desc.from_.append(from_addr)
			tx_desc.to.append(to_addr)

			tx_desc.value = web3_tx.value / 10**18
			tx_desc.unit = "ETH"
			tx_desc.data = web3_tx.input

			tx.descriptor.append(tx_desc)
			block.transactions.append(tx)
			
			#ccql_data.print_obj(tx)
			#ccql_data.print_obj(tx_desc)
			#print(tx)
			#print(tx_desc)

			i += 1
			if i >= limit:
				break

		for a in accounts.keys():
			block.accounts.append(accounts[a])

		return block


	def get_blocks(self, block_id_list):
		blocks = []
		for block_id in block_id_list:
			blocks.append(self.get_block(block_id))
		return blocks


	def get_transaction(self, transaction_id):

		if not isinstance(transaction_id, str):
			print("Error: transaction descriptor is not a string")
			sys.exit()
		
		# construct block desciptor for web3
		transaction_id_web3 = transaction_id
		if (transaction_id == "0x0"):
			transaction_id_web3 = '0xa'

		web3_tx = self.w3.eth.getTransaction(transaction_id_web3)
		
		tx = ccql_data.Transaction()
		tx_desc = ccql_data.TransactionDescriptor()

		tx.id = web3_tx.hash.hex()
		
		# Ethereum gas after London hardfork: maxFeePerGas, maxPriorityFeePerGas
		# Ethereum gas before London hardfork: gas, gasPrice
		if 'maxFeePerGas' in web3_tx and not web3_tx.maxFeePerGas is None:
			baseFeePerGas = web3_tx.maxFeePerGas - web3_tx.maxPriorityFeePerGas
			fee = baseFeePerGas * web3_tx.gas
			tx.fee = fee / 10**18
			tx.feeUnit = "ETH"
		elif 'gasPrice' in web3_tx and not web3_tx.gasPrice is None:
			fee = web3_tx.gasPrice * web3_tx.gas
			tx.fee = fee / 10**18
			tx.feeUnit = "ETH"

		from_addr = ccql_data.Address()
		from_addr.id = web3_tx['from']
		to_addr = ccql_data.Address()
		to_addr.id = web3_tx['to']

		#tx[ccql_data.TX_BLOCK_ID] = web3_tx.blockNumber
		#tx[ccql_data.TX_block_id] = web3_tx.blockHash

		tx_desc.from_.append(from_addr)
		tx_desc.to.append(to_addr)

		tx_desc.value = web3_tx.value / 10**18
		tx_desc.unit = "ETH"
		tx_desc.data = web3_tx.input

		tx.descriptor.append(tx_desc)

		return tx


	def get_transactions(self, transaction_id_list):
		transactions = []
		for transaction_id in transaction_id_list:
			transactions.append(self.get_transaction(transaction_id))
		return transactions


	def get_account(self, account_id):

		if not isinstance(account_id, str):
			print("Error: account descriptor is not a string")
			sys.exit()
		
		# construct block desciptor for web3
		account_id_web3 = account_id
		if (account_id == "0x0"):
			account_id_web3 = '0xa'
		else:
			account_id_web3 = self.w3.toChecksumAddress(account_id)

		ac = ccql_data.Account()
		ac_desc = ccql_data.AccountDescriptor()

		ac.id = account_id

		# Ethereum supports the "Ether/ETH" asset only
		as_eth = ccql_data.Asset()
		as_type = ccql_data.AssetType()

		as_type.id = 1
		as_type.typeName = "Ether"
		as_type.unit = "ETH"

		as_eth.id = 1
		as_eth.assetType = as_type

		# Balance returned in 10^⁻18 Eth (Wei)
		web3_balance = self.w3.eth.getBalance(account_id_web3)
		as_eth.balance = web3_balance * pow(10, -18)

		ac.accountDescriptor = ac_desc
		ac.assets.append(as_eth)

		return ac


	def get_accounts(self, account_id_list):
		accounts = []
		for account_id in account_id_list:
			accounts.append(self.get_account(account_id))
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

class Web3_Solana_Node(CCQL_Node):

	# Node Web Socket Connection
	#WEB3_ADDRESS = "ws://51.154.78.219:46804"
	WEB3_ADDRESS = "https://api.mainnet-beta.solana.com"

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

		#self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
		
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
		status = ccql_data.Status()
		validationDesc = ccql_data.ValidationDescriptor()

		block.id = web3_block.hash.hex()
		block.validationDescriptor = validationDesc
		block.validationDescriptor.proposer = []
		block.validationDescriptor.creator = []
		block.validationDescriptor.attestations = []
		
		block_desc.height = web3_block.number
		block_desc.timestamp = web3_block.timestamp
		block_desc.status = status
		block.descriptor = block_desc

		block.linkedBlockDescriptor = linked_block_desc

		accounts = {}

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
				tx.feeUnit = "ETH"
			elif 'gasPrice' in web3_tx and not web3_tx.gasPrice is None:
				fee = web3_tx.gasPrice * web3_tx.gas
				tx.fee = fee / 10**18
				tx.feeUnit = "ETH"

			from_addr = ccql_data.Address()
			from_addr.id = web3_tx['from']
			to_addr = ccql_data.Address()
			to_addr.id = web3_tx['to']

			accounts[from_addr.id] = from_addr
			accounts[to_addr.id] = to_addr

			tx_desc.from_.append(from_addr)
			tx_desc.to.append(to_addr)

			tx_desc.value = web3_tx.value / 10**18
			tx_desc.data = web3_tx.input

			tx.descriptor.append(tx_desc)
			block.transactions.append(tx)
			
			#ccql_data.print_obj(tx)
			#ccql_data.print_obj(tx_desc)
			#print(tx)
			#print(tx_desc)

			i += 1
			if i >= limit:
				break

		for a in accounts.keys():
			block.accounts.append(accounts[a])

		return block


	def get_blocks(self, block_id_list):
		blocks = []
		for block_id in block_id_list:
			blocks.append(self.get_block(block_id))
		return blocks


	def get_transaction(self, transaction_id):

		if not isinstance(transaction_id, str):
			print("Error: transaction descriptor is not a string")
			sys.exit()
		
		# construct block desciptor for web3
		transaction_id_web3 = transaction_id
		if (transaction_id == "0x0"):
			transaction_id_web3 = '0xa'

		web3_tx = self.w3.eth.getTransaction(transaction_id_web3)
		
		tx = ccql_data.Transaction()
		tx_desc = ccql_data.TransactionDescriptor()

		tx.id = web3_tx.hash.hex()
		
		# Ethereum gas after London hardfork: maxFeePerGas, maxPriorityFeePerGas
		# Ethereum gas before London hardfork: gas, gasPrice
		if 'maxFeePerGas' in web3_tx and not web3_tx.maxFeePerGas is None:
			baseFeePerGas = web3_tx.maxFeePerGas - web3_tx.maxPriorityFeePerGas
			fee = baseFeePerGas * web3_tx.gas
			tx.fee = fee / 10**18
			tx.feeUnit = "ETH"
		elif 'gasPrice' in web3_tx and not web3_tx.gasPrice is None:
			fee = web3_tx.gasPrice * web3_tx.gas
			tx.fee = fee / 10**18
			tx.feeUnit = "ETH"

		from_addr = ccql_data.Address()
		from_addr.id = web3_tx['from']
		to_addr = ccql_data.Address()
		to_addr.id = web3_tx['to']

		#tx[ccql_data.TX_BLOCK_ID] = web3_tx.blockNumber
		#tx[ccql_data.TX_block_id] = web3_tx.blockHash

		tx_desc.from_.append(from_addr)
		tx_desc.to.append(to_addr)

		tx_desc.value = web3_tx.value / 10**18
		tx_desc.data = web3_tx.input

		tx.descriptor.append(tx_desc)

		return tx


	def get_transactions(self, transaction_id_list):
		transactions = []
		for transaction_id in transaction_id_list:
			transactions.append(self.get_transaction(transaction_id))
		return transactions


	def get_account(self, account_id):

		if not isinstance(account_id, str):
			print("Error: account descriptor is not a string")
			sys.exit()
		
		# construct block desciptor for web3
		account_id_web3 = account_id
		if (account_id == "0x0"):
			account_id_web3 = '0xa'
		else:
			account_id_web3 = self.w3.toChecksumAddress(account_id)

		ac = ccql_data.Account()
		ac_desc = ccql_data.AccountDescriptor()

		ac.id = account_id

		# Ethereum supports the "Ether/ETH" asset only
		as_eth = ccql_data.Asset()
		as_type = ccql_data.AssetType()

		as_type.id = 1
		as_type.typeName = "Ether"
		as_type.unit = "ETH"

		as_eth.id = 1
		as_eth.assetType = as_type

		# Balance returned in 10^⁻18 Eth (Wei)
		web3_balance = self.w3.eth.getBalance(account_id_web3)
		as_eth.balance = web3_balance * pow(10, -18)

		ac.accountDescriptor = ac_desc
		ac.assets.append(as_eth)

		return ac


	def get_accounts(self, account_id_list):
		accounts = []
		for account_id in account_id_list:
			accounts.append(self.get_account(account_id))
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
		status = ccql_data.Status()
		validationDesc = ccql_data.ValidationDescriptor()

		block.id = web3_block.hash.hex()
		block.validationDescriptor = validationDesc
		block.validationDescriptor.proposer = []
		block.validationDescriptor.creator = []
		block.validationDescriptor.attestations = []
		
		block_desc.height = web3_block.number
		block_desc.timestamp = web3_block.timestamp
		block_desc.status = status
		block.descriptor = block_desc

		block.linkedBlockDescriptor = linked_block_desc

		accounts = {}

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
				tx.feeUnit = "ETH"
			elif 'gasPrice' in web3_tx and not web3_tx.gasPrice is None:
				fee = web3_tx.gasPrice * web3_tx.gas
				tx.fee = fee / 10**18
				tx.feeUnit = "ETH"

			from_addr = ccql_data.Address()
			from_addr.id = web3_tx['from']
			to_addr = ccql_data.Address()
			to_addr.id = web3_tx['to']

			accounts[from_addr.id] = from_addr
			accounts[to_addr.id] = to_addr

			tx_desc.from_.append(from_addr)
			tx_desc.to.append(to_addr)

			tx_desc.value = web3_tx.value / 10**18
			tx_desc.unit = "ETH"
			tx_desc.data = web3_tx.input

			tx.descriptor.append(tx_desc)
			block.transactions.append(tx)
			
			#ccql_data.print_obj(tx)
			#ccql_data.print_obj(tx_desc)
			#print(tx)
			#print(tx_desc)

			i += 1
			if i >= limit:
				break

		for a in accounts.keys():
			block.accounts.append(accounts[a])

		return block


	def get_blocks(self, block_id_list):
		blocks = []
		for block_id in block_id_list:
			blocks.append(self.get_block(block_id))
		return blocks


	def get_transaction(self, transaction_id):

		if not isinstance(transaction_id, str):
			print("Error: transaction descriptor is not a string")
			sys.exit()
		
		# construct block desciptor for web3
		transaction_id_web3 = transaction_id
		if (transaction_id == "0x0"):
			transaction_id_web3 = '0xa'

		web3_tx = self.w3.eth.getTransaction(transaction_id_web3)
		
		tx = ccql_data.Transaction()
		tx_desc = ccql_data.TransactionDescriptor()

		tx.id = web3_tx.hash.hex()
		
		# Ethereum gas after London hardfork: maxFeePerGas, maxPriorityFeePerGas
		# Ethereum gas before London hardfork: gas, gasPrice
		if 'maxFeePerGas' in web3_tx and not web3_tx.maxFeePerGas is None:
			baseFeePerGas = web3_tx.maxFeePerGas - web3_tx.maxPriorityFeePerGas
			fee = baseFeePerGas * web3_tx.gas
			tx.fee = fee / 10**18
			tx.feeUnit = "ETH"
		elif 'gasPrice' in web3_tx and not web3_tx.gasPrice is None:
			fee = web3_tx.gasPrice * web3_tx.gas
			tx.fee = fee / 10**18
			tx.feeUnit = "ETH"

		from_addr = ccql_data.Address()
		from_addr.id = web3_tx['from']
		to_addr = ccql_data.Address()
		to_addr.id = web3_tx['to']

		#tx[ccql_data.TX_BLOCK_ID] = web3_tx.blockNumber
		#tx[ccql_data.TX_block_id] = web3_tx.blockHash

		tx_desc.from_.append(from_addr)
		tx_desc.to.append(to_addr)

		tx_desc.value = web3_tx.value / 10**18
		tx_desc.unit = "ETH"
		tx_desc.data = web3_tx.input

		tx.descriptor.append(tx_desc)

		return tx


	def get_transactions(self, transaction_id_list):
		transactions = []
		for transaction_id in transaction_id_list:
			transactions.append(self.get_transaction(transaction_id))
		return transactions


	def get_account(self, account_id):

		if not isinstance(account_id, str):
			print("Error: account descriptor is not a string")
			sys.exit()
		
		# construct block desciptor for web3
		account_id_web3 = account_id
		if (account_id == "0x0"):
			account_id_web3 = '0xa'
		else:
			account_id_web3 = self.w3.toChecksumAddress(account_id)

		ac = ccql_data.Account()
		ac_desc = ccql_data.AccountDescriptor()

		ac.id = account_id

		# Ethereum supports the "Ether/ETH" asset only
		as_eth = ccql_data.Asset()
		as_type = ccql_data.AssetType()

		as_type.id = 1
		as_type.typeName = "Ether"
		as_type.unit = "ETH"

		as_eth.id = 1
		as_eth.assetType = as_type

		# Balance returned in 10^⁻18 Eth (Wei)
		web3_balance = self.w3.eth.getBalance(account_id_web3)
		as_eth.balance = web3_balance * pow(10, -18)

		ac.accountDescriptor = ac_desc
		ac.assets.append(as_eth)

		return ac


	def get_accounts(self, account_id_list):
		accounts = []
		for account_id in account_id_list:
			accounts.append(self.get_account(account_id))
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


class Web3_Solana_Node(CCQL_Node):

	# Node Web Socket Connection
	#WEB3_ADDRESS = "ws://51.154.78.219:46804"
	WEB3_ADDRESS = "https://api.mainnet-beta.solana.com"

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

		#self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
		
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
		status = ccql_data.Status()
		validationDesc = ccql_data.ValidationDescriptor()

		block.id = web3_block.hash.hex()
		block.validationDescriptor = validationDesc
		block.validationDescriptor.proposer = []
		block.validationDescriptor.creator = []
		block.validationDescriptor.attestations = []
		
		block_desc.height = web3_block.number
		block_desc.timestamp = web3_block.timestamp
		block_desc.status = status
		block.descriptor = block_desc

		block.linkedBlockDescriptor = linked_block_desc

		accounts = {}

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
				tx.feeUnit = "ETH"
			elif 'gasPrice' in web3_tx and not web3_tx.gasPrice is None:
				fee = web3_tx.gasPrice * web3_tx.gas
				tx.fee = fee / 10**18
				tx.feeUnit = "ETH"

			from_addr = ccql_data.Address()
			from_addr.id = web3_tx['from']
			to_addr = ccql_data.Address()
			to_addr.id = web3_tx['to']

			accounts[from_addr.id] = from_addr
			accounts[to_addr.id] = to_addr

			tx_desc.from_.append(from_addr)
			tx_desc.to.append(to_addr)

			tx_desc.value = web3_tx.value / 10**18
			tx_desc.data = web3_tx.input

			tx.descriptor.append(tx_desc)
			block.transactions.append(tx)
			
			#ccql_data.print_obj(tx)
			#ccql_data.print_obj(tx_desc)
			#print(tx)
			#print(tx_desc)

			i += 1
			if i >= limit:
				break

		for a in accounts.keys():
			block.accounts.append(accounts[a])

		return block


	def get_blocks(self, block_id_list):
		blocks = []
		for block_id in block_id_list:
			blocks.append(self.get_block(block_id))
		return blocks


	def get_transaction(self, transaction_id):

		if not isinstance(transaction_id, str):
			print("Error: transaction descriptor is not a string")
			sys.exit()
		
		# construct block desciptor for web3
		transaction_id_web3 = transaction_id
		if (transaction_id == "0x0"):
			transaction_id_web3 = '0xa'

		web3_tx = self.w3.eth.getTransaction(transaction_id_web3)
		
		tx = ccql_data.Transaction()
		tx_desc = ccql_data.TransactionDescriptor()

		tx.id = web3_tx.hash.hex()
		
		# Ethereum gas after London hardfork: maxFeePerGas, maxPriorityFeePerGas
		# Ethereum gas before London hardfork: gas, gasPrice
		if 'maxFeePerGas' in web3_tx and not web3_tx.maxFeePerGas is None:
			baseFeePerGas = web3_tx.maxFeePerGas - web3_tx.maxPriorityFeePerGas
			fee = baseFeePerGas * web3_tx.gas
			tx.fee = fee / 10**18
			tx.feeUnit = "ETH"
		elif 'gasPrice' in web3_tx and not web3_tx.gasPrice is None:
			fee = web3_tx.gasPrice * web3_tx.gas
			tx.fee = fee / 10**18
			tx.feeUnit = "ETH"

		from_addr = ccql_data.Address()
		from_addr.id = web3_tx['from']
		to_addr = ccql_data.Address()
		to_addr.id = web3_tx['to']

		#tx[ccql_data.TX_BLOCK_ID] = web3_tx.blockNumber
		#tx[ccql_data.TX_block_id] = web3_tx.blockHash

		tx_desc.from_.append(from_addr)
		tx_desc.to.append(to_addr)

		tx_desc.value = web3_tx.value / 10**18
		tx_desc.data = web3_tx.input

		tx.descriptor.append(tx_desc)

		return tx


	def get_transactions(self, transaction_id_list):
		transactions = []
		for transaction_id in transaction_id_list:
			transactions.append(self.get_transaction(transaction_id))
		return transactions


	def get_account(self, account_id):

		if not isinstance(account_id, str):
			print("Error: account descriptor is not a string")
			sys.exit()
		
		# construct block desciptor for web3
		account_id_web3 = account_id
		if (account_id == "0x0"):
			account_id_web3 = '0xa'
		else:
			account_id_web3 = self.w3.toChecksumAddress(account_id)

		ac = ccql_data.Account()
		ac_desc = ccql_data.AccountDescriptor()

		ac.id = account_id

		# Ethereum supports the "Ether/ETH" asset only
		as_eth = ccql_data.Asset()
		as_type = ccql_data.AssetType()

		as_type.id = 1
		as_type.typeName = "Ether"
		as_type.unit = "ETH"

		as_eth.id = 1
		as_eth.assetType = as_type

		# Balance returned in 10^⁻18 Eth (Wei)
		web3_balance = self.w3.eth.getBalance(account_id_web3)
		as_eth.balance = web3_balance * pow(10, -18)

		ac.accountDescriptor = ac_desc
		ac.assets.append(as_eth)

		return ac


	def get_accounts(self, account_id_list):
		accounts = []
		for account_id in account_id_list:
			accounts.append(self.get_account(account_id))
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


class Cardano_Node(CCQL_Node):

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
		status = ccql_data.Status()
		validationDesc = ccql_data.ValidationDescriptor()

		block.id = web3_block.hash.hex()
		block.validationDescriptor = validationDesc
		block.validationDescriptor.proposer = []
		block.validationDescriptor.creator = []
		block.validationDescriptor.attestations = []
		
		block_desc.height = web3_block.number
		block_desc.timestamp = web3_block.timestamp
		block_desc.status = status
		block.descriptor = block_desc

		block.linkedBlockDescriptor = linked_block_desc

		accounts = {}

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
				tx.feeUnit = "ETH"
			elif 'gasPrice' in web3_tx and not web3_tx.gasPrice is None:
				fee = web3_tx.gasPrice * web3_tx.gas
				tx.fee = fee / 10**18
				tx.feeUnit = "ETH"

			from_addr = ccql_data.Address()
			from_addr.id = web3_tx['from']
			to_addr = ccql_data.Address()
			to_addr.id = web3_tx['to']

			accounts[from_addr.id] = from_addr
			accounts[to_addr.id] = to_addr

			tx_desc.from_.append(from_addr)
			tx_desc.to.append(to_addr)

			tx_desc.value = web3_tx.value / 10**18
			tx_desc.data = web3_tx.input

			tx.descriptor.append(tx_desc)
			block.transactions.append(tx)
			
			#ccql_data.print_obj(tx)
			#ccql_data.print_obj(tx_desc)
			#print(tx)
			#print(tx_desc)

			i += 1
			if i >= limit:
				break

		for a in accounts.keys():
			block.accounts.append(accounts[a])

		return block


	def get_blocks(self, block_id_list):
		blocks = []
		for block_id in block_id_list:
			blocks.append(self.get_block(block_id))
		return blocks


	def get_transaction(self, transaction_id):

		if not isinstance(transaction_id, str):
			print("Error: transaction descriptor is not a string")
			sys.exit()
		
		# construct block desciptor for web3
		transaction_id_web3 = transaction_id
		if (transaction_id == "0x0"):
			transaction_id_web3 = '0xa'

		web3_tx = self.w3.eth.getTransaction(transaction_id_web3)
		
		tx = ccql_data.Transaction()
		tx_desc = ccql_data.TransactionDescriptor()

		tx.id = web3_tx.hash.hex()
		
		# Ethereum gas after London hardfork: maxFeePerGas, maxPriorityFeePerGas
		# Ethereum gas before London hardfork: gas, gasPrice
		if 'maxFeePerGas' in web3_tx and not web3_tx.maxFeePerGas is None:
			baseFeePerGas = web3_tx.maxFeePerGas - web3_tx.maxPriorityFeePerGas
			fee = baseFeePerGas * web3_tx.gas
			tx.fee = fee / 10**18
			tx.feeUnit = "ETH"
		elif 'gasPrice' in web3_tx and not web3_tx.gasPrice is None:
			fee = web3_tx.gasPrice * web3_tx.gas
			tx.fee = fee / 10**18
			tx.feeUnit = "ETH"

		from_addr = ccql_data.Address()
		from_addr.id = web3_tx['from']
		to_addr = ccql_data.Address()
		to_addr.id = web3_tx['to']

		#tx[ccql_data.TX_BLOCK_ID] = web3_tx.blockNumber
		#tx[ccql_data.TX_block_id] = web3_tx.blockHash

		tx_desc.from_.append(from_addr)
		tx_desc.to.append(to_addr)

		tx_desc.value = web3_tx.value / 10**18
		tx_desc.data = web3_tx.input

		tx.descriptor.append(tx_desc)

		return tx


	def get_transactions(self, transaction_id_list):
		transactions = []
		for transaction_id in transaction_id_list:
			transactions.append(self.get_transaction(transaction_id))
		return transactions


	def get_account(self, account_id):

		if not isinstance(account_id, str):
			print("Error: account descriptor is not a string")
			sys.exit()
		
		# construct block desciptor for web3
		account_id_web3 = account_id
		if account_id == "0x0":
			account_id_web3 = '0xa'
		else:
			account_id_web3 = self.w3.toChecksumAddress(account_id)

		ac = ccql_data.Account()
		ac_desc = ccql_data.AccountDescriptor()

		ac.id = account_id

		# Ethereum supports the "Ether/ETH" asset only
		as_eth = ccql_data.Asset()
		as_type = ccql_data.AssetType()

		as_type.id = 1
		as_type.typeName = "Ether"
		as_type.unit = "ETH"

		as_eth.id = 1
		as_eth.assetType = as_type

		# Balance returned in 10^⁻18 Eth (Wei)
		web3_balance = self.w3.eth.getBalance(account_id_web3)
		as_eth.balance = web3_balance * pow(10, -18)

		ac.accountDescriptor = ac_desc
		ac.assets.append(as_eth)

		return ac


	def get_accounts(self, account_id_list):
		accounts = []
		for account_id in account_id_list:
			accounts.append(self.get_account(account_id))
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

class Bitcoin_Node(CCQL_Node):

	# Node Web Socket Connection
	#WEB3_ADDRESS = "ws://51.154.78.219:46804"
	WEB3_ADDRESS = "https://api.mainnet-beta.solana.com"

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

		#self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
		
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
		status = ccql_data.Status()
		validationDesc = ccql_data.ValidationDescriptor()

		block.id = web3_block.hash.hex()
		block.validationDescriptor = validationDesc
		block.validationDescriptor.proposer = []
		block.validationDescriptor.creator = []
		block.validationDescriptor.attestations = []
		
		block_desc.height = web3_block.number
		block_desc.timestamp = web3_block.timestamp
		block_desc.status = status
		block.descriptor = block_desc

		block.linkedBlockDescriptor = linked_block_desc

		accounts = {}

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
				tx.feeUnit = "ETH"
			elif 'gasPrice' in web3_tx and not web3_tx.gasPrice is None:
				fee = web3_tx.gasPrice * web3_tx.gas
				tx.fee = fee / 10**18
				tx.feeUnit = "ETH"

			from_addr = ccql_data.Address()
			from_addr.id = web3_tx['from']
			to_addr = ccql_data.Address()
			to_addr.id = web3_tx['to']

			accounts[from_addr.id] = from_addr
			accounts[to_addr.id] = to_addr

			tx_desc.from_.append(from_addr)
			tx_desc.to.append(to_addr)

			tx_desc.value = web3_tx.value / 10**18
			tx_desc.data = web3_tx.input

			tx.descriptor.append(tx_desc)
			block.transactions.append(tx)
			
			#ccql_data.print_obj(tx)
			#ccql_data.print_obj(tx_desc)
			#print(tx)
			#print(tx_desc)

			i += 1
			if i >= limit:
				break

		for a in accounts.keys():
			block.accounts.append(accounts[a])

		return block


	def get_blocks(self, block_id_list):
		blocks = []
		for block_id in block_id_list:
			blocks.append(self.get_block(block_id))
		return blocks


	def get_transaction(self, transaction_id):

		if not isinstance(transaction_id, str):
			print("Error: transaction descriptor is not a string")
			sys.exit()
		
		# construct block desciptor for web3
		transaction_id_web3 = transaction_id
		if (transaction_id == "0x0"):
			transaction_id_web3 = '0xa'

		web3_tx = self.w3.eth.getTransaction(transaction_id_web3)
		
		tx = ccql_data.Transaction()
		tx_desc = ccql_data.TransactionDescriptor()

		tx.id = web3_tx.hash.hex()
		
		# Ethereum gas after London hardfork: maxFeePerGas, maxPriorityFeePerGas
		# Ethereum gas before London hardfork: gas, gasPrice
		if 'maxFeePerGas' in web3_tx and not web3_tx.maxFeePerGas is None:
			baseFeePerGas = web3_tx.maxFeePerGas - web3_tx.maxPriorityFeePerGas
			fee = baseFeePerGas * web3_tx.gas
			tx.fee = fee / 10**18
			tx.feeUnit = "ETH"
		elif 'gasPrice' in web3_tx and not web3_tx.gasPrice is None:
			fee = web3_tx.gasPrice * web3_tx.gas
			tx.fee = fee / 10**18
			tx.feeUnit = "ETH"

		from_addr = ccql_data.Address()
		from_addr.id = web3_tx['from']
		to_addr = ccql_data.Address()
		to_addr.id = web3_tx['to']

		#tx[ccql_data.TX_BLOCK_ID] = web3_tx.blockNumber
		#tx[ccql_data.TX_block_id] = web3_tx.blockHash

		tx_desc.from_.append(from_addr)
		tx_desc.to.append(to_addr)

		tx_desc.value = web3_tx.value / 10**18
		tx_desc.data = web3_tx.input

		tx.descriptor.append(tx_desc)

		return tx


	def get_transactions(self, transaction_id_list):
		transactions = []
		for transaction_id in transaction_id_list:
			transactions.append(self.get_transaction(transaction_id))
		return transactions


	def get_account(self, account_id):

		if not isinstance(account_id, str):
			print("Error: account descriptor is not a string")
			sys.exit()
		
		# construct block desciptor for web3
		account_id_web3 = account_id
		if (account_id == "0x0"):
			account_id_web3 = '0xa'
		else:
			account_id_web3 = self.w3.toChecksumAddress(account_id)

		ac = ccql_data.Account()
		ac_desc = ccql_data.AccountDescriptor()

		ac.id = account_id

		# Ethereum supports the "Ether/ETH" asset only
		as_eth = ccql_data.Asset()
		as_type = ccql_data.AssetType()

		as_type.id = 1
		as_type.typeName = "Ether"
		as_type.unit = "ETH"

		as_eth.id = 1
		as_eth.assetType = as_type

		# Balance returned in 10^⁻18 Eth (Wei)
		web3_balance = self.w3.eth.getBalance(account_id_web3)
		as_eth.balance = web3_balance * pow(10, -18)

		ac.accountDescriptor = ac_desc
		ac.assets.append(as_eth)

		return ac


	def get_accounts(self, account_id_list):
		accounts = []
		for account_id in account_id_list:
			accounts.append(self.get_account(account_id))
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
		status = ccql_data.Status()
		validationDesc = ccql_data.ValidationDescriptor()

		block.id = web3_block.hash.hex()
		block.validationDescriptor = validationDesc
		block.validationDescriptor.proposer = []
		block.validationDescriptor.creator = []
		block.validationDescriptor.attestations = []
		
		block_desc.height = web3_block.number
		block_desc.timestamp = web3_block.timestamp
		block_desc.status = status
		block.descriptor = block_desc

		block.linkedBlockDescriptor = linked_block_desc

		accounts = {}

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
				tx.feeUnit = "ETH"
			elif 'gasPrice' in web3_tx and not web3_tx.gasPrice is None:
				fee = web3_tx.gasPrice * web3_tx.gas
				tx.fee = fee / 10**18
				tx.feeUnit = "ETH"

			from_addr = ccql_data.Address()
			from_addr.id = web3_tx['from']
			to_addr = ccql_data.Address()
			to_addr.id = web3_tx['to']

			accounts[from_addr.id] = from_addr
			accounts[to_addr.id] = to_addr

			tx_desc.from_.append(from_addr)
			tx_desc.to.append(to_addr)

			tx_desc.value = web3_tx.value / 10**18
			tx_desc.unit = "ETH"
			tx_desc.data = web3_tx.input

			tx.descriptor.append(tx_desc)
			block.transactions.append(tx)
			
			#ccql_data.print_obj(tx)
			#ccql_data.print_obj(tx_desc)
			#print(tx)
			#print(tx_desc)

			i += 1
			if i >= limit:
				break

		for a in accounts.keys():
			block.accounts.append(accounts[a])

		return block


	def get_blocks(self, block_id_list):
		blocks = []
		for block_id in block_id_list:
			blocks.append(self.get_block(block_id))
		return blocks


	def get_transaction(self, transaction_id):

		if not isinstance(transaction_id, str):
			print("Error: transaction descriptor is not a string")
			sys.exit()
		
		# construct block desciptor for web3
		transaction_id_web3 = transaction_id
		if (transaction_id == "0x0"):
			transaction_id_web3 = '0xa'

		web3_tx = self.w3.eth.getTransaction(transaction_id_web3)
		
		tx = ccql_data.Transaction()
		tx_desc = ccql_data.TransactionDescriptor()

		tx.id = web3_tx.hash.hex()
		
		# Ethereum gas after London hardfork: maxFeePerGas, maxPriorityFeePerGas
		# Ethereum gas before London hardfork: gas, gasPrice
		if 'maxFeePerGas' in web3_tx and not web3_tx.maxFeePerGas is None:
			baseFeePerGas = web3_tx.maxFeePerGas - web3_tx.maxPriorityFeePerGas
			fee = baseFeePerGas * web3_tx.gas
			tx.fee = fee / 10**18
			tx.feeUnit = "ETH"
		elif 'gasPrice' in web3_tx and not web3_tx.gasPrice is None:
			fee = web3_tx.gasPrice * web3_tx.gas
			tx.fee = fee / 10**18
			tx.feeUnit = "ETH"

		from_addr = ccql_data.Address()
		from_addr.id = web3_tx['from']
		to_addr = ccql_data.Address()
		to_addr.id = web3_tx['to']

		#tx[ccql_data.TX_BLOCK_ID] = web3_tx.blockNumber
		#tx[ccql_data.TX_block_id] = web3_tx.blockHash

		tx_desc.from_.append(from_addr)
		tx_desc.to.append(to_addr)

		tx_desc.value = web3_tx.value / 10**18
		tx_desc.unit = "ETH"
		tx_desc.data = web3_tx.input

		tx.descriptor.append(tx_desc)

		return tx


	def get_transactions(self, transaction_id_list):
		transactions = []
		for transaction_id in transaction_id_list:
			transactions.append(self.get_transaction(transaction_id))
		return transactions


	def get_account(self, account_id):

		if not isinstance(account_id, str):
			print("Error: account descriptor is not a string")
			sys.exit()
		
		# construct block desciptor for web3
		account_id_web3 = account_id
		if (account_id == "0x0"):
			account_id_web3 = '0xa'
		else:
			account_id_web3 = self.w3.toChecksumAddress(account_id)

		ac = ccql_data.Account()
		ac_desc = ccql_data.AccountDescriptor()

		ac.id = account_id

		# Ethereum supports the "Ether/ETH" asset only
		as_eth = ccql_data.Asset()
		as_type = ccql_data.AssetType()

		as_type.id = 1
		as_type.typeName = "Ether"
		as_type.unit = "ETH"

		as_eth.id = 1
		as_eth.assetType = as_type

		# Balance returned in 10^⁻18 Eth (Wei)
		web3_balance = self.w3.eth.getBalance(account_id_web3)
		as_eth.balance = web3_balance * pow(10, -18)

		ac.accountDescriptor = ac_desc
		ac.assets.append(as_eth)

		return ac


	def get_accounts(self, account_id_list):
		accounts = []
		for account_id in account_id_list:
			accounts.append(self.get_account(account_id))
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

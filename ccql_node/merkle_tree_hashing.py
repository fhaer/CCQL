import sys
import hashlib

def calculate_sha256_f(file):
	sha256 = hashlib.sha256()
	with open(file, 'rb') as f:
		while True:
			data = f.read(65536)
			if not data:
				break
			sha256.update(data)
	print("sha256(file(", file, ")) = 0x", bytes.hex(sha256.digest()), sep="")
	return sha256.digest()

def calculate_sha256_b(data):
	sha256 = hashlib.sha256()
	sha256.update(data)
	print("sha256(", "bytes(0x" + bytes.hex(data[0:4]) + "..." + bytes.hex(data[-4:]), ")) = 0x", bytes.hex(sha256.digest()), sep="")
	return sha256.digest()

def calculate_merkle_root(files):
	sha256 = hashlib.sha256()
	pairs = []
	print("\nCalculating hash values for all files ...\n")
	files.sort()
	for f in files:
		pairs.append(calculate_sha256_f(f))
	print("\nCalculating Merkle root ...\n")
	leafs = []
	while (len(leafs) > 0 or len(pairs) > 1):
		leaf_a = None
		leaf_b = None
		if len(leafs) > 1:
			# hash first two leafs
			leaf_a = leafs.pop()
			leaf_b = leafs.pop()
			sha256 = calculate_sha256_b(leaf_a + leaf_b)
			pairs.append(sha256)
		elif len(leafs) == 1:
			# hash first leaf and sha256(0)
			leaf_a = leafs.pop()
			leaf_b = bytes.fromhex('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
			sha256 = calculate_sha256_b(leaf_a + leaf_b)
			pairs.append(sha256)
		else:
			leafs = pairs.copy()
			pairs = []
			print()

	if len(pairs) > 0:
		print("\nMerkle root: 0x", bytes.hex(pairs[0]), sep="", end="\n\n")
		return pairs[0]
	print("Error: merkle root calculation failed")
	sys.exit()

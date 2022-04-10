import base58
import re

def encode_str_bytes32(data):
    if data.startswith("0x"):
        data_bytes = bytes.fromhex(data[2:]) # + bytearray(b'\x01')
        return data_bytes
    return str(data).encode(encoding='iso-8859-1', errors='ignore')

def decode_str_bytes32(data):
    #if data[0] == b'\x01':
    #    return binascii.hexlify(data[2:])
    st = data.decode(encoding='iso-8859-1', errors='ignore')
    return st.rstrip('\x00')

def encode_str_list_bytes32(ls):
    bytes32_ls = []
    for l in ls:
        bytes32_ls.append(encode_str_bytes32(l))
    return bytes32_ls

def encode_binary_bytes32(data):
    if isinstance(data, str) and data.startswith("0x"):
        data_bytes = bytes.fromhex(data[2:])
        return data_bytes
    elif isinstance(data, str):
        return bytes.fromhex(data)
    return data

def decode_binary_bytes32(data):
    return "0x" + bytes.hex(data[0:])

def encode_cid_bytes32(cid):
    cid_bytes = base58.b58decode(cid)
    hash_value = cid_bytes[2:]
    return "0x" + hash_value.hex()

def decode_cid_bytes32(data):
    # add multihash prefix for IPFS CIDs
    hex_str = "1220" + data.hex()
    cid_bytes = bytes.fromhex(hex_str)
    return base58.b58encode(cid_bytes).decode("iso-8859-15")

def construct_uri(sh, auth, path):
	uri = sh + ":"
	if len(auth) > 0:
		uri += "//" + auth
	if len(path) > 0:
		uri += path
	return uri

def parse_uri(address):
	scheme = ""
	authority = ""
	path = ""
	uri_match = re.search("^(.+?):(.+)$", address)
	if uri_match:
		scheme = uri_match.group(1)
		authority_path = uri_match.group(2)
		authority_match = re.search("^//(.+?)(/.+)?$", uri_match.group(2))
		if authority_match:
			if authority_match.group(1) and authority_match.group(2):
				authority = authority_match.group(1)
				path = authority_match.group(2)
			else:
				authority = ""
				path = authority_match.group(1)
		else:
			authority = ""
			path = authority_path
	return (scheme, authority, path)
    
def get_mime_type(files):
	if files[0].endswith(".xml"):
		mime_type = "text/xml"
	for f in files:
		if mime_type == "text/xml" and not f.endswith(".xml"):
			mime_type == ""
	return mime_type

def split_path(path, n):
	if len(path) == 0:
		return [""]
	if path.startswith("0x"):
		return [path]
	c = len(path) // n
	if len(path)%n != 0:
		c += 1
	parts = []
	for i in range(0, c):
		s = i*n
		e = s+n
		if e > len(path):
			e = len(path)
		parts.append(path[s:e])
	return parts

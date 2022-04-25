from encodings import normalize_encoding
from os import stat
import sys
import getopt
import re
import math
import uuid
from unittest import result

import ccql_node_connector
import ccql_identity_provider

from ccql_node import ccql_data

CCQL_VERSION = "CCQL test environment v0.1"
R_MAX = "r_max"

def print_usage():
    print("Usage: ccql.py [-h|--help] <query_statement>")
    print("")
    print("CCQL Test environment.")
    print("")
    print("")
    print("Query Statement:")
    print("")
    print("<query_statement> = ")
    print("  Q <query_attribut_spec>(, <query_attribut_spec>)*  ")
    print("  S <source_spec>(, <source_spec>)*  ")
    print("  [F <filter_spec>(, <filter_spec>)*];")
    print("")
    print("")
    print("For details, refer to the read-me file and the ccql.ebnf grammar specification.")
    print("")
    sys.exit()


def process_query(query_statement):

    query_attribute_clause = []
    source_clause = []
    filter_clause = []
    result_map = {}

    clause_selector = ""

    # query statement per definition from the data model, see module ccql_data
    for token in query_statement:

        if token in ccql_data.Q_CLAUSES:
            clause_selector = token

        elif clause_selector == ccql_data.Q:
            query_attr_spec = parse_query_clause(token)
            query_attribute_clause.append(query_attr_spec)

        elif clause_selector == ccql_data.S:
            source_spec = parse_source_clause(token)
            source_clause.append(source_spec)

        elif clause_selector == ccql_data.F:
            filter_spec = parse_filter_clause(token)
            filter_clause.append(filter_spec)

        else:
            print("Format error in:", clause_selector, "clause")
            print("Statement token:", token)
            sys.exit()

    i = 0
    if len(query_attribute_clause) > 0:
        for source_spec in source_clause:
            i += 1
            process_query_for_source(source_spec, i, query_attribute_clause, result_map)

    output_query_result(query_attribute_clause, i, result_map, filter_clause)


def parse_query_clause(input):

    statement = input.strip().rstrip(',').strip()
    query_attr_spec = statement.split('.')
    
    if len(query_attr_spec) != 2:
        print("Error: format error in query clause, not using syntax <class>.<attribute>")
        sys.exit()
    elif not query_attr_spec[0] in ccql_data.CCQL_CLASSES:
        print("Error: format error in query clause, <class> not in", ccql_data.CCQL_CLASSES)
        sys.exit()

    if not isinstance(statement, str):
        print("Error: non-string value in query clause")
        sys.exit()

    return query_attr_spec


def parse_source_clause(input):

    statement = input.strip().rstrip(',').strip()
    source_attr_spec = statement.split(':')

    #if len(source_attr_spec) != 3 or len(source_attr_spec) != 4:
    #    print("Error: format error in source clause, not starting with <blockchain_instance>:<network_instance>:<chain_descriptor_instance>", source_attr_spec)
    #    sys.exit()
    if len(source_attr_spec) < 3 or len(source_attr_spec) > 4:
        print("Error: format error in source clause, not using syntax <blockchain_instance>:<network_instance>:<chain_descriptor_instance>", "\n")
        print("Data model <blockchain_instance>:<network_instance>:<chain_descriptor_instance> =", ccql_data.get_chain_instance_list())
        sys.exit()
    elif len(source_attr_spec) == 4:
        optional_source_spec = source_attr_spec[3].split(".")
        if len(optional_source_spec) != 2 or not optional_source_spec[0] in ccql_data.SOURCE_SPEC_OPTIONAL:
            print("Error: format error in source clause, not using syntax <blockchain_instance>:<network_instance>:<chain_descriptor_instance>:[<source>.<block_instance>|<source>.<transaction_instance>|<source>.<account_instance>] with <source> not in", ccql_data.SOURCE_SPEC_OPTIONAL, "\n")
            print("Data model <blockchain_instance>:<network_instance>:<chain_descriptor_instance> =", ccql_data.get_chain_instance_list())
            sys.exit()
        
    if not isinstance(statement, str):
        print("Error: non-string value in source clause")
        sys.exit()

    blockchain_inst = parse_attribute(source_attr_spec[0])
    network_inst = parse_attribute(source_attr_spec[1])
    chain_desc_inst = parse_attribute(source_attr_spec[2])
    optional_source_class = ""
    optional_source_inst = ""

    if len(source_attr_spec) == 4:
        optional_source_class = parse_class(source_attr_spec[3])
        optional_source_inst = parse_attribute(source_attr_spec[3])
    
    return (blockchain_inst, network_inst, chain_desc_inst, optional_source_class, optional_source_inst)


def parse_filter_clause(input):

    statement = input.strip().rstrip(',').strip()

    filter_syntax = '(\S+)\.(\S+)\s*(=|<>|<|>|<=|>=)\s*(\S+)'
    filter_spec = re.findall(filter_syntax, statement)
    
    if len(filter_spec) != 1 or len(filter_spec[0]) != 4:
        print("Error: format error in filter clause, not syntax <class>.<attribute> <operator> <value> with <operator> not in (=|<>|<|>|<=|>=)")
        sys.exit()

    if not isinstance(statement, str):
        print("Error: non-string value in filter clause")
        sys.exit()
    
    filter_class = filter_spec[0][0]
    filter_attr = filter_spec[0][1]
    filter_operator = filter_spec[0][2]
    filter_value = filter_spec[0][3]
    
    if not filter_class in ccql_data.CCQL_CLASSES:
        print("Error: format error in filter clause, not starting with syntax <class>.<attribute> or <class> not in", ccql_data.CCQL_CLASSES)
        sys.exit()

    return (filter_class, filter_attr, filter_operator, filter_value)


def process_query_for_source(source_spec, i, query_attribute_clause, result_map):

    # source specification
    blockchain_inst = source_spec[0]
    network_inst = source_spec[1]
    chain_desc_inst = source_spec[2]
    optional_source_class = source_spec[3]
    optional_source_inst = source_spec[4]

    node_connector = ccql_node_connector.CCQL_Node_Connector(blockchain_inst, network_inst, chain_desc_inst)
    identity_acc = ccql_identity_provider.CCQL_Identity_Provider()
    
    # optional source specifications: blocks, transactions, accounts, assets, tokens, data
    if len(optional_source_class) > 0:
        if optional_source_class == ccql_data.BLOCK or optional_source_class == ccql_data.BLOCK_S:
            (block, block_desc, status, linked_block_desc, validation_desc, val_desc_proposer, val_desc_creator, val_desc_att, tx, acc) = node_connector.get_block(optional_source_inst)
            map_query_result(query_attribute_clause, i, ccql_data.BLOCK, ccql_data.BLOCK_S, block, result_map)
            map_query_result(query_attribute_clause, i, ccql_data.BLOCK_DESC, None, block_desc, result_map)
            map_query_result(query_attribute_clause, i, ccql_data.BLOCK_STATUS, None, status, result_map)
            map_query_result(query_attribute_clause, i, ccql_data.BLOCK_DESC_LINKED, None, linked_block_desc, result_map)
            map_query_result(query_attribute_clause, i, ccql_data.BLOCK_VALIDATION_DESC, None, validation_desc, result_map)
            map_query_result(query_attribute_clause, i, ccql_data.BLOCK_VALIDATOR_PROPOSER, None, val_desc_proposer, result_map)
            map_query_result(query_attribute_clause, i, ccql_data.BLOCK_VALIDATOR_CREATOR, None, val_desc_creator, result_map)
            map_query_result(query_attribute_clause, i, ccql_data.BLOCK_VALIDATOR_ATTESTER, None, val_desc_att, result_map)
            map_query_result(query_attribute_clause, i, ccql_data.TRANSACTION, ccql_data.TRANSACTION_S, tx, result_map)
            map_query_result(query_attribute_clause, i, ccql_data.ACCOUNT, ccql_data.ACCOUNT_S, acc, result_map)
        elif optional_source_class == ccql_data.ACCOUNT or optional_source_class == ccql_data.ACCOUNT_S:
            (account, accountDesc, asset, assetType, token, tokenType, data, storageType) = node_connector.get_account(optional_source_inst)
            map_query_result(query_attribute_clause, i, ccql_data.ACCOUNT, ccql_data.ACCOUNT_S, account, result_map)
            map_query_result(query_attribute_clause, i, ccql_data.ACCOUNT_DESC, None, accountDesc, result_map)
            map_query_result(query_attribute_clause, i, ccql_data.ACCOUNT_ASSET, ccql_data.ACCOUNT_ASSET_S, asset, result_map)
            map_query_result(query_attribute_clause, i, ccql_data.ACCOUNT_ASSET_TYPE, None, assetType, result_map)
            map_query_result(query_attribute_clause, i, ccql_data.ACCOUNT_TOKEN, ccql_data.ACCOUNT_TOKEN_S, token, result_map)
            map_query_result(query_attribute_clause, i, ccql_data.ACCOUNT_TOKEN_TYPE, None, tokenType, result_map)
            map_query_result(query_attribute_clause, i, ccql_data.ACCOUNT_DATA, ccql_data.ACCOUNT_DATA_S, data, result_map)
            map_query_result(query_attribute_clause, i, ccql_data.ACCOUNT_STORAGE_TYPE, None, storageType, result_map)
        elif optional_source_class == ccql_data.TRANSACTION or optional_source_class == ccql_data.TRANSACTION_S:
            (tx, txDesc, utxo) = node_connector.get_transaction(optional_source_inst)
            map_query_result(query_attribute_clause, i, ccql_data.TRANSACTION, ccql_data.TRANSACTION_S, tx, result_map)
            map_query_result(query_attribute_clause, i, ccql_data.TRANSACTION_DESC, None, txDesc, result_map)
            map_query_result(query_attribute_clause, i, ccql_data.UTXO, None, utxo, result_map)
        else:
            print("Unknown optional source class:", optional_source_class)
            sys.exit()
    

def parse_class_attribute(statement):
    class_attr = statement.split('.')
    return (class_attr[0], class_attr[-1])
    
def parse_class(statement):
    class_attr = statement.split('.')
    return class_attr[0]
    
def parse_attribute(statement):
    class_attr = statement.split('.')
    return class_attr[-1]
    

def map_query_result(query_attribute_clause, i, source_type, source_type_short, result, result_map):

    result_map_key = str(i) + ":" + str(source_type)

    if not source_type in result_map.keys():
        result_map[result_map_key] = {}

    for r in result:
        if not 'id' in dir(r):
            r.id = str(uuid.uuid4())
        result_map[result_map_key][r.id] = r

    for i in range(0, len(query_attribute_clause)):
        cl = query_attribute_clause[i][0]
        if cl == source_type_short:
            query_attribute_clause[i][0] = source_type

def map_query_result_last(query_attribute_clause, source_type, result, result_map):

    if not source_type in result_map.keys():
        result_map[source_type] = {}
    if not R_MAX in result_map[source_type].keys():
        result_map[source_type][R_MAX] = 1
    
    query_attributes = get_query_attributes(query_attribute_clause, source_type)
    if isinstance(query_attributes, list):
        for q_att in query_attributes:
            key = source_type + "." + q_att
            append_result(result_map, source_type, key, "")
            for r in result:
                if isinstance(r[q_att], list):
                    for rv in r[q_att]:
                        #result_map[q_att].append(str(rv))
                        append_result(result_map, source_type, key, str(rv))
                else:
                    #result_map[q_att].append(str(r[q_att]))
                    append_result(result_map, source_type, key, str(r[q_att]))
            if len(result_map[source_type][key]) > result_map[source_type][R_MAX]:
                result_map[source_type][R_MAX] = len(result_map[source_type][key])
                #r_max = len(result_map[q_att])
    else:
        result_map[query_attributes].append(str(result))


def append_result(result_map, source_type, key, result_value):

    if key in result_map[source_type].keys():
        # append
        result_map[source_type][key].append(str(result_value))
    else:
        # initialize
        if (len(str(result_value)) > 0):
            result_map[source_type][key] = [str(result_value)]
        else:
            result_map[source_type][key] = []

def output_query_result(query_attribute_clause, i, result_map, filter_clause):

    print()
    print("Query results:\n")
    output_query_result_by_attribute(query_attribute_clause, i, result_map, filter_clause)
    print()
    #print("DEBUG: Raw result data")
    #print(result_map)

    
def output_query_result_by_attribute(query_attribute_clause, i, result_map, filter_clause):

    types_output = ""
    types_output = append_query_result_types(i, result_map, types_output, query_attribute_clause)
    print(types_output)
    (n_rows, rows_output) = append_query_result_values(i, result_map, query_attribute_clause, filter_clause)
    for row in rows_output:
        print(row)

    print("\nNumber of rows:", n_rows)


def append_query_result_types(i, result_map, types_output, query_attribute_clause):

    for source_id in range(1, i+1):
        for qa in query_attribute_clause:
            qa_class = qa[0]
            qa_attr = qa[-1]
            types_output += str(source_id) + ":" + qa_class + "." + qa_attr + "|"

    return types_output

def append_query_result_types_l(result_map, source_type, types_output):
    for att_type in result_map[source_type].keys():
        if att_type == R_MAX:
            continue
        types_output += att_type + "|"
    return types_output

def append_query_result_value(output, value, n_rows_remaining):
    if isinstance(value, list):
        if len(value) > 0:
            n_rows_remaining = int(n_rows_remaining / len(value))
        for val in value:
            for i in range(0, n_rows_remaining):
                if hasattr(val, "id"):
                    output[-1].append(val.id)
                else:
                    output[-1].append(str(val))
    else:
        for i in range(0, n_rows_remaining):
            if hasattr(value, "id"):
                output[-1].append(value.id)
            else:
                output[-1].append(str(value))

def apply_filter(cls, attr, val, filter_clause):
    if len(filter_clause) < 1:
        return True
    if cls == filter_clause[0][0] and attr == filter_clause[0][1]:
        if val == filter_clause[0][3]:
            return True
        else:
            return True
    else:
        return True


def append_query_result_values(i, result_map, query_attribute_clause, filter_clause):

    n_rows = 1
    for source_id in range(1, i+1):
        for q in query_attribute_clause:
            query_attr_spec = get_query_attributes(q)
            source_type = query_attr_spec[0]
            attr = query_attr_spec[-1]

            q_rows = 0

            source_key = str(source_id) + ":" + source_type

            if not source_key in result_map.keys():
                print("\nAbort:", source_key, "could not be constructed from the given source clause\n")
                sys.exit()

            for r in result_map[source_key].values():
                val = getattr(r, attr)
                if apply_filter(source_type, attr, val, filter_clause):
                    if isinstance(val, list):
                        q_rows += len(val)
                    else:
                        q_rows += 1

            n_rows *= q_rows

    n_rows_remaining = n_rows
    output_columns = []
    
    for source_id in range(1, i+1):
        for q in query_attribute_clause:
            query_attr_spec = get_query_attributes(q)
            source_type = query_attr_spec[0]
            attr = query_attr_spec[-1]

            source_key = str(source_id) + ":" + source_type
            output_columns.append([])

            for r in result_map[source_key].values():
                val = getattr(r, attr)
                if apply_filter(source_type, attr, val, filter_clause):
                    append_query_result_value(output_columns, val, n_rows_remaining)
    
    n_columns = len(output_columns)

    rows_output = []
    for i in range(0, n_rows):
        values_output = ""
        for j in range(0, n_columns):
            values_output += output_columns[j][i] + "|"
        rows_output.append(values_output)
    
    rows_output = list(dict.fromkeys(rows_output))

    return (len(rows_output), rows_output)


def cart_product_last(relations, attributes):
    
    for r in relations:

        n_rows = 1

        for a in attributes:
            if a in r.keys() and isinstance(r[a], list):
                n_rows *= len(r[a])

        rep_rows = n_rows
        output_columns = []

        for a in attributes:
            if not a in r.keys():
                print("Attribute not found:", a)
                continue
            output_columns.append([])
            if isinstance(r[a], list):
                rep_rows = int(rep_rows / len(r[a]))
                for val in r[a]:
                    for i in range(0, rep_rows):
                        output_columns[-1].append(str(val))
            else:
                for i in range(0, rep_rows):
                    output_columns[-1].append(str(r[a]))
    
    return output_columns


def get_query_attributes(query_specification):
    if type(query_specification) is tuple or type(query_specification) is list:
        return query_specification
    query_attr_spec = query_specification.split(".")
    if not len(query_attr_spec) == 2:
        print("Error: format error in query clause")
        sys.exit(1)
    return query_attr_spec

def append_query_result_values_bck(result_map, source_type, values_output, query_attr_spec):
    
    for r in result_map[source_type].values():

        n_rows = 1

        for a in query_attr_spec:
            if a in r.keys() and isinstance(r[a], list):
                n_rows *= len(r[a])

        rep_rows = n_rows
        output_columns = []

        for a in query_attr_spec:
            if not a in r.keys():
                print("Attribute not found:", a)
                continue
            output_columns.append([])
            if isinstance(r[a], list):
                rep_rows = int(rep_rows / len(r[a]))
                for val in r[a]:
                    for i in range(0, rep_rows):
                        output_columns[-1].append(str(val))
            else:
                for i in range(0, rep_rows):
                    output_columns[-1].append(str(r[a]))
    
        n_columns = len(output_columns)

        for i in range(0, n_rows):
            for j in range(0, n_columns):
                values_output += output_columns[j][i] + "|"
            values_output += "\n"

    return values_output

def append_query_result_values_l(result_map, source_type, values_output):
    #for source_type in sorted(result_map.keys()):
    r_max = result_map[source_type][R_MAX]
    for i in range(0, r_max):
        for r in result_map[source_type].keys():
            value = ""
            if r == R_MAX:
                continue
            elif i < len(result_map[source_type][r]):
                value = result_map[source_type][r][i]
            elif len(result_map[source_type][r]) > 0:
                value = result_map[source_type][r][len(result_map[source_type][r])-1]
            else:
                value = " "
            #join_types = get_join_types(result_map, source_type)
            #for join_type in join_types:
            #    if value in join_types[join_type]:

            values_output += value + "|"
        values_output += "\n"
    return values_output


def parse_cli():

    try:
        opts, args = getopt.getopt(sys.argv[1:], "qh",
            ["query"])

    except getopt.GetoptError as err:
        print(err)
        print_usage()

    if len(opts) < 1 and len(args) > 0:
        # no options given, assuming query statement follows
        process_query(args)
    elif len(args) < 1:
        print_usage()

    for opt, arg in opts:
        if opt in ("-q", "--query"):
            process_query(args)
        elif opt in ("-h", "--help"):
            print_usage()
        else:
            print(CCQL_VERSION)

parse_cli()

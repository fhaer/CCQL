from encodings import normalize_encoding
from os import stat
import sys
import getopt
import re
import math
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

    #print("Query, Source, and Filter Specification:")
    #print("")
    #print("<query_attribut_spec> = { chain.<ch_attr> | block.<bl_attr> | account.<ac_attr> | tx.<tx_attr> }")
    #print("<ch_attr> = { id | descriptor }                                                -- chain attributes defined by the data model in ccql_data")
    #print("<bl_attr> = { id | descriptor | timestamp | transaction_ids }                  -- block attributes according to ccql_data")
    #print("<ac_attr> = { id | descriptor | balance }                                      -- account attributes according to ccql_data")
    #print("<tx_attr> = { id | descriptor | address_from | address_to | balance | data }   -- transaction attributes according to ccql_data")
    #print("")
    #print("Source descriptors are supported for blocks and accounts:")
    #print("<source_attr_spec> = { <chain_descriptor>.<block_descriptor> | <chain_descriptor>.<tx_descriptor> | <chain_descriptor>.<account_descriptor> }")
    #print("<chain_descriptor> = { eth }                                                   -- only eth (Ethereum) is supported at this point")
    #print("<block_descriptor> = { <id> | <descriptor> }                                   -- block by ID or descriptor, i.e. number or hash for eth")
    #print("<tx_descriptor> = { <id> }                                                     -- transaction with given ID, i.e. 0x<transaction_hash> for eth")
    #print("<account_descriptor> = { <id> }                                                -- account with ID, i.e. 0x<address> for eth")
    #print("")
    #print("Filter descriptors are supported for comparisons of transactions and accounts:")
    #print("<filter_descriptor> = { <transaction_filter> | <account_filter> } ")
    #print("<transaction_filter> = { <transaction_descriptor> = <transaction_descriptor> } -- only equals comparison at this point")
    #print("<account_filter> = { <account_descriptor> = <account_descriptor> }             -- only equals comparison at this point")
    #print("")
    #print("Example Queries")
    #print("Q account.id S eth.0x06012c8cf97BEaD5deAe237070F9587f8E7A266d")
    #print("Q account.id, account.balance S eth.0x06012c8cf97BEaD5deAe237070F9587f8E7A266d")
    #print("Q block.id, block.timestamp, block.transaction_ids S eth.4711111")
    #print("Q tx.id, tx.balance, tx.address_to, tx.address_from S eth.0x7bc23a1e155346033bf4c7e772bdc274c71215a7f4fe1607fc4e0ae24d2c0243")
    #print("")
    #print("Testing:")
    #print(" Q chain, block, tx.id, tx.address_to S eth.block.4711 F tx.address_to = 0xabc L 3")
    #print("  => query block 4711, query tx all tx, filter for address_to, max. 3")
    #print(" Q S eth.block, eth.acc F eth.tx. eth.acc.id")
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

    if len(query_attribute_clause) > 0:
        for source_spec in source_clause:
            process_query_for_source(source_spec, query_attribute_clause, result_map)
        # TODO filter_clause

    output_query_result(query_attribute_clause, result_map)


def parse_query_clause(input):

    statement = input.strip().rstrip(',').strip()
    query_attr_spec = statement.partition('.')

    if len(query_attr_spec) != 3:
        print("Error: format error in query clause, not using syntax <class>.<attribute>")
        sys.exit()
    elif query_attr_spec[1] != "." or not query_attr_spec[0] in ccql_data.CCQL_CLASSES:
        print("Error: format error in query clause, not using syntax <class>.<attribute> or <class> not in", ccql_data.CCQL_CLASSES)
        sys.exit()

    if not isinstance(statement, str):
        print("Error: non-string value in query clause")
        sys.exit()

    class_spec = query_attr_spec[0]
    attr_spec = query_attr_spec[2]

    return (class_spec, attr_spec)


def parse_source_clause(input):

    statement = input.strip().rstrip(',').strip()
    source_attr_spec = statement.partition(':')

    if len(source_attr_spec) != 5 or len(source_attr_spec) != 7:
        print("Error: format error in source clause, not starting with <blockchin_instance>:<network_instance>:<chain_descriptor_instance>")
        sys.exit()
    elif len(source_attr_spec) == 5 and (source_attr_spec[1] != ":" or source_attr_spec[3] != ":"):
        print("Error: format error in source clause, not using syntax <blockchin_instance>:<network_instance>:<chain_descriptor_instance>")
        sys.exit()
    elif len(source_attr_spec) == 7:
        optional_source_spec = source_attr_spec[6].partition(".")
        if source_attr_spec[1] != ":" or source_attr_spec[3] != ":" or source_attr_spec[5] != ":" \
            or len(optional_source_spec) != 3 or optional_source_spec[1] == "." or not optional_source_spec[0] in ccql_data.SOURCE_SPEC_OPTIONAL:
            print("Error: format error in source clause, not using syntax <blockchin_instance>:<network_instance>:<chain_descriptor_instance>:[<source>.<block_instance>|<source>.<transaction_instance>|<source>.<account_instance>] with <source> not in", ccql_data.SOURCE_SPEC_OPTIONAL)
            sys.exit()
        
    if not isinstance(statement, str):
        print("Error: non-string value in source clause")
        sys.exit()

    blockchain_inst = parse_attribute(source_attr_spec[0])
    network_inst = parse_attribute(source_attr_spec[2])
    chain_desc_inst = parse_attribute(source_attr_spec[4])
    optional_source_class = ""
    optional_source_inst = ""

    if len(source_attr_spec) == 7:
        optional_source_class = parse_class(source_attr_spec[6])
        optional_source_inst = parse_attribute(source_attr_spec[6])
    
    return (blockchain_inst, network_inst, chain_desc_inst, optional_source_class, optional_source_inst)


def parse_filter_clause(input):

    statement = input.strip().rstrip(',').strip()

    filter_syntax = 'r(\S+)\.(\S+)\s*(=|<>|<|>|<=|>=)\s*(\S+)'
    filter_spec = re.findall(filter_syntax, statement)

    if len(filter_spec) != 1 or len(filter_spec[0] != 4):
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


def process_query_for_source(source_spec, query_attribute_clause, result_map):

    node_connector = ccql_node_connector.CCQL_Node_Connector(source_spec[0], source_spec[1], source_spec[2])

    identity_acc = ccql_identity_provider.CCQL_Identity_Provider()
    
    if source_attr_spec[-1].startswith("0x") and len(source_attr_spec[-1]) <= 42:
        account_descriptor = source_attr_spec[-1]
        account = node_connector.get_account(chain_descriptor, account_descriptor, query_attribute_clause)
        process_query_result(query_attribute_clause, ccql_data.AC, account, result_map)
    elif source_attr_spec[-1].startswith("0x") and len(source_attr_spec[-1]) > 42:
        tx = source_attr_spec[-1]
        tx = node_connector.get_transaction(chain_descriptor, tx, query_attribute_clause)
        process_query_result(query_attribute_clause, ccql_data.TX, tx, result_map)
    else:
        block_descriptor = source_attr_spec[-1]
        print()
        print("chain_descriptor =", chain_descriptor)
        print("block_descriptor =", block_descriptor)
        transactions = node_connector.get_block(chain_descriptor, block_descriptor, query_attribute_clause)
        process_query_result(query_attribute_clause, ccql_data.BL, transactions, result_map)

    return result_map


def parse_class_attribute(statement):
    class_attr = statement.partition('.')
    return (class_attr[0], class_attr[2])
    
def parse_class(statement):
    class_attr = statement.partition('.')
    return class_attr[0]
    
def parse_attribute(statement):
    class_attr = statement.partition('.')
    return class_attr[-1]
    

def get_query_attributes(query_attribute_clause, source_type):
    query_attributes = []
    for statement in query_attribute_clause:
        query_attr_spec = statement.partition(".")
        q_type = query_attr_spec[0]
        if len(query_attr_spec) == 3 and query_attr_spec[1] == "." and q_type == source_type:
            source_type = query_attr_spec[0]
            last_attr = query_attr_spec[-1]
            query_attributes.append(last_attr)
    return query_attributes


def process_query_result(query_attribute_clause, source_type, result, result_map):

    if not source_type in result_map.keys():
        result_map[source_type] = {}

    for r in result:
        result_map[source_type][r[ccql_data.ID]] = r

def process_query_result_l(query_attribute_clause, source_type, result, result_map):

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

def output_query_result(query_attribute_clause, result_map):

    print()
    print("Query results:")
    output_query_result_by_attribute(query_attribute_clause, result_map)
    print()
    #print("DEBUG: Raw result data")
    #print(result_map)

    
def output_query_result_by_attribute(query_attribute_clause, result_map):

    #for source_type in sorted(result_map.keys()):
    types_output = ""
    types_output = append_query_result_types(result_map, types_output, query_attribute_clause)
    print(types_output)
    values_output = ""
    (n_rows, values_output) = append_query_result_values(result_map, values_output, query_attribute_clause)
    print(values_output)

    print("Number of rows:", n_rows)


def append_query_result_types(result_map, types_output, query_attribute_clause):
    for a in query_attribute_clause:
        types_output += a + "|"
    return types_output

def append_query_result_types_l(result_map, source_type, types_output):
    for att_type in result_map[source_type].keys():
        if att_type == R_MAX:
            continue
        types_output += att_type + "|"
    return types_output

def append_query_result_values(result_map, values_output, query_attribute_clause):

    n_rows = 1
    for q in query_attribute_clause:
        query_attr_spec = get_query_attributes(q)
        source_type = query_attr_spec[0]
        attr = query_attr_spec[-1]

        q_rows = 0

        for r in result_map[source_type].values():
            #val = result_map[source_type][r[ccql_data.ID]][attr]
            val = r[attr]
            if isinstance(val, list):
                q_rows += len(val)
            else:
                q_rows += 1

        n_rows *= q_rows

    n_rows_remaining = n_rows
    output_columns = []
    
    for q in query_attribute_clause:
        query_attr_spec = get_query_attributes(q)
        source_type = query_attr_spec[0]
        attr = query_attr_spec[-1]

        #if not a in r.keys():
        #    print("Attribute not found:", a)
        #    continue

        output_columns.append([])

        #print(source_type)
        #print(result_map)
        for r in result_map[source_type].values():
            val = r[attr]
            #print(val)
            #val = result_map[source_type][r[ccql_data.ID]][attr]
            if isinstance(val, list):
                n_rows_remaining = int(n_rows_remaining / len(val))
                for v in val:
                    for i in range(0, n_rows_remaining):
                        output_columns[-1].append(str(v))
            else:
                for i in range(0, n_rows_remaining):
                    output_columns[-1].append(str(val))
    
    n_columns = len(output_columns)
    
    #print(output_columns)

    for i in range(0, n_rows):
        for j in range(0, n_columns):
            values_output += output_columns[j][i] + "|"
        values_output += "\n"

    return (n_rows, values_output)


def carthesian_product(relations, attributes):
    
    for r in rows:

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


def get_query_attributes(query_statement):
    query_attr_spec = query_statement.partition(".")
    if not len(query_attr_spec) == 3:
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

    if len(opts) < 1:
        # no options given, assuming query statement follows
        process_query(args)

    for opt, arg in opts:
        if opt in ("-q", "--query"):
            process_query(args)
        elif opt in ("-h", "--help"):
            print_usage()
        else:
            print(CCQL_VERSION)

parse_cli()

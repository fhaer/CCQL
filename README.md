## CCQL

Prototype implementation, grammar, and data model of a cross-chain query language.

### Prototype

The prototype is implemented in Python 3.9, using the web3.py library for accessing blockchains. Additional node software running locally in a fully-validating configuration is required. The following Python 3 modules are required: Web3 requests base58 binascii hashlib .

Note: The prototype is only intended to demonstrate the feasibility of implementation.

#### Usage and Query Syntax

```
Usage: ccql.py [-h|--help] <QueryStatement>

<QueryStatement> =
  Q <AttrSpec>(, <AttrSpec>)*
  S <SourceSpec>(, <SourceSpec>)*
  [F <FilterSpec>(, <FilterSpec>)*];

```
#### Syntax of Query, Source, and Filter clauses 

The syntax is described in the following excerpt from the syntax diagrams (for the complete syntax and diagrams see the grammar directory):

<img src="https://github.com/fhaer/CCQL/blob/main/syntax_diagram_excerpt.png?raw=true" data-canonical-src="https://github.com/fhaer/CCQL/blob/main/syntax_diagram_excerpt.png?raw=true" width="550" />

The query clause and filter clause are specified with CCQLClass and AttrName. CCQLClass refers to a class of the data model, AttrName to an attribute of a class. The data model is located below.

The source clause is specified by a chain instance ChainI, network instance NetI, chain descriptor instance ChainDescI, and optional instances of block BlockI, transaction TxI, or account AccI. Supported instances of the data model classes are stored in ccql_node/ccql_data.py. For example, included instances are: 
- Ethereum: ChainI = eth, NetI = main (Ethereum mainnet), ChainDescI = 1 (Ethereum chain)
- Avalanche: ChainI = avax, NetI = main (Avalanche Primary Network), ChainDescI = p (P-Chain) / x (X-Chain) / c (C-Chain) 

##### Complete grammmar specification

In the grammar directory, the following files define the syntax:

- grammar-specification.ebnf: specification of the EBNF grammar
- grammar-specification.xhtml: generated HTML documentation of the grammar
- grammar-specification.xtext: implementation using the Eclipse Modeling Framework based on Xtext

#### Data Model

![Data Model](https://github.com/fhaer/CCQL/blob/main/data_model/ccql-data-model.svg?raw=true)

In the data_model directory, the model can be viewed in PDF, SVG, and XMI files created through Eclipse-based modeling software.


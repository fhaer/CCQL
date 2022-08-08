## CCQL

Data model, grammar, and prototype implementation of a cross-chain query language.

### Data Model

In the data_model directory, the model can be viewed in PDF, SVG, and XMI files created through Eclipse-based modeling software.

### Grammar Specification

In the grammar directory, the following files define the grammar:

- grammar-specification.ebnf: specification of the EBNF grammar
- grammar-specification.xhtml: generated HTML documentation of the grammar
- grammar-specification.xtext: implementation using the Eclipse Modeling Framework based on Xtext

### Prototype

The prototype is implemented in Python 3.9, using the web3.py library for accessing blockchains. Additional node software running locally in a fully-validating configuration is required.

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

The syntax is described in the following excerpt from the syntax diagrams (For the complete syntax and diagrams see the grammar directory).

<img src="https://github.com/fhaer/CCQL/blob/main/syntax_diagram_excerpt.png?raw=true" data-canonical-src="https://github.com/fhaer/CCQL/blob/main/syntax_diagram_excerpt.png?raw=true" width="550" />

The query clause and filter clause are specified with CCQLClass and AttrName. CCQLClass refers to a class of the data model, AttrName to an attribute of a class. The data model is located below.

The source clause is specified by a chain instance ChainI, network instance NetI, chain descriptor instance ChainDescI, and optional instances of block BlockI, transaction TxI, or account AccI. Supported instances of the data model classes are stored in ccql_node/ccql_data.py. For example, included instances are: 
- Ethereum: ChainI = eth, NetI = main (Ethereum mainnet), ChainDesc = 1 (Ethereum chain)
- Avalanche: ChainI = avax, NetI = main (Avalanche Primary Network), ChainDesc = p (P-Chain) / x (X-Chain) / c (C-Chain) 

#### Data Model

![Data Model](https://github.com/fhaer/CCQL/blob/main/data_model/ccql-data-model.svg?raw=true)


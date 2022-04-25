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

#### Usage

```
Usage: ccql.py [-h|--help] <query_statement>

CCQL Test environment.

Query Statement:

<query_statement> =
  Q <query_attribut_spec>(, <query_attribut_spec>)*
  S <source_spec>(, <source_spec>)*
  [F <filter_spec>(, <filter_spec>)*];

For details, refer to the EBNF grammar specification.
```


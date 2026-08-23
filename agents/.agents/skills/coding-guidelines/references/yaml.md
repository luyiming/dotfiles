## Use a restricted subset of YAML 1.2

- use the `.yaml` extension for new YAML files
- mapping keys are unique, unquoted snake_case identifiers (`[a-z][a-z0-9_]*`)
- strings use double quotes
- booleans are exactly `true` or `false`
- null is exactly `null`
- dates and datetimes are strings
- integers use decimal notation without unnecessary leading zeros
- floating-point numbers use decimal or scientific notation
- non-finite numbers such as `.inf` and `.nan` are not allowed
- use block style for mappings and sequences containing structured values
- short sequences of scalar values may use flow style (`[...]`)
- no anchors, aliases, or merge keys
- no YAML tags or custom constructors
- multiline strings use literal block scalars (`|`); folded block scalars (`>`) are not allowed

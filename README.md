`jschon-sort` sorts a JSON or YAML document according to its JSON Schema: that is, so that the order
in which its objects' keys are declared  matches the order in which properties are declared in its JSON Schema.

The "jschon" name relates to it being based on the [jschon](https://github.com/marksparkza/jschon) library
for JSON Schema handling.

## Motivation

JSON object properties have arbitrary order. In practice, within serialized JSON or YAML files,
a particular order of properties can benefit readability: for example,
`{"start": 10, "end": 20}` might read more naturally even though naive lexicographic sorting (e.g. with `json.dumps(..., sort_keys=True)`) would result in `{"end": 20, "start": 10}`.
While there are [several](https://github.com/json-schema/json-schema/issues/119)
[attempts](https://github.com/json-schema-org/json-schema-spec/issues/571)
to introduce property ordering into JSON Schema, here we're taking a different approach.
By leveraging the fact that the JSON Schema itself is written with human maintainers in mind,
we can extrapolate the intuitive order from the JSON Schema definitions' ordering and apply it on the document itself.

## Example

Given **schema**:

```json
{
  "type": "object",
  "properties": {
    "range": {
      "type": "object",
      "properties": {
        "start": {"type": "number"},
        "end": {"type": "number"}
      }
    }
  }
}
```

the following **document**:

```json
{"range": {"end": 20, "start": 10}}
```
would be reordered as:
```json
{"range": {"start": 20, "end": 10}}
```

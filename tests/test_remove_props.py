import json
from typing import Mapping

from jschon.json import JSONCompatible

from jschon_tools import process_json_doc


SCHEMA: Mapping[str, JSONCompatible] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "test": {
            "type": "array",
            "items": {
                "type": "object",
                # patternProperties is ordered intentionally before properties
                "patternProperties": {
                    "^B{3}$": {"type": "number"},
                    "^A{3}$": {"type": "number"},
                },
                "properties": {
                    "known": {"type": "number"},
                },
                "additionalProperties": True,
            },
        },
    },
}


def test_remove_additional_properties_from_json_doc() -> None:
    # Arrange
    doc_str = '{"test": [{"AAA": 1, "BBB": 2, "known": 3, "unknown": 4}]}'
    doc = json.loads(doc_str)

    # Act
    actual = process_json_doc(doc_data=doc, schema_data=SCHEMA, remove_additional_props=True)

    # Assert
    assert actual is not doc
    assert json.dumps(doc) == doc_str, "ensure doc is not modified in place"
    assert json.dumps(actual) == '{"test": [{"AAA": 1, "BBB": 2, "known": 3}]}'

import json
from typing import Dict
from typing import Mapping

import pytest
from jschon.json import JSONCompatible

from jschon_sort import sort_doc_by_schema


SCHEMA: Mapping[str, JSONCompatible] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "ranges": {
            "type": "array",
            "items": {
                "type": "object",
                # patternProperties is ordered intentionally before properties
                "patternProperties": {
                    "^B{3}$": {"type": "number"},
                    "^A{3}$": {"type": "number"},
                },
                "properties": {
                    "start": {"type": "number"},
                    "end": {"type": "number"},
                },
                "required": ["start", "end"],
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}


def test_sort_doc_by_schema__failed():
    # Arrange
    doc_str = '{"foo": "bar"}'
    doc = json.loads(doc_str)

    # Act
    with pytest.raises(ValueError, match='Document failed schema validation'):
        sort_doc_by_schema(doc_data=doc, schema_data=SCHEMA)

    # Assert
    assert json.dumps(doc) == doc_str, "ensure doc is not modified in place"


@pytest.mark.parametrize(
    'schema_version',
    [
        'https://json-schema.org/draft/2020-12/schema',
        'https://json-schema.org/draft-07/schema',
    ],
)
def test_sort_doc_by_schema(schema_version: str) -> None:
    # Arrange
    doc_str = '{"ranges": [{"end": 20, "start": 10, "AAA": 42, "BBB": 42}]}'
    doc = json.loads(doc_str)

    # Act
    actual = sort_doc_by_schema(doc_data=doc, schema_data={**SCHEMA, '$schema': schema_version})

    # Assert
    assert actual is not doc
    assert json.dumps(doc) == doc_str, "ensure doc is not modified in place"
    assert json.dumps(actual) == '{"ranges": [{"BBB": 42, "AAA": 42, "start": 10, "end": 20}]}'


def test_sort_doc_by_schema__local_ref() -> None:
    # Arrange
    doc_str = '{"foo": {"end": 20, "start": 10}}'
    doc = json.loads(doc_str)

    schema: Mapping[str, JSONCompatible] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "$defs": {
            "range": {
                "type": "object",
                "properties": {
                    "start": {"type": "number"},
                    "end": {"type": "number"},
                },
                "required": ["start", "end"],
                "additionalProperties": False,
            },
        },
        "additionalProperties": {
            "$ref": "#/$defs/range",
        },
    }

    # Act
    actual = sort_doc_by_schema(doc_data=doc, schema_data=schema)

    # Assert
    assert actual is not doc
    assert json.dumps(actual) == '{"foo": {"start": 10, "end": 20}}'


def test_sort_doc_by_schema__oneof() -> None:
    # Arrange
    doc_str = '{"abc": {"end": 20, "start": 10}, "xyz": {"to": 40, "from": 30}}'
    doc = json.loads(doc_str)

    schema: Mapping[str, JSONCompatible] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": {
            "type": "object",
            "oneOf": [
                {
                    "properties": {
                        "start": {"type": "number"},
                        "end": {"type": "number"},
                    },
                    "required": ["start", "end"],
                    "additionalProperties": False,
                },
                {
                    "properties": {
                        "from": {"type": "number"},
                        "to": {"type": "number"},
                    },
                    "required": ["from", "to"],
                    "additionalProperties": False,
                },
            ],
        },
    }

    # Act
    actual = sort_doc_by_schema(doc_data=doc, schema_data=schema)

    # Assert
    assert actual is not doc
    assert json.dumps(actual) == '{"abc": {"start": 10, "end": 20}, "xyz": {"from": 30, "to": 40}}'

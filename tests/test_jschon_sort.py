import json

import pytest

from jschon_sort import sort_doc_by_schema

SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "ranges": {
            "type": "array",
            "items": {
                "type": "object",
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
        sort_doc_by_schema(doc, SCHEMA)

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
    doc_str = '{"ranges": [{"end": 20, "start": 10}]}'
    doc = json.loads(doc_str)

    # Act
    actual = sort_doc_by_schema(doc, {**SCHEMA, '$schema': schema_version})

    # Assert
    assert actual is not doc
    assert json.dumps(doc) == doc_str, "ensure doc is not modified in place"
    assert json.dumps(actual) == '{"ranges": [{"start": 10, "end": 20}]}'

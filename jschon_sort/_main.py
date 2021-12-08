import copy
import math
from typing import Dict
from typing import List
from typing import Mapping
from typing import Tuple

import jschon.jsonschema
from jschon.json import AnyJSONCompatible


def _get_sort_keys_for_json_nodes(root_node: jschon.JSON) -> Mapping[jschon.JSONPointer, Tuple[int, ...]]:
    """
    Gets a mapping from JSON nodes (as JSON pointers) to sort keys (as tuples of integers) that match their position
    within the JSON.
    """
    mapping = {}
    root_depth = len(root_node.path)

    def _recurse(node: jschon.JSON, node_sort_key: Tuple[int, ...]) -> None:
        relative_path = node.path[root_depth:]
        mapping[relative_path] = node_sort_key

        if node.type == "object":
            for idx, v in enumerate(node.data.values()):
                new_loc = (*node_sort_key, idx)
                _recurse(v, new_loc)
        elif node.type == "array":
            for idx, v in enumerate(node.data):
                new_loc = (*node_sort_key, idx)
                _recurse(v, new_loc)

    _recurse(root_node, ())

    return mapping


def sort_doc_by_schema(*, doc_data: AnyJSONCompatible, schema_data: AnyJSONCompatible) -> AnyJSONCompatible:
    try:
        root_schema = jschon.JSONSchema(schema_data)
    except jschon.CatalogError:
        # jschon only supports newer jsonschema drafts
        schema_data = copy.copy(schema_data)
        schema_data['$schema'] = "https://json-schema.org/draft/2020-12/schema"
        root_schema = jschon.JSONSchema(schema_data)

    doc_json = jschon.JSON(doc_data)
    res = root_schema.evaluate(doc_json)
    if not res.valid:
        raise ValueError('Document failed schema validation')

    schema_sort_keys_cache: Dict[jschon.URI, Mapping[jschon.JSONPointer, Tuple[int, ...]]] = {}

    def _get_sort_keys_for_schema(schema: jschon.JSONSchema) -> Mapping[jschon.JSONPointer, Tuple[int, ...]]:
        if sort_keys := schema_sort_keys_cache.get(schema.canonical_uri):
            return sort_keys
        sort_keys = _get_sort_keys_for_json_nodes(schema)
        schema_sort_keys_cache[schema.canonical_uri] = sort_keys
        return sort_keys

    doc_sort_keys: Dict[jschon.JSONPointer, Tuple[int, ...]] = {}

    def _traverse_scope(scope: jschon.jsonschema.Scope) -> None:
        schema_sort_keys = _get_sort_keys_for_schema(scope.schema)
        doc_sort_keys.setdefault(scope.instpath, schema_sort_keys[scope.relpath])
        for child in scope.iter_children():
            _traverse_scope(child)

    _traverse_scope(res)

    end_sort_key = (math.inf,)

    def _sort_json_node(node: AnyJSONCompatible, json_node: jschon.JSON) -> AnyJSONCompatible:
        """Traverses the nodes while also keeping at pointer at a high-level JSON object (to get the JSON pointers)."""
        if json_node.type == "object":
            key_sort_keys: Dict[str, Tuple[Tuple[float, ...], str]] = {}

            properties: List[Tuple[str, AnyJSONCompatible]] = []

            k: str
            v: AnyJSONCompatible
            v_json: jschon.JSON
            for (k, v), v_json in zip(node.items(), json_node.data.values()):
                properties.append((k, _sort_json_node(v, v_json)))
                # Keys which don't map to the schema (e.g. undefined properties when additionalProperties is missing,
                # defaulting to true) are assumed to come last (end_sort_key).
                # As a tie breaker for multiple such undefined properties, we use the key's name.
                # TODO: update jschon to add additional properties to res.children when appropriate
                key_sort_keys[k] = doc_sort_keys.get(v_json.path, end_sort_key), k

            properties.sort(key=lambda pair: key_sort_keys[pair[0]])

            # to maintain YAML round-trip data, copy node and re-populate
            node_copy = node.copy()
            node_copy.clear()
            node_copy.update(properties)

            return node_copy

        elif json_node.type == "array":
            return [_sort_json_node(node[idx], v_json) for idx, v_json in enumerate(json_node.data)]

        return node

    # we recurse down both the "JSON" and the actual document, and mutate only the actual document
    # which is the primitive type that we can serialize back to JSON/YAML easily
    return _sort_json_node(doc_data, doc_json)

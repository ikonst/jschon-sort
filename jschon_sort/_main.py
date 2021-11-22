import copy
import math
from typing import Dict
from typing import Tuple

import jschon.jsonschema
from jschon.json import AnyJSONCompatible


def _get_sort_keys_for_json_nodes(node: jschon.JSON) -> Dict[jschon.JSONPointer, Tuple[int, ...]]:
    """
    Gets a mapping from JSON nodes (as JSON pointers) to sort keys (as tuples of integers) that match their position
    within the JSON.
    """
    mapping = {}

    def _recurse(node: jschon.JSON, node_sort_key: Tuple[int, ...]) -> None:
        if node.type == "object":
            for idx, v in enumerate(node.data.values()):
                new_loc = (*node_sort_key, idx)
                mapping[v.path] = new_loc
                _recurse(v, new_loc)
        elif node.type == "array":
            for idx, v in enumerate(node.data):
                new_loc = (*node_sort_key, idx)
                _recurse(v, new_loc)

    _recurse(node, ())

    return mapping


def sort_doc_by_schema(doc_data: AnyJSONCompatible, schema_data: AnyJSONCompatible) -> AnyJSONCompatible:
    schema_json = jschon.JSON(schema_data)
    schema_sort_keys = _get_sort_keys_for_json_nodes(schema_json)

    try:
        schema = jschon.JSONSchema(schema_data)
    except jschon.CatalogError:
        # jschon only supports newer jsonschema drafts
        schema_data = copy.copy(schema_data)
        schema_data['$schema'] = "https://json-schema.org/draft/2020-12/schema"
        schema = jschon.JSONSchema(schema_data)

    doc_json = jschon.JSON(doc_data)
    res = schema.evaluate(doc_json)
    doc_sort_keys = {}

    if not res.valid:
        raise ValueError('Document failed schema validation')

    def _traverse_children(scope: jschon.jsonschema.Scope) -> None:
        for child in scope.iter_children():
            doc_sort_keys[child.instpath] = schema_sort_keys[child.path]
            _traverse_children(child)

    _traverse_children(res)

    end_sort_key = (math.inf,)

    def _sort_json_node(node: AnyJSONCompatible, json_node: jschon.JSON) -> AnyJSONCompatible:
        """Traverses the nodes while also keeping at pointer at a high-level JSON object (to get the JSON pointers)."""
        if json_node.type == "object":
            key_sort_keys: Dict[str, Tuple[Tuple[float, ...], str]] = {}

            k: str
            v: AnyJSONCompatible
            v_json: jschon.JSON
            for (k, v), v_json in zip(node.items(), json_node.data.values()):
                node[k] = _sort_json_node(v, v_json)
                # Keys which don't map to the schema (e.g. undefined properties when additionalProperties is missing,
                # defaulting to true) are assumed to come last (end_sort_key).
                # As a tie breaker for multiple such undefined properties, we use the key's name.
                # TODO: fix jschon to add additional properties to res.children when appropriate
                key_sort_keys[k] = doc_sort_keys.get(v_json.path, end_sort_key), k

            return dict(sorted(node.items(), key=lambda pair: key_sort_keys[pair[0]]))

        elif json_node.type == "array":
            for idx, v_json in enumerate(json_node.data):
                node[idx] = _sort_json_node(node[idx], v_json)

        return node

    # we recurse down both the "JSON" and the actual document, and mutate only the actual document
    # which is the primitive type that we can serialize back to JSON/YAML easily
    return _sort_json_node(doc_data, doc_json)

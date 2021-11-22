import argparse
import json
import sys

import jschon

from ._main import sort_doc_by_schema
from ._yaml import create_yaml
from ._yaml import YamlIndent


def main():
    jschon.create_catalog('2020-12')

    parser = argparse.ArgumentParser(
        prog='jschon-sort',
        description="Sorts a JSON or YAML document to match a JSON Schema's order of properties",
    )
    parser.add_argument('path', help='path to the JSON / YAML document')
    parser.add_argument(
        '--schema', required=True, metavar='/path/to/schema.json', help='path to the JSON Schema document'
    )
    parser.add_argument(
        '--dry-run',
        '-n',
        help='if set, result is not persisted back to the original file',
        action='store_true',
    )
    parser.add_argument('--indent', type=int, default=4, help='indent size')
    parser.add_argument(
        '--yaml-indent',
        type=lambda s: YamlIndent(*map(int, s.split(','))),
        metavar='MAPPING,SEQUENCE,OFFSET',
        default=YamlIndent(2, 4, 2),
        help='YAML indent size',
    )
    args = parser.parse_args()

    is_yaml = args.path.endswith('.yaml') or args.path.endswith('.yml')
    yaml = create_yaml(indent=args.yaml_indent)
    with open(args.path) as f:
        if is_yaml:
            doc_data = yaml.load(f)
        else:
            doc_data = json.load(f)

    with open(args.schema) as f:
        schema_data = json.load(f)

    sorted_doc_data = sort_doc_by_schema(doc_data=doc_data, schema_data=schema_data)

    if not args.dry_run:
        if is_yaml:
            with open(args.path, 'w') as f:
                yaml.dump(sorted_doc_data, f)
        else:
            with open(args.path, 'w') as f:
                json.dump(sorted_doc_data, f, indent=args.indent)


if __name__ == '__main__':
    main()  # pragma: no cover

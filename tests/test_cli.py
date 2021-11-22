import json
import subprocess
from pathlib import Path
from textwrap import dedent
from typing import List
from typing import Literal
from typing import Union

import pytest


@pytest.mark.parametrize('dry_run', (False, True), ids=('wet_run', 'dry_run'))
@pytest.mark.parametrize('file_format', ('yaml', 'yaml_indented', 'json'))
def test_cli(tmp_path: Path, dry_run: bool, file_format: Literal['yaml', 'yaml_indented', 'json']) -> None:
    # Arrange
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "range": {
                "type": "object",
                "properties": {
                    "start": {"type": "number"},
                    "end": {"type": "number"},
                    "zero": {"type": "null"},
                },
                "additionalProperties": False,
            },
        },
        "additionalProperties": False,
    }

    if file_format == 'json':
        doc_text = '{"range": {"end": 20, "start": 10, "zero": null}}'
        doc_path = tmp_path / "doc.json"
        doc_path.write_text(doc_text)
    elif file_format in ('yaml', 'yaml_indented'):
        doc_text = dedent(
            """
        range:  # range comment
          end: 20  # end comment
          start: 10  # start comment
          zero: null
        """
        )
        doc_path = tmp_path / "doc.yaml"
        doc_path.write_text(doc_text)
    else:
        raise NotImplementedError(file_format)  # pragma: no cover

    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema))

    # Act
    args: List[Union[str, Path]] = ['jschon-sort', '--schema', schema_path, doc_path]
    if dry_run:
        args += ['--dry-run']
    if file_format == 'yaml_indented':
        args += ['--yaml-indent', '4,4,4']
    subprocess.check_output(args)

    # Assert
    if dry_run:
        assert doc_path.read_text() == doc_text
    else:
        if file_format == 'json':
            assert (
                doc_path.read_text()
                == dedent(
                    """
            {
                "range": {
                    "start": 10,
                    "end": 20,
                    "zero": null
                }
            }
            """
                ).strip()
            )
        elif file_format == 'yaml':
            assert (
                doc_path.read_text()
                == dedent(
                    """
            range:  # range comment
              start: 10  # start comment
              end: 20  # end comment
              zero: null
            """
                ).lstrip()
            )
        elif file_format == 'yaml_indented':
            assert (
                doc_path.read_text()
                == dedent(
                    """
                range:  # range comment
                    start: 10 # start comment
                    end: 20 # end comment
                    zero: null
                """
                ).lstrip()
            )
        else:
            raise NotImplementedError(file_format)  # pragma: no cover

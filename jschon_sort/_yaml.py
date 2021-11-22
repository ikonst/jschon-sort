from typing import NamedTuple

import ruyaml


class YamlIndent(NamedTuple):
    mapping: int
    sequence: int
    offset: int


def create_yaml(*, indent: YamlIndent) -> ruyaml.main.YAML:
    yaml = ruyaml.main.YAML()
    yaml.indent(**indent._asdict())
    yaml.preserve_quotes = True  # type: ignore[assignment]
    yaml.width = 4096  # type: ignore[assignment]
    yaml.Representer.add_representer(type(None), lambda self: self.represent_scalar('tag:yaml.org,2002:null', 'null'))
    return yaml

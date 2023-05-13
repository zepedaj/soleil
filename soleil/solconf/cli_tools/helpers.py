from typing import List, Optional
import yaml
from pathlib import Path
from importlib import import_module


def load_dot_solex(config_source):
    """
    Loads any extra arguments specified in a ``.solex`` file at the same level as the ``config_source`` file.
    """
    params = {}
    if (dot_solex := Path(config_source).parent / ".solex").is_file():
        with open(dot_solex, "rt") as fo:
            yaml_str = fo.read()
        params = yaml.safe_load(yaml_str)

    return params


def import_extra_modules(modules: Optional[List[str]], dot_solex_path: Path):
    # Load any extra modules specified in the CLI or in the .solex file.
    modules = (modules or []) + load_dot_solex(dot_solex_path).get("modules", [])
    for _mdl in modules:
        import_module(_mdl)

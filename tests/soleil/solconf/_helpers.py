from contextlib import contextmanager
from typing import Dict, Any
import os
from tempfile import TemporaryDirectory
from pathlib import Path
import yaml

DOCS_CONTENT_ROOT = Path(__file__).parent.parent.parent.parent / 'docs' / 'source' / 'content'


@contextmanager
def file_structure(contents: Dict[str, Any]):
    """
    Generates a file structure with the specified contents. The keys are the relative paths, the values the file contents.

    All paths must be relative paths that will be created within a temporary directory -- attempting to '..' outside this directory will raise an error.

    """
    path_mappings = {}
    with TemporaryDirectory() as temp_dir:
        # TODO - not great, creates a temporary directory in the CWD.
        # But chdir-ing somewhere else break pytest --pdb
        temp_dir = Path(temp_dir)
        for raw_path, contents in contents.items():
            path = (temp_dir / raw_path).resolve()
            if temp_dir not in path.parents:
                raise Exception(f'Invalid path `{raw_path}`.')
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as fo:
                yaml.dump(contents, fo)
            path_mappings[raw_path] = path

        yield temp_dir, path_mappings

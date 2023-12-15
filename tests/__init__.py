from pathlib import Path
from typing import Type
from uuid import uuid4
from soleil import load_solconf
from soleil.loader.loader import ConfigLoader

TEST_DATA_ROOT = Path(__file__).parent.parent / "data_for_tests"

__all__ = ["TEST_DATA_ROOT"]


def load_test_data(module, resolve=False, **kwargs) -> Type:
    kwargs.setdefault("package_name", uuid4().hex)
    return load_solconf(
        (TEST_DATA_ROOT / module).with_suffix(".solconf"), resolve=resolve, **kwargs
    )


# Avoid ipdb freeze
import freezegun

freezegun.configure(extend_ignore_list=["prompt_toolkit"])

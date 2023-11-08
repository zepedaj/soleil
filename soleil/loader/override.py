from dataclasses import asdict, dataclass
from typing import Optional
from pglib.autonamed_pattern import AutonamedPattern
import re
from enum import Enum, auto


# Regular expressions for ref strings.
_REF_STR_COMPONENT_PATTERN_RAW = r"(0|[1-9]\d*|\*?[_a-zA-Z]\w*)"
_FULL_REF_STR_PATTERN_RAW = AutonamedPattern(
    r"\.*(?P<start>{x})?(?(start)(\.+{x})*\.*)",
    {"x": AutonamedPattern(_REF_STR_COMPONENT_PATTERN_RAW)},
)

_OVERRIDE_PATTERN = re.compile(
    f"(?P<ref_str>{_FULL_REF_STR_PATTERN_RAW})(?P<assignment_type>\\=|\\*\\=)(?P<raw_content>.*)"
)


# TODO: The _OVERRIDE_PATTERN above should depend on the possible values of OverrideType
class OverrideType(Enum):
    existing = "="  # Assigns to existing value
    # clobber = "*=" # Overrides even specials like submodules()
    # append = "+="  # Appends the attribute or entry if it does not exist.


class Handled(Enum):
    HANDLED = auto()
    DELEGATED = auto()
    NOT_HANDLED = auto()


@dataclass
class Override:
    source: str
    """ The source string specified in the command line"""
    target: str
    """ The target name specifying the variable being overriden """
    type: OverrideType
    """ The type of override """
    value: str
    """ The value used to override """
    handled: Handled = Handled.NOT_HANDLED
    """ Whether the override was handled """
    as_id: bool = True
    """ Whether this override should be used to define :func:`id_str` """
    _binding_id: Optional[str] = None
    """ Used by the pre-processor to determine which module handles this override """

    @classmethod
    def build(cls, override_str: str):
        # TODO: Use a restricted ast processor to parse the override str - will result in earlier detection
        # e.g., currently the override 'device=cuda:1' should fail -- the correct override should be 'device="cuda:1"'.
        if not (parts := re.fullmatch(_OVERRIDE_PATTERN, override_str)):
            raise ValueError(f"Invalid override pattern {override_str}.")
        else:
            return cls(
                override_str,
                parts["ref_str"],
                OverrideType(parts["assignment_type"]),
                parts["raw_content"],
            )

    def copy(self, **new_vals):
        return type(self)(**{**asdict(self), **new_vals})

    def __str__(self, **updates):
        return f"{self.target}{self.type.value}{self.value}"

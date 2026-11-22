"""Select an existing unconditional-jump compare slot, scanning backwards."""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class SignatureSlot:
    index: int
    prefix: str
    added_value: bool = False


_WITH_VALUE = re.compile(r'^(jump\s+(\S+)\s+always)\s+(\S+)\s*$')
_WITHOUT_VALUE = re.compile(r'^(jump\s+(\S+)\s+always)\s*$')


def find_slot(lines: list[str]) -> SignatureSlot | None:
    """Return the final eligible slot; do not add, remove or reorder statements."""
    for index in range(len(lines) - 1, -1, -1):
        match = _WITH_VALUE.match(lines[index].strip())
        if match:
            return SignatureSlot(index, f"{match.group(1)} {match.group(3)}")
        match = _WITHOUT_VALUE.match(lines[index].strip())
        if match:
            return SignatureSlot(index, f"{match.group(1)} 0", added_value=True)
    return None

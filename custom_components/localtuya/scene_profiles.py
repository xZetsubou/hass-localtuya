"""Opt-in, device-specific scene catalogs for unusual Tuya DP formats.

The Eternity Eave profile contains values captured from the Smart Life app.
It does not apply to other lights in the generic Tuya ``dj`` category.
"""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
import re

ETERNITY_EAVE = "eternity_eave"
SCENE_PROFILES = {ETERNITY_EAVE: "Enbrighten Eternity Eave Lights (DP 106)"}


@lru_cache(maxsize=1)
def eternity_eave_scenes() -> dict[str, str]:
    """Return friendly name -> default DP 106 mode string.

    The first four hex characters identify a factory scene; the next four
    encode its default speed and the last four its default brightness.
    DIY modes can contain #delimited colors and are intentionally not mapped.
    """
    path = Path(__file__).with_name("scene_profiles") / "eternity_eave.csv"
    scenes: dict[str, str] = {}
    prefixes: set[str] = set()
    with path.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            name, value = row["name"], row["default"].lower()
            if not name or not re.fullmatch(r"[0-9a-f]{12}", value):
                raise ValueError(f"Invalid Eternity Eave scene: {name!r}")
            if name in scenes or value[:4] in prefixes:
                raise ValueError(f"Duplicate Eternity Eave scene: {name!r}")
            scenes[name] = value
            prefixes.add(value[:4])
    return scenes


def scene_for_value(value: str | None) -> str | None:
    """Resolve a factory scene even when its speed or brightness was changed."""
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-fA-F]{12}", value):
        return None
    prefix = value[:4].lower()
    return next(
        (name for name, default in eternity_eave_scenes().items() if default[:4] == prefix),
        None,
    )

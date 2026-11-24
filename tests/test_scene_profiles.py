"""Captured scene defaults for Enbrighten Eternity Eave lights."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

PROFILE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components/localtuya/scene_profiles.py"
)
spec = spec_from_file_location("scene_profiles_standalone", PROFILE_PATH)
assert spec is not None and spec.loader is not None
profiles = module_from_spec(spec)
spec.loader.exec_module(profiles)


def test_catalog_and_independent_slider_matching():
    scenes = profiles.eternity_eave_scenes()
    assert len(scenes) == 58
    assert scenes["Halloween"] == "020f01f403e8"
    assert scenes["Blue/White"] == "700c000003e8"
    assert scenes["Stata's Helper"] == "3a15012c03e8"
    assert profiles.scene_for_value("020f000a000a") == "Halloween"
    assert profiles.scene_for_value("3301012c03e8") == "Bubbly"
    assert profiles.scene_for_value("650c01f403e81#0019ff19#00ff4600") is None
    assert profiles.scene_for_value("H\x0b") is None
    assert profiles.scene_for_value(None) is None


@pytest.mark.parametrize("value", ["", "bad", "020f01f403e80", "zzzz01f403e8"])
def test_invalid_or_unrecognized(value):
    assert profiles.scene_for_value(value) is None

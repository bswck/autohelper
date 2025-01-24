from functools import partial
from pathlib import Path
from unittest.mock import Mock

import pytest
from inline_snapshot import snapshot
from pytest_subtests import SubTests

from autohelper.framework import debugging
from tests.test_framework import sample_module


def test_frame_location_with_implicit_offset() -> None:
    location = debugging.get_frame_location()
    assert location
    filename = str(Path(location.filename).relative_to(Path.cwd()))
    assert filename == snapshot("tests/test_framework/test_debugging.py")
    assert location.lineno == snapshot(14)


@partial(partial, sample_module.some_function)
def test_frame_location_with_explicit_offset() -> None:
    location = debugging.get_frame_location(offset=2)
    assert location
    filename = str(Path(location.filename).relative_to(Path.cwd()))
    assert filename == snapshot("tests/test_framework/sample_module.py")
    assert location.lineno == snapshot(5)


@pytest.fixture
def obj() -> Mock:
    return Mock()


def test_location(obj: Mock, subtests: SubTests) -> None:
    with subtests.test("test_saving"):
        # fmt: off
        debugging.save_location(obj); location = debugging.get_frame_location()  # noqa: E702
        # fmt: on
        saved_location = getattr(obj, debugging.LOCATION_ATTR)
        assert saved_location == location
    with subtests.test("test_retrieving"):
        assert debugging.get_location_info(obj) == saved_location
    with subtests.test("test_formatting"):
        assert debugging.get_location(obj) == snapshot(
            "tests/test_framework/test_debugging.py:38"
        )

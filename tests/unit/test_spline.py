"""Regression tests for the ActiveX spline contract."""

from unittest.mock import MagicMock

import pytest

from adapters.mixins.drawing_mixin import DrawingMixin
from core import InvalidParameterError


@pytest.fixture
def adapter():
    instance = DrawingMixin()
    instance._get_document = MagicMock()
    instance._points_to_variant_array = lambda points: tuple(points)
    instance._to_variant_array = tuple
    instance._finalize_entity = MagicMock(return_value="AB")
    return instance


def test_spline_uses_three_arguments_and_numeric_tangents(adapter):
    model = adapter._get_document.return_value.ModelSpace
    model.AddSpline.side_effect = lambda points, start, end: MagicMock(Handle="AB")
    assert adapter.draw_spline([(0, 0), (20, 30), (40, 0)]) == "AB"
    assert model.AddSpline.call_args.args[1:] == ((0.0, 0.0, 0.0),) * 2


def test_closed_spline_uses_writable_closed2(adapter):
    spline = adapter._get_document.return_value.ModelSpace.AddSpline.return_value
    adapter.draw_spline([(0, 0), (20, 30), (40, 0)], closed=True)
    assert spline.Closed2 is True


@pytest.mark.parametrize("degree", [1, 2, 4])
def test_unsupported_degree_rejected_before_creating_entity(adapter, degree):
    with pytest.raises(InvalidParameterError):
        adapter.draw_spline([(0, 0), (20, 30)], degree=degree)
    adapter._get_document.return_value.ModelSpace.AddSpline.assert_not_called()


def test_failed_closure_removes_partial_spline(adapter):
    class ReadOnlySpline:
        __slots__ = ("Delete",)

        def __init__(self):
            self.Delete = MagicMock()

    spline = ReadOnlySpline()
    adapter._get_document.return_value.ModelSpace.AddSpline.return_value = spline
    with pytest.raises(AttributeError):
        adapter.draw_spline([(0, 0), (20, 30), (40, 0)], closed=True)
    spline.Delete.assert_called_once()

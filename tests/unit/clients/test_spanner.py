import pytest

from recap.clients.spanner import SpannerClient


@pytest.mark.parametrize(
    "method, paths, expected_result",
    [
        # Test ls method
        ("ls", [], ("spanner://", [None, None, None, None])),
        ("ls", ["instance1"], ("spanner://", [None, "instance1", None, None])),
        (
            "ls",
            ["instance1", "database1"],
            ("spanner://", [None, "instance1", "database1", None]),
        ),
        (
            "ls",
            ["instance1", "database1", "table1"],
            ("spanner://", [None, "instance1", "database1", "table1"]),
        ),
        # Test schema method
        ("schema", [], ("spanner://", [None, None, None, None])),
        (
            "schema",
            ["instance1", "database1", "table1"],
            ("spanner://", [None, "instance1", "database1", "table1"]),
        ),
        # Test invalid method
        (
            "invalid_method",
            ["instance1"],
            pytest.raises(ValueError, match="Invalid method"),
        ),
    ],
)
def test_parse_method(method, paths, expected_result):
    """Test parsing of URL paths for different methods."""
    if isinstance(expected_result, tuple):
        result = SpannerClient.parse(method, paths)
        assert result == expected_result
    else:
        with expected_result:
            SpannerClient.parse(method, paths)

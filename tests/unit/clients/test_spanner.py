import pytest

from recap.clients.spanner import SpannerClient


@pytest.mark.parametrize(
    "method, paths, expected_result",
    [
        # Test ls method
        ("ls", [], ("spanner://", [None, None, None, None])),
        ("ls", ["project1"], ("spanner://", ["project1", None, None, None])),
        (
            "ls",
            ["project1", "instance1"],
            ("spanner://", ["project1", "instance1", None, None]),
        ),
        (
            "ls",
            ["project1", "instance1", "database1"],
            ("spanner://", ["project1", "instance1", "database1", None]),
        ),
        (
            "ls",
            ["project1", "instance1", "database1", "table1"],
            ("spanner://", ["project1", "instance1", "database1", "table1"]),
        ),
        # Test schema method
        ("schema", [], ("spanner://", [None, None, None, None])),
        (
            "schema",
            ["project1", "instance1", "database1", "table1"],
            ("spanner://", ["project1", "instance1", "database1", "table1"]),
        ),
        # Test invalid method
        (
            "invalid_method",
            ["project1"],
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

from secbrain.utils.response_diff import (
    diff_body_size_entropy,
    diff_headers,
    diff_json_semantic,
    diff_keywords,
    diff_status,
)


def test_diff_status():
    assert diff_status(200, 200)["changed"] is False
    assert diff_status(200, 403)["changed"] is True


def test_diff_headers():
    res = diff_headers({"A": "1"}, {"a": "2", "b": "3"})
    assert res["has_diff"] is True
    assert "a" in res["changed"]
    assert "b" in res["added"]
    assert "a" not in res["removed"]


def test_diff_body_size_entropy():
    res = diff_body_size_entropy("aaa", "aaab")
    assert res["size"]["delta"] == 1
    assert res["entropy"]["test"] >= res["entropy"]["baseline"]


def test_diff_keywords():
    res = diff_keywords("hello", "hello admin", ["admin", "forbidden"])
    assert res["changed"] is True
    assert res["keywords"]["admin"]["baseline"] is False
    assert res["keywords"]["admin"]["test"] is True


def test_diff_json_semantic():
    res = diff_json_semantic('{"a":1}', '{"a":1,"b":2}')
    assert res["changed"] is True
    assert "b" in res["added_keys"]

import io
import json

import pytest

from plagx_preflight import CHECKS, VERSION, check_draft, count_words, find_citations, split_sentences
from plagx_preflight.cli import main


def codes(text, **options):
    return [i["code"] for i in check_draft(text, **options)["issues"]]


def test_result_shape():
    r = check_draft("The the cat sat.")
    assert list(r) == ["stats", "errors", "warnings", "infos", "issues"]
    assert list(r["stats"]) == ["words", "sentences", "paragraphs", "characters", "readingTimeMinutes", "fleschReadingEase"]
    assert list(r["issues"][0]) == ["level", "code", "message", "start", "end", "line", "column", "text", "suggestion"]
    assert r["issues"][0]["message"] == 'Suggestion: "The the" looks like a repeated word.'


def test_utf16_offsets():
    i = next(x for x in check_draft("\U0001F600 the the end.")["issues"] if x["code"] == "repeated-word")
    assert (i["start"], i["end"], i["column"]) == (3, 10, 4)
    assert check_draft("a\U0001F600b")["stats"]["characters"] == 3


def test_helpers():
    assert count_words("It's a well-known fact, 42 times.") == 6
    assert [s["text"] for s in split_sentences("One. Two!")] == ["One.", "Two!"]
    c = find_citations("é (Moore, 2011; Price, 2016, 2018)")
    assert [f"{x['key']}:{x['year']}" for x in c] == ["moore:2011", "price:2016", "price:2018"]
    assert c[0]["start"] == 3
    assert [x["key"] for x in find_citations("(Greenblatt 45)", "mla")] == ["greenblatt"]
    assert VERSION == "0.1.2" and "passive-voice" in CHECKS


def test_options():
    assert codes("One two. Three four.", min_words=10, required_headings=["Introduction", "Conclusion"], checks=["length"]) == [
        "missing-heading", "missing-heading", "word-count-low"]
    assert codes("the the ,,", checks=[]) == []
    assert "passive-voice" in codes("The data were collected.", checks=["passive-voice"])


@pytest.mark.parametrize("bad", [{"style": "chicago"}, {"checks": ["magic"]}, {"min_words": -1}, {"max_words": "ten"}])
def test_invalid_options(bad):
    with pytest.raises(ValueError):
        check_draft("x", **bad)


def run(*args, stdin=None):
    out, err = io.StringIO(), io.StringIO()
    code = main(list(args), out, err)
    return code, out.getvalue(), err.getvalue()


@pytest.fixture
def files(tmp_path):
    bad = tmp_path / "bad.txt"
    bad.write_text("Shown (Smith, 2020). the the end.\n", encoding="utf-8")
    clean = tmp_path / "clean.md"
    clean.write_text("A clean draft. It has two sentences.\n", encoding="utf-8")
    return bad, clean


def test_cli_check(files):
    bad, clean = files
    code, out, _ = run("check", str(bad))
    assert code == 1 and "missing-reference-section" in out
    assert run("check", str(clean))[0] == 0
    assert run("check", str(clean), "--min-words", "50", "--strict")[0] == 1
    code, out, _ = run("check", str(clean), "--json", "--require-heading=Conclusion")
    assert [i["code"] for i in json.loads(out)[0]["issues"]] == ["missing-heading"]


def test_cli_stats(files):
    _, clean = files
    code, out, _ = run("stats", str(clean))
    assert code == 0 and "Words:               7" in out
    assert json.loads(run("stats", str(clean), "--json")[1])[0]["stats"]["sentences"] == 2


def test_cli_usage_errors(files, tmp_path):
    _, clean = files
    doc = tmp_path / "paper.docx"
    doc.write_text("x")
    for args in (["check"], ["check", str(doc)], ["check", str(tmp_path / "missing.txt")], ["check", str(clean), "--style", "x"],
                 ["check", str(clean), "--min-words", "ten"], ["check", str(clean), "--checks", "magic"], ["lint", str(clean)], []):
        assert run(*args)[0] == 2, args
    assert run("--version")[1] == f"{VERSION}\n"
    assert "plagx-preflight check <file>" in run("--help")[1]

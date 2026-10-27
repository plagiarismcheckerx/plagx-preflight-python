# Plagx Preflight for Python

*A free academic writing tool by Plagiarism Checker X.*

**Plagx Preflight for Python is a free, open-source draft checker for Python.** Use it as an essay checker before you submit: it checks the word count and structure, matches in-text citations against the reference list, and gives punctuation and basic grammar suggestions plus readability stats.

- No dependencies, works offline: your text never leaves the machine
- Python 3.9+, typed
- APA and MLA citation checks
- Command line with JSON output and CI-friendly exit codes
- Results identical to the [JavaScript version](https://github.com/plagiarismcheckerx/plagx-preflight), offsets included

**[Try the live demo →](https://plagiarismcheckerx.github.io/plagx-preflight/)**

Developer downloads: [PyPI](https://pypi.org/project/plagx-preflight/) · [npm](https://www.npmjs.com/package/plagx-preflight) · [Packagist](https://packagist.org/packages/plagiarismcheckerx/plagx-preflight) · [Docker Hub](https://hub.docker.com/r/plagiarismcheckerx/plagx-preflight) · [GitHub](https://github.com/plagiarismcheckerx/plagx-preflight)

> Plagx Preflight is a free academic writing utility by Plagiarism Checker X. It checks length, structure, references, punctuation and basic grammar, and every result is a suggestion. Plagiarism checking and AI-generated text detection are available in Plagiarism Checker X, linked at the end of this page.

## Install

```bash
pip install plagx-preflight
```

## Quick start

```python
from plagx_preflight import check_draft

result = check_draft(text, min_words=1500, max_words=2000, style="apa",
                     required_headings=["Introduction", "Conclusion"])

result["stats"]
# {'words': 1620, 'sentences': 84, 'paragraphs': 12, 'characters': 9811,
#  'readingTimeMinutes': 9, 'fleschReadingEase': 48.2}

for issue in result["issues"]:
    print(f"{issue['line']}:{issue['column']} {issue['level']} {issue['message']}")
# 5:14 warning Suggestion: "the the" looks like a repeated word.
```

## Command line

```bash
plagx-preflight check essay.txt --min-words 1500 --max-words 2000 --style apa
plagx-preflight check essay.md --json
plagx-preflight stats essay.txt
cat essay.txt | plagx-preflight check -
python -m plagx_preflight --help
```

| Option | Meaning |
|---|---|
| `--min-words <n>`, `--max-words <n>` | Word limits (reference list excluded) |
| `--style apa\|mla` | Citation style (default `apa`) |
| `--checks <list>` | Comma-separated check groups |
| `--require-heading <name>` | Required heading, repeatable |
| `--strict` | Count warnings as failures |
| `--json` | JSON output |

Exit codes: `0` no errors, `1` errors found (with `--strict`, warnings too), `2` usage or input error. Accepts `.txt` and `.md`.

## API

`check_draft(text, *, min_words=None, max_words=None, style="apa", checks=None, required_headings=())` returns a dict with `stats`, `errors`, `warnings`, `infos` and `issues`. Each issue has `level`, `code`, `message`, `start`, `end`, `line`, `column`, `text` and `suggestion`. Issues are sorted by position.

`start`, `end` and `column` count UTF-16 code units, like JavaScript, so results match the other Plagx Preflight libraries exactly. For Python string slicing, use `text` or `line` and `column` (they differ only after emoji and other characters outside the Basic Multilingual Plane).

| Option | Default | |
|---|---|---|
| `min_words`, `max_words` | `None` | Word limits (reference list excluded) |
| `style` | `"apa"` | `"apa"` or `"mla"` |
| `checks` | all except `"passive-voice"` | `length`, `references`, `punctuation`, `grammar`, `passive-voice` |
| `required_headings` | `()` | e.g. `["Introduction", "Conclusion"]` |

Helpers: `count_words(text)`, `split_sentences(text)`, `find_citations(text, style)`, `VERSION`, `CHECKS`. Invalid options raise `ValueError`.

## Checks

| Group | Codes | Level |
|---|---|---|
| Length & structure | `word-count-low`, `word-count-high`, `long-sentence` (over 40 words), `long-paragraph` (over 250 words), `single-sentence-paragraph`, `missing-heading` | warning / info |
| References | `citation-no-reference`, `missing-reference-section`, `reference-not-cited`, `et-al-format` | error / warning |
| Punctuation | `unmatched-quote`, `unmatched-bracket`, `double-space`, `space-before-punctuation`, `missing-space-after-punctuation`, `repeated-punctuation`, `mixed-quote-styles` | warning / info |
| Grammar | `repeated-word`, `a-an`, `sentence-capital`, `lowercase-i`, `common-confusion`, `passive-voice` (off by default) | warning / info |

## Good to know

- Every result is a suggestion. The grammar rules are deliberately conservative, so they miss some mistakes rather than flag correct text.
- The reference list starts at a heading such as References, Bibliography or Works Cited. It is excluded from the word count and from the punctuation and grammar checks.

## Development

```bash
pip install -e . pytest
pytest
```

`tests/parity/expected.json` and `tests/fixtures/` come from the JavaScript reference (`npm run parity` in plagx-preflight). Every case must match exactly. `src/plagx_preflight/_unicode.py` holds Unicode letter classes generated from the JavaScript regex engine (`node scripts/build_unicode.mjs`), because Python's `re` module has no `\p{...}`.

## Plagx Preflight - Free Draft & Grammar Checker

An open-source writing utility for students, researchers and developers. Check length, structure, citations, punctuation and basic grammar before you submit.

Developed by Plagiarism Checker X.

Plagx Preflight gives writing suggestions; it does not detect plagiarism or AI-generated text. For full document checks, explore [Plagiarism Checker X](https://plagiarismcheckerx.com/?utm_source=plagx-preflight-python) and its [AI Content Detector](https://plagiarismcheckerx.com/ai-content-detector?utm_source=plagx-preflight-python).

## License

MIT © Plagiarism Checker X

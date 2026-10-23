"""Plagx Preflight command line. A free academic writing utility by Plagiarism Checker X."""
from __future__ import annotations

import json
import os
import sys
from typing import List, Optional, TextIO

from . import CHECKS, DEFAULT_CHECKS, STYLES, __version__, check_draft

HELP = f"""Plagx Preflight {__version__}: check a draft before you submit

Usage:
  plagx-preflight check <file> [...]   List suggestions for length, references,
                                       punctuation and basic grammar
  plagx-preflight stats <file> [...]   Print word count, sentences and readability

<file> is a .txt or .md file. Use - to read from stdin.

Options:
  --min-words <n>               Minimum word count
  --max-words <n>               Maximum word count
  --style apa|mla               Citation style (default: apa)
  --checks <list>               Comma-separated: {",".join(CHECKS)}
                                (default: all except passive-voice)
  --require-heading <name>      Required heading (repeatable)
  --strict                      check: treat warnings as errors
  --json                        Print the result as JSON
  -v, --version                 Show version
  -h, --help                    Show this help

Exit codes: 0 = no errors, 1 = errors found, 2 = usage or input error.

Automated suggestions only. A free academic writing utility by Plagiarism
Checker X, which checks originality and AI-generated text: https://plagiarismcheckerx.com/"""


class UsageError(Exception):
    pass


def _csv(s: str) -> List[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def _parse_args(argv: List[str]):
    opts = {"style": "apa", "checks": list(DEFAULT_CHECKS), "required_headings": [], "min_words": None,
            "max_words": None, "strict": False, "json": False, "help": False, "version": False}
    args = []
    i = 0
    while i < len(argv):
        a = argv[i]
        inline = None
        if a.startswith("--") and "=" in a:
            a, inline = a.split("=", 1)

        def value() -> str:
            nonlocal i
            if inline is not None:
                return inline
            if i + 1 >= len(argv):
                raise UsageError(f"{a} needs a value")
            i += 1
            return argv[i]

        def number() -> int:
            v = value()
            if not v.isascii() or not v.isdigit():
                raise UsageError(f"{a} needs a whole number")
            return int(v)

        if a == "--min-words":
            opts["min_words"] = number()
        elif a == "--max-words":
            opts["max_words"] = number()
        elif a == "--style":
            opts["style"] = value()
        elif a == "--checks":
            opts["checks"] = _csv(value())
        elif a == "--require-heading":
            opts["required_headings"].append(value())
        elif a == "--strict":
            opts["strict"] = True
        elif a == "--json":
            opts["json"] = True
        elif a in ("-h", "--help"):
            opts["help"] = True
        elif a in ("-v", "--version"):
            opts["version"] = True
        elif a.startswith("-") and a != "-":
            raise UsageError(f"Unknown option {a}")
        else:
            args.append(a)
        i += 1
    if opts["style"] not in STYLES:
        raise UsageError(f'Unknown style "{opts["style"]}". Use: {", ".join(STYLES)}')
    for c in opts["checks"]:
        if c not in CHECKS:
            raise UsageError(f'Unknown check "{c}". Use: {", ".join(CHECKS)}')
    return opts, args


def load_text(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if path != "-" and ext not in (".txt", ".md"):
        raise UsageError(f"{path}: only .txt and .md files are supported")
    try:
        if path == "-":
            data = sys.stdin.buffer.read()
        else:
            with open(path, "rb") as f:
                data = f.read()
        text = data.decode("utf-8")
    except FileNotFoundError:
        raise UsageError(f"Cannot read {path}: file not found") from None
    except (OSError, UnicodeDecodeError) as e:
        raise UsageError(f"Cannot read {path}: {e}") from None
    return text[1:] if text.startswith("﻿") else text


def _print_stats(file: str, s: dict) -> str:
    return "\n".join([
        file,
        f"  Words:               {s['words']}",
        f"  Sentences:           {s['sentences']}",
        f"  Paragraphs:          {s['paragraphs']}",
        f"  Characters:          {s['characters']}",
        f"  Reading time:        {s['readingTimeMinutes']} min",
        f"  Flesch reading ease: {s['fleschReadingEase']}",
    ])


def _print_check(file: str, r: dict) -> str:
    lines = [f"{file}:{x['line']}:{x['column']}  {x['level']:<7} {x['code']:<32} {x['message']}" for x in r["issues"]]
    lines.append(f"{file}: {r['stats']['words']} words, {r['errors']} error(s), {r['warnings']} warning(s), {r['infos']} info")
    return "\n".join(lines)


def main(argv: List[str], out: Optional[TextIO] = None, err: Optional[TextIO] = None) -> int:
    out = out or sys.stdout
    err = err or sys.stderr
    try:
        opts, args = _parse_args(argv)
    except UsageError as e:
        err.write(f"{e}\n\nRun plagx-preflight --help for usage.\n")
        return 2
    if opts["version"]:
        out.write(f"{__version__}\n")
        return 0
    if opts["help"] or not args:
        out.write(f"{HELP}\n")
        return 0 if opts["help"] or args else 2
    command, files = args[0], args[1:]
    try:
        if command not in ("check", "stats"):
            raise UsageError(f'Unknown command "{command}"')
        if not files:
            raise UsageError(f"{command} needs a file (.txt or .md, or - for stdin)")
        texts = [(f, load_text(f)) for f in files]
    except UsageError as e:
        err.write(f"{e}\n\nRun plagx-preflight --help for usage.\n")
        return 2

    failed = False
    reports = []
    for file, text in texts:
        if command == "stats":
            r = check_draft(text, checks=[])
        else:
            r = check_draft(text, min_words=opts["min_words"], max_words=opts["max_words"], style=opts["style"],
                            checks=opts["checks"], required_headings=opts["required_headings"])
        if r["errors"] or (opts["strict"] and r["warnings"]):
            failed = True
        reports.append({"file": file, **r})
    dump = lambda data: json.dumps(data, indent=2, ensure_ascii=False)  # noqa: E731
    if command == "stats":
        data = [{"file": r["file"], "stats": r["stats"]} for r in reports]
        out.write(f"{dump(data)}\n" if opts["json"] else "\n\n".join(_print_stats(r["file"], r["stats"]) for r in reports) + "\n")
        return 0
    out.write(f"{dump(reports)}\n" if opts["json"] else "\n\n".join(_print_check(r["file"], r) for r in reports) + "\n")
    return 1 if failed else 0


def run() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))

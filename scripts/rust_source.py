"""Bounded Rust source inspection shared with the implementation regression gate.

Extracted from the 2026-11-23 production-duplication-audit/audit.py lexer and
function-body walk. This is lexical inspection, not a Rust parser/type checker.
Strings (including raw strings), chars and nested comments remain indivisible;
test-only items are excluded, while platform/feature production cfg is retained.
"""
from __future__ import annotations

import bisect
import hashlib
import json
from pathlib import PurePosixPath
import re

EXCLUDE = frozenset({
    "test", "tests", "bench", "benches", "benchmarks", "comparison", "compare",
    "example", "examples", "fuzz", "fixtures", "testdata", "vendor", "third_party",
    "third-party", "external", "node_modules", "target", "build",
    "historical-source", "transport-lab",
})
_RAW = re.compile(r'(?:br|cr|r)(#*)"')
_QUOTED = re.compile(r'(?:b|c)?"')
_CHAR = re.compile(r"(?:b)?'(?:\\(?:u\{[0-9a-fA-F_]+\}|x[0-9a-fA-F]{2}|.)|[^'\\\n])'")
_WORD = re.compile(r"(?:r#)?[A-Za-z_][A-Za-z_0-9]*|[0-9][A-Za-z_0-9.]*")
_IDENT = re.compile(r"(?:r#)?[A-Za-z_][A-Za-z_0-9]*\Z")
_KEYWORDS = frozenset("as async await break const continue crate dyn else enum extern false fn for if impl in let loop match mod move mut pub ref return self Self static struct super trait true type unsafe use where while".split())


def production_path(path, *, generated=()):
    path = PurePosixPath(path)
    return (path.suffix == ".rs" and path.name != "build.rs"
            and path.as_posix() not in generated
            and not any(part.lower() in EXCLUDE for part in path.parts)
            and not re.search(r"(?:^|_)(?:tests?|fixture)(?:_|\.)", path.name))


def tokens(text):
    """Return (token, byte-independent character offset), omitting comments."""
    out, i = [], 0
    while i < len(text):
        if text[i].isspace():
            i += 1
            continue
        if text.startswith("//", i):
            end = text.find("\n", i)
            i = len(text) if end < 0 else end
            continue
        if text.startswith("/*", i):
            depth, i = 1, i + 2
            while i < len(text) and depth:
                if text.startswith("/*", i):
                    depth, i = depth + 1, i + 2
                elif text.startswith("*/", i):
                    depth, i = depth - 1, i + 2
                else:
                    i += 1
            continue
        start = i
        raw, quoted, char = _RAW.match(text, i), _QUOTED.match(text, i), _CHAR.match(text, i)
        if raw:
            end = text.find('"' + raw[1], raw.end())
            i = len(text) if end < 0 else end + 1 + len(raw[1])
        elif quoted:
            i = quoted.end()
            while i < len(text):
                if text[i] == "\\":
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
        elif char:
            i = char.end()
        else:
            word = _WORD.match(text, i)
            i = word.end() if word else i + 1
        out.append((text[start:i], start))
    return out


def _matching(values):
    close, stack = {}, []
    pairs = {")": "(", "]": "[", "}": "{"}
    for index, value in enumerate(values):
        if value in ("(", "[", "{"):
            stack.append((value, index))
        elif value in pairs and stack and stack[-1][0] == pairs[value]:
            _, start = stack.pop()
            close[start] = index
    return close


def _cfg_without_tests(values):
    """Three-valued cfg evaluation with test=false, all other cfg unknown."""
    if values == ["test"]:
        return False
    if len(values) < 3 or values[1] != "(" or values[-1] != ")":
        return None
    name = values[0]
    args, current, depth = [], [], 0
    for value in values[2:-1] + [","]:
        if value == "," and depth == 0:
            if current:
                args.append(_cfg_without_tests(current))
            current = []
        else:
            current.append(value)
            depth += (value == "(") - (value == ")")
    if name == "all":
        return False if False in args else True if all(x is True for x in args) else None
    if name == "any":
        return True if True in args else False if all(x is False for x in args) else None
    if name == "not" and len(args) == 1 and args[0] is not None:
        return not args[0]
    return None


def production_tokens(text):
    ts = tokens(text)
    values = [token for token, _ in ts]
    close, excluded = _matching(values), []
    for index, value in enumerate(values):
        if value != "#":
            continue
        start = index + 1
        inner = start < len(values) and values[start] == "!"
        start += inner
        if start not in close or values[start] != "[":
            continue
        end = close[start]
        attr = values[start + 1:end]
        test_only = attr == ["test"] or (len(attr) > 3 and attr[:2] == ["cfg", "("]
                                         and attr[-1] == ")" and _cfg_without_tests(attr[2:-1]) is False)
        if not test_only:
            continue
        if inner:
            enclosing = [(begin, finish) for begin, finish in close.items()
                         if values[begin] == "{" and begin < index < finish]
            if not enclosing:
                excluded.append((0, len(ts) - 1))
            else:
                begin, finish = min(enclosing, key=lambda pair: pair[1])
                item = begin
                while item and values[item - 1] not in ("{", "}", ";"):
                    item -= 1
                # A module-level inner attribute excludes the entire module.
                # Other inner-attribute contexts stay in scope conservatively.
                if "mod" in values[item:begin]:
                    excluded.append((item, finish))
        else:
            cursor = end + 1
            while cursor < len(values) and values[cursor] not in ("{", ";"):
                # Other attributes, parameters and array types can themselves
                # contain braces/semicolons; none of those ends the item.
                cursor = close[cursor] + 1 if values[cursor] in ("[", "(") and cursor in close else cursor + 1
            excluded.append((index, close.get(cursor, cursor)))
    kept, limit = [], -1
    intervals = iter(sorted(excluded))
    current = next(intervals, None)
    for index, token in enumerate(ts):
        while current and current[0] <= index:
            limit = max(limit, current[1])
            current = next(intervals, None)
        if index > limit:
            kept.append(token)
    return kept


def _local_names(header, body):
    # Conservative binding subset: named arguments and simple let/for patterns.
    # Calls, method/field/path names, constants and protocol literals are not
    # globally renamed. Unsupported binding syntax keeps its exact spelling.
    close = _matching(header)
    params = next((i for i, token in enumerate(header) if token == "("), None)
    args = header[params + 1:close[params]] if params in close else []
    names = {token for index, token in enumerate(args[:-1])
             if _IDENT.fullmatch(token) and args[index + 1] == ":"
             and (index + 2 == len(args) or args[index + 2] != ":")}
    for index, token in enumerate(body):
        if token not in ("let", "for"):
            continue
        pattern = []
        for value in body[index + 1:]:
            if value in ("=", ":", "in", ";"):
                break
            pattern.append(value)
        if (any(value not in ("mut", "ref", "&", "(", ")", "[", "]", ",")
                and not _IDENT.fullmatch(value) for value in pattern)
                or any(_IDENT.fullmatch(value) and pattern[i + 1] == "("
                       for i, value in enumerate(pattern[:-1]))):
            continue
        names.update(value for value in pattern if _IDENT.fullmatch(value) and value not in _KEYWORDS)
    return names - _KEYWORDS


def body_fingerprint(body, *, locals=None):
    if locals:
        names, normalized, stack = {}, [], []
        for index, token in enumerate(body):
            before = body[index - 1] if index else ""
            after = body[index + 1] if index + 1 < len(body) else ""
            opening = stack[-1][1] if stack and stack[-1][0] == "{" else 0
            owner = body[opening - 1] if opening else ""
            # In Record { field }, `field` names both a local and a field.
            # Preserve it. Ambiguous identifier-led braces stay conservative;
            # this may miss a rename but must not merge distinct field names.
            shorthand = (opening and (_IDENT.fullmatch(owner) or owner == ">")
                         and before in ("{", ",", "]") and after in (",", "}"))
            if (token in locals and not shorthand and before not in (".", ":", "fn")
                    and after not in ("(", "!", ":")):
                token = names.setdefault(token, f"local_{len(names)}")
            normalized.append(token)
            if body[index] in ("(", "[", "{"):
                stack.append((body[index], index))
            elif body[index] in (")", "]", "}") and stack:
                stack.pop()
        body = normalized
    return hashlib.sha256(json.dumps(body).encode()).hexdigest()


def functions(text, ts=None):
    ts = production_tokens(text) if ts is None else ts
    values = [token for token, _ in ts]
    close = _matching(values)
    newlines = [match.start() for match in re.finditer("\n", text)]
    for index, value in enumerate(values):
        if value != "fn" or index + 1 >= len(ts) or not _IDENT.fullmatch(values[index + 1]):
            continue
        cursor = index + 2
        while cursor < len(ts) and values[cursor] not in ("{", ";"):
            cursor = close[cursor] + 1 if values[cursor] in ("[", "(") and cursor in close else cursor + 1
        if cursor not in close or values[cursor] != "{":
            continue
        end = close[cursor]
        body = values[cursor:end + 1]
        yield {"name": values[index + 1], "line": bisect.bisect_left(newlines, ts[index][1]) + 1,
               "start": ts[index][1], "end": ts[end][1] + 1, "tokens": len(body),
               "body_sha256": body_fingerprint(body),
               "identifiers_sha256": body_fingerprint(body, locals=_local_names(values[index:cursor], body))}

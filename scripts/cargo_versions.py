"""Cargo version requirements for the dependency coordination gate.

The parser is deliberately strict: unsupported or malformed input is an error,
never a compatible version. This module uses only the Python standard library.
Behavior reference:
https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html
"""

from __future__ import annotations

from dataclasses import dataclass
import re

__all__ = ["satisfies", "version_key"]

_NUMBER = r"(?:0|[1-9][0-9]*)"
_COMPONENT = rf"(?:{_NUMBER}|[xX*])"
_IDENTIFIERS = r"[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*"
_VERSION = re.compile(
    rf"(?P<core>{_COMPONENT}(?:\.{_COMPONENT}){{0,2}})"
    rf"(?:-(?P<pre>{_IDENTIFIERS}))?"
    rf"(?:\+(?P<build>{_IDENTIFIERS}))?"
)
_COMPARATOR = re.compile(r"(>=|<=|=|>|<|\^|~)? *(.*)")
_U64_MAX = (1 << 64) - 1
_WILDCARDS = {"*", "x", "X"}


@dataclass(frozen=True)
class _Version:
    numbers: tuple[int, ...]
    pre: tuple[str, ...]


@dataclass(frozen=True)
class _Comparator:
    operator: str
    version: _Version


def _parse_version(text: str, *, partial: bool = False) -> tuple[_Version, bool]:
    if not isinstance(text, str) or (match := _VERSION.fullmatch(text)) is None:
        raise ValueError(f"invalid Cargo version: {text!r}")
    components = match["core"].split(".")
    numbers: list[int] = []
    wildcard = False
    for component in components:
        if component in _WILDCARDS:
            wildcard = True
        elif wildcard:
            raise ValueError(f"number after wildcard in Cargo version: {text!r}")
        else:
            # The regex checks leading zeros and signs; Cargo bounds core numbers.
            if len(component) > 20 or int(component) > _U64_MAX:
                raise ValueError(f"Cargo version component exceeds u64: {text!r}")
            numbers.append(int(component))
    if not numbers or (not partial and (wildcard or len(numbers) != 3)):
        raise ValueError(f"invalid Cargo version: {text!r}")
    if (match["pre"] or match["build"]) and (wildcard or len(numbers) != 3):
        raise ValueError(f"Cargo metadata requires a full version: {text!r}")
    pre = tuple(match["pre"].split(".")) if match["pre"] else ()
    for identifier in pre:
        if identifier.isdecimal() and len(identifier) > 1 and identifier[0] == "0":
            raise ValueError(f"leading zero in Cargo prerelease: {text!r}")
    return _Version(tuple(numbers), pre), wildcard


def _parse_requirement(text: str) -> tuple[_Comparator, ...]:
    if not isinstance(text, str):
        raise ValueError(f"invalid Cargo requirement: {text!r}")
    # Cargo's grammar permits ASCII spaces around operators and commas.
    text = text.strip(" ")
    if text in _WILDCARDS:
        return ()
    parts = text.split(",")
    if len(parts) > 32:
        raise ValueError("Cargo requirements allow at most 32 comparators")
    result = []
    for part in parts:
        part = part.strip(" ")
        match = _COMPARATOR.fullmatch(part)
        if not part or match is None:
            raise ValueError(f"invalid Cargo requirement: {text!r}")
        operator, version = match.groups()
        parsed, wildcard = _parse_version(version, partial=True)
        # An implicit operator with a wildcard denotes a fixed numeric prefix;
        # an explicit operator retains its normal partial-version semantics.
        operator = operator or ("=" if wildcard else "^")
        result.append(_Comparator(operator, parsed))
    return tuple(result)


def _prerelease_key(pre: tuple[str, ...]) -> tuple:
    # A release sorts after every prerelease. Numeric identifiers sort before
    # text, numerically; lengths avoid converting unbounded identifiers to int.
    identifiers = tuple(
        (0, len(value), value) if value.isdecimal() else (1, 0, value)
        for value in pre
    )
    return (not pre, identifiers)


def version_key(text: str) -> tuple:
    """Compare full package versions using SemVer precedence (ignoring build metadata)."""
    version, _ = _parse_version(text)
    return version.numbers, _prerelease_key(version.pre)


def _matches(version: _Version, comparator: _Comparator) -> bool:
    required = comparator.version
    actual_numbers = version.numbers
    required_numbers = required.numbers
    precision = len(required_numbers)
    prefix = actual_numbers[:precision]
    exact = prefix == required_numbers and version.pre == required.pre
    operator = comparator.operator

    if operator == "=":
        return exact

    if operator in {">", ">=", "<", "<="}:
        if prefix != required_numbers:
            comparison = (prefix > required_numbers) - (prefix < required_numbers)
        elif precision == 3:
            actual_pre = _prerelease_key(version.pre)
            required_pre = _prerelease_key(required.pre)
            comparison = (actual_pre > required_pre) - (actual_pre < required_pre)
        else:
            # A strict partial comparison excludes the whole matching prefix.
            comparison = 0
        return {
            ">": comparison > 0,
            ">=": comparison > 0 or exact,
            "<": comparison < 0,
            "<=": comparison < 0 or exact,
        }[operator]

    if operator == "~":
        fixed = min(precision, 2)
        if actual_numbers[:fixed] != required_numbers[:fixed]:
            return False
        if precision == 3 and actual_numbers[2] != required_numbers[2]:
            return actual_numbers[2] > required_numbers[2]
        return _prerelease_key(version.pre) >= _prerelease_key(required.pre)

    # Caret requirements fix the left-most nonzero component. Missing minor
    # or patch numbers have their own Cargo semantics, including ^0 and ^0.0.
    if actual_numbers[0] != required_numbers[0]:
        return False
    if precision == 1:
        return True
    if precision == 2:
        if required_numbers[0] == 0:
            return actual_numbers[1] == required_numbers[1]
        return actual_numbers[1] >= required_numbers[1]
    fixed = next((i + 1 for i, value in enumerate(required_numbers) if value), 3)
    if actual_numbers[:fixed] != required_numbers[:fixed]:
        return False
    return (actual_numbers, _prerelease_key(version.pre)) >= (
        required_numbers, _prerelease_key(required.pre)
    )


def satisfies(version: str, requirement: str) -> bool:
    """Return whether a full version satisfies a Cargo version requirement.

    Accepts =, >, >=, <, <=, ~, ^, implicit caret, wildcards, and comma
    intersections. Build metadata is ignored. A prerelease needs an explicit
    prerelease comparator for its same major/minor/patch. Invalid syntax raises
    ValueError, even when another comparator already excludes the version.
    """
    parsed, _ = _parse_version(version)
    comparators = _parse_requirement(requirement)
    if not all(_matches(parsed, comparator) for comparator in comparators):
        return False
    return not parsed.pre or any(
        comparator.version.pre and comparator.version.numbers == parsed.numbers
        for comparator in comparators
    )

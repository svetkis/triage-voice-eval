"""Robust JSON parser for malformed LLM output."""

from __future__ import annotations

import json
import re


def parse(text: str, fallback: dict | None = None) -> tuple[dict, bool]:
    """Parse JSON from potentially malformed LLM output.

    Returns (parsed_dict, is_fallback).
    is_fallback=True means parsing failed and fallback was returned.

    Warning: when JSON is truncated (stage 4), string values may be
    incomplete. For safety-critical fields (e.g. ``advice``), a truncated
    non-empty string will appear truthy — which may cause guards like
    CrisisGuard to report LEAK on partial data. Callers should check
    is_fallback before trusting field values in safety decisions.
    """
    # Stage 1: direct parse
    result = _try_loads(text)
    if result is not None:
        return result, False

    # Stage 2: strip markdown fences
    stripped = _strip_markdown(text)
    if stripped is not None:
        result = _try_loads(stripped)
        if result is not None:
            return result, False

    # Stage 3: extract JSON object via bracket balancing
    extracted = _extract_json_object(text)
    if extracted is not None:
        result = _try_loads(extracted)
        if result is not None:
            return result, False

    # Stage 4: repair truncated JSON
    repaired = _repair_truncated(text)
    if repaired is not None:
        result = _try_loads(repaired)
        if result is not None:
            return result, False

    # Stage 5: fallback
    return fallback if fallback is not None else {}, True


def _try_loads(text: str) -> dict | None:
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except (json.JSONDecodeError, ValueError):
        pass
    return None


def _strip_markdown(text: str) -> str | None:
    m = re.search(r"```(?:json)?\s*\n(.*?)\n\s*```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return None


def _extract_json_object(text: str) -> str | None:
    """Find the first top-level JSON object using string-aware bracket balancing."""
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    i = start
    while i < len(text):
        ch = text[i]
        if in_string:
            if ch == "\\" and i + 1 < len(text):
                i += 2  # skip escaped char
                continue
            if ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        i += 1

    return None  # no matching close found


def _repair_truncated(text: str) -> str | None:
    """Attempt to repair truncated JSON by closing unclosed structures.

    Warning: repaired strings may contain incomplete values.
    E.g. ``"advice": "Call 911 imme`` becomes ``"advice": "Call 911 imme"``.
    The value is syntactically valid but semantically truncated.
    """
    start = text.find("{")
    if start == -1:
        return None

    fragment = text[start:]

    # Walk through tracking state
    in_string = False
    stack: list[str] = []  # tracks '{' and '['
    i = 0
    while i < len(fragment):
        ch = fragment[i]
        if in_string:
            if ch == "\\" and i + 1 < len(fragment):
                i += 2
                continue
            if ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                stack.append("{")
            elif ch == "[":
                stack.append("[")
            elif ch == "}":
                if stack and stack[-1] == "{":
                    stack.pop()
            elif ch == "]":
                if stack and stack[-1] == "[":
                    stack.pop()
        i += 1

    if not stack and not in_string:
        return None  # nothing to repair, and stage 3 already failed

    # Build closing sequence
    suffix = ""
    if in_string:
        suffix += '"'
    for bracket in reversed(stack):
        if bracket == "{":
            suffix += "}"
        else:
            suffix += "]"

    repaired = fragment + suffix
    return repaired

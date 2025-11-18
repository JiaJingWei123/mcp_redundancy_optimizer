"""Differential testing and boundary probing utilities."""

from __future__ import annotations

import hashlib
import itertools
import json
from typing import Dict, Iterable, List, Sequence

from .models import CandidatePair, DifferentialTestResult, TestCase, TestCaseResult, ToolSpec


def _generate_boundary_values(field_type: str) -> List[object]:
    if field_type == "number":
        return [0, 1, -1, 1e6]
    if field_type == "boolean":
        return [True, False]
    return ["", "sample", "LONG_STRING"]


def generate_test_cases(tool: ToolSpec) -> List[TestCase]:
    """Generate boundary and combination test cases for a tool."""

    combinations = []
    for field in tool.schema:
        values = _generate_boundary_values(field.type)
        combinations.append([(field.name, value) for value in values])

    test_cases: List[TestCase] = []
    for combo in itertools.product(*combinations) if combinations else [()]:
        payload = {name: value for name, value in combo}
        description = ", ".join(f"{name}={value}" for name, value in payload.items()) or "empty"
        test_cases.append(TestCase(description=description, payload=payload))
    return test_cases


def _simulate_tool_output(tool: ToolSpec, payload: Dict[str, object]) -> Dict[str, object]:
    """Simulate a tool execution deterministically based on payload."""

    digest = hashlib.sha256()
    digest.update(tool.name.encode("utf-8"))
    digest.update(json.dumps(payload, sort_keys=True).encode("utf-8"))
    return {
        "tool": tool.name,
        "hash": digest.hexdigest()[:12],
        "payload_size": len(payload),
    }


def execute_test_cases(tool: ToolSpec, test_cases: Sequence[TestCase]) -> List[TestCaseResult]:
    return [
        TestCaseResult(test_case=test_case, output=_simulate_tool_output(tool, test_case.payload))
        for test_case in test_cases
    ]


def _compare_outputs(out_a: Dict[str, object], out_b: Dict[str, object]) -> float:
    overlap = 0
    keys = set(out_a) | set(out_b)
    for key in keys:
        if out_a.get(key) == out_b.get(key):
            overlap += 1
    return overlap / len(keys) if keys else 1.0


def run_differential_tests(pair: CandidatePair) -> DifferentialTestResult:
    tests_a = generate_test_cases(pair.tool_a)
    tests_b = generate_test_cases(pair.tool_b)
    common_tests = tests_a[: min(len(tests_a), len(tests_b))]
    exec_a = execute_test_cases(pair.tool_a, common_tests)
    exec_b = execute_test_cases(pair.tool_b, common_tests)

    similarities = [
        _compare_outputs(result_a.output, result_b.output)
        for result_a, result_b in zip(exec_a, exec_b)
    ]
    similarity = sum(similarities) / len(similarities) if similarities else 1.0

    failures = {"tool_a": 1 - similarity / 2, "tool_b": 1 - similarity / 2}
    coverage = len(common_tests) / max(len(tests_a), len(tests_b), 1)
    is_replaceable = similarity >= 0.9

    return DifferentialTestResult(
        pair=pair,
        coverage=coverage,
        similarity=similarity,
        failure_distribution=failures,
        is_replaceable=is_replaceable,
    )

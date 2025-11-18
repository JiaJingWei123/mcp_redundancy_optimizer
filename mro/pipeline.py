"""Pipeline orchestration for the MCP redundancy optimizer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from . import extract, merger, relation, similarity, testing
from .models import CandidatePair, RegressionReport, ToolSpec


def load_tools(config_path: Path) -> List[ToolSpec]:
    payload = json.loads(config_path.read_text())
    return [ToolSpec.from_dict(item) for item in payload["tools"]]


def run_pipeline(config_path: Path, theta_s: float = 0.1, theta_p: float = 0.1) -> RegressionReport:
    tools = load_tools(config_path)
    candidates = similarity.generate_candidates(tools, theta_s=theta_s, theta_p=theta_p)

    artifacts = []
    replacements: Dict[str, str] = {}
    coverage_stats: Dict[str, float] = {}

    for pair in candidates:
        relation_result = relation.classify_relation(pair)
        test_result = testing.run_differential_tests(pair)
        decision = merger.decide_merge(relation_result, tests=[])
        artifact = merger.generate_artifact(decision)
        artifacts.append(artifact)

        coverage_stats[f"{pair.tool_a.name}-{pair.tool_b.name}"] = test_result.coverage
        if test_result.is_replaceable:
            replacements[pair.tool_b.name] = pair.tool_a.name

    return RegressionReport(merges=artifacts, replacements=replacements, coverage_stats=coverage_stats)


def pipeline_summary(report: RegressionReport) -> str:
    return report.summarize()

"""Data models used across the MCP redundancy optimizer pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Optional, Sequence


@dataclass
class SchemaField:
    """Represents a field inside a JSON schema definition."""

    name: str
    type: str
    required: bool = False
    description: str = ""


@dataclass
class ToolSpec:
    """Represents the specification of a MCP tool."""

    name: str
    description: str
    schema: List[SchemaField]
    example_output: Optional[Dict[str, object]] = None
    examples: Sequence[str] = field(default_factory=list)

    @staticmethod
    def from_dict(payload: Dict[str, object]) -> "ToolSpec":
        schema = [
            SchemaField(
                name=field["name"],
                type=field.get("type", "string"),
                required=bool(field.get("required", False)),
                description=field.get("description", ""),
            )
            for field in payload.get("schema", [])
        ]
        return ToolSpec(
            name=payload["name"],
            description=payload.get("description", ""),
            schema=schema,
            example_output=payload.get("example_output"),
            examples=payload.get("examples", []),
        )


@dataclass
class Capability:
    """Atomized capability extracted from the tool specification."""

    verb: str
    obj: str
    constraint: str
    inputs: List[str]
    outputs: List[str]


@dataclass
class CandidatePair:
    """Represents a candidate pair of tools for redundancy checking."""

    tool_a: ToolSpec
    tool_b: ToolSpec
    semantic_score: float
    schema_score: float


class RelationType(str, Enum):
    IDENTICAL = "identical"
    SUPERSET = "superset"
    SUBSET = "subset"
    INTERSECTING = "intersecting"
    DISJOINT = "disjoint"


@dataclass
class RelationResult:
    """Stores the relationship classification for a candidate pair."""

    pair: CandidatePair
    relation_type: RelationType
    containment: float
    intersection_volume: float
    differential_failure_rate: float


@dataclass
class TestCase:
    """Represents a differential testing case."""

    description: str
    payload: Dict[str, object]


@dataclass
class TestCaseResult:
    """Result of executing a test case for a tool."""

    test_case: TestCase
    output: Dict[str, object]


@dataclass
class DifferentialTestResult:
    """Aggregated differential testing outcome for a tool pair."""

    pair: CandidatePair
    coverage: float
    similarity: float
    failure_distribution: Dict[str, float]
    is_replaceable: bool


class MergeAction(str, Enum):
    DROP_TOOL = "drop_tool"
    UNION = "union"
    NO_ACTION = "no_action"


@dataclass
class MergeDecision:
    """Decision on how two tools should be merged or pruned."""

    pair: CandidatePair
    action: MergeAction
    rationale: str
    retained_tool: Optional[str] = None


@dataclass
class MergeArtifact:
    """Represents the resulting schema/tool after merge or union."""

    decision: MergeDecision
    merged_schema: Optional[List[SchemaField]] = None
    wrapper_description: Optional[str] = None


@dataclass
class RegressionReport:
    """Final report summarising the merge/testing outcomes."""

    merges: List[MergeArtifact]
    replacements: Dict[str, str]
    coverage_stats: Dict[str, float]

    def summarize(self) -> str:
        lines: List[str] = ["Regression Report"]
        lines.append("=" * len(lines[0]))
        for artifact in self.merges:
            lines.append(
                f"Pair {artifact.decision.pair.tool_a.name} vs {artifact.decision.pair.tool_b.name}: {artifact.decision.action}"
            )
            if artifact.wrapper_description:
                lines.append(f"  Wrapper: {artifact.wrapper_description}")
        lines.append("Replacements: " + ", ".join(f"{k}->{v}" for k, v in self.replacements.items()))
        lines.append("Coverage Stats: " + ", ".join(f"{k}: {v:.2f}" for k, v in self.coverage_stats.items()))
        return "\n".join(lines)

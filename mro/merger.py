"""Utilities for deciding and generating merge artifacts."""

from __future__ import annotations

from typing import List

from .models import (
    CandidatePair,
    MergeAction,
    MergeArtifact,
    MergeDecision,
    RelationResult,
    RelationType,
    SchemaField,
    ToolSpec,
)


def decide_merge(relation: RelationResult, tests: List[dict]) -> MergeDecision:
    pair = relation.pair
    if relation.relation_type == RelationType.IDENTICAL:
        retained = pair.tool_a.name
        rationale = "Identical tools; dropping duplicate."
        return MergeDecision(pair=pair, action=MergeAction.DROP_TOOL, rationale=rationale, retained_tool=retained)
    if relation.relation_type == RelationType.SUPERSET:
        retained = pair.tool_a.name
        rationale = "Tool A subsumes tool B based on containment heuristics."
        return MergeDecision(pair=pair, action=MergeAction.DROP_TOOL, rationale=rationale, retained_tool=retained)
    if relation.relation_type == RelationType.SUBSET:
        retained = pair.tool_b.name
        rationale = "Tool B subsumes tool A based on containment heuristics."
        return MergeDecision(pair=pair, action=MergeAction.DROP_TOOL, rationale=rationale, retained_tool=retained)
    if relation.relation_type == RelationType.INTERSECTING:
        rationale = "Intersecting capabilities; generate union schema with flags."
        return MergeDecision(pair=pair, action=MergeAction.UNION, rationale=rationale)
    return MergeDecision(pair=pair, action=MergeAction.NO_ACTION, rationale="Distinct tools; keep both.")


def _union_schema(tool_a: ToolSpec, tool_b: ToolSpec) -> List[SchemaField]:
    seen = {}
    for field in tool_a.schema + tool_b.schema:
        key = (field.name, field.type)
        if key not in seen:
            seen[key] = field
        else:
            seen_field = seen[key]
            seen[key] = SchemaField(
                name=field.name,
                type=field.type,
                required=seen_field.required and field.required,
                description=seen_field.description or field.description,
            )
    return list(seen.values())


def generate_artifact(decision: MergeDecision) -> MergeArtifact:
    pair = decision.pair
    if decision.action == MergeAction.UNION:
        merged_schema = _union_schema(pair.tool_a, pair.tool_b)
        description = (
            f"Wrapper tool exposing modes {{'use_{pair.tool_a.name}', 'use_{pair.tool_b.name}'}}"
        )
        return MergeArtifact(decision=decision, merged_schema=merged_schema, wrapper_description=description)
    if decision.action == MergeAction.DROP_TOOL:
        retained = decision.retained_tool or pair.tool_a.name
        description = f"Retain {retained}; remove the other tool from catalog."
        return MergeArtifact(decision=decision, wrapper_description=description)
    return MergeArtifact(decision=decision, wrapper_description="No merge action performed.")

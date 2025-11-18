"""Relation classification logic using geometric heuristics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .models import CandidatePair, RelationResult, RelationType


@dataclass
class BoxEmbedding:
    """A toy representation of a high-dimensional box embedding."""

    center: float
    radius: float

    def intersection_volume(self, other: "BoxEmbedding") -> float:
        distance = abs(self.center - other.center)
        overlap = max(0.0, self.radius + other.radius - distance)
        return min(1.0, overlap / (self.radius + other.radius + 1e-6))

    def containment(self, other: "BoxEmbedding") -> float:
        if self.radius == 0:
            return 0.0
        return min(1.0, other.radius / (self.radius + 1e-6))


def _build_box(pair: CandidatePair, use_first: bool) -> BoxEmbedding:
    score = pair.semantic_score if use_first else pair.schema_score
    center = score
    radius = max(0.05, 1 - score)
    return BoxEmbedding(center=center, radius=radius)


def classify_relation(pair: CandidatePair) -> RelationResult:
    box_a = _build_box(pair, True)
    box_b = _build_box(pair, False)
    intersection = box_a.intersection_volume(box_b)
    containment = box_a.containment(box_b)

    if pair.semantic_score >= 0.99 and pair.schema_score >= 0.99:
        relation = RelationType.IDENTICAL
    elif containment >= 0.75 and (1 - pair.schema_score) <= 0.05:
        relation = RelationType.SUPERSET
    elif containment >= 0.75:
        relation = RelationType.SUBSET
    elif 0.2 <= intersection <= 0.6 and pair.schema_score >= 0.5:
        relation = RelationType.INTERSECTING
    else:
        relation = RelationType.DISJOINT

    differential_failure_rate = max(0.0, 1 - pair.semantic_score)
    return RelationResult(
        pair=pair,
        relation_type=relation,
        containment=containment,
        intersection_volume=intersection,
        differential_failure_rate=differential_failure_rate,
    )

"""Candidate generation utilities based on semantic and schema similarity."""

from __future__ import annotations

from collections import Counter
from math import sqrt
from typing import Iterable, List, Sequence

from .models import CandidatePair, SchemaField, ToolSpec


STOP_WORDS = {"the", "a", "and", "of", "to", "is", "for", "with"}


def _tokenize(text: str) -> List[str]:
    return [word.lower() for word in text.split() if word.lower() not in STOP_WORDS]


def _cosine_similarity(text_a: str, text_b: str) -> float:
    tokens_a = Counter(_tokenize(text_a))
    tokens_b = Counter(_tokenize(text_b))
    numerator = sum(tokens_a[t] * tokens_b.get(t, 0) for t in tokens_a)
    denominator = sqrt(sum(v * v for v in tokens_a.values())) * sqrt(
        sum(v * v for v in tokens_b.values())
    )
    return numerator / denominator if denominator else 0.0


def _schema_signature(schema: Sequence[SchemaField]) -> set:
    signature = set()
    for field in schema:
        signature.add(f"{field.name}:{field.type}:{int(field.required)}")
        signature.add(f"type:{field.type}")
    return signature


def schema_similarity(tool_a: ToolSpec, tool_b: ToolSpec) -> float:
    sig_a = _schema_signature(tool_a.schema)
    sig_b = _schema_signature(tool_b.schema)
    if not sig_a and not sig_b:
        return 1.0
    intersection = len(sig_a & sig_b)
    union = len(sig_a | sig_b)
    return intersection / union if union else 0.0


def semantic_similarity(tool_a: ToolSpec, tool_b: ToolSpec) -> float:
    return _cosine_similarity(tool_a.description, tool_b.description)


def generate_candidates(
    tools: Sequence[ToolSpec], theta_s: float = 0.5, theta_p: float = 0.5
) -> List[CandidatePair]:
    candidates: List[CandidatePair] = []
    for i, tool_a in enumerate(tools):
        for tool_b in tools[i + 1 :]:
            sem = semantic_similarity(tool_a, tool_b)
            schema = schema_similarity(tool_a, tool_b)
            if sem >= theta_s and schema >= theta_p:
                candidates.append(
                    CandidatePair(
                        tool_a=tool_a,
                        tool_b=tool_b,
                        semantic_score=sem,
                        schema_score=schema,
                    )
                )
    return candidates

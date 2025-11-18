"""Capability extraction utilities."""

from __future__ import annotations

import re
from typing import Iterable, List

from .models import Capability, SchemaField, ToolSpec

VERB_PATTERN = re.compile(r"\b([a-z]+)\b", re.IGNORECASE)


def _find_candidate_words(text: str) -> List[str]:
    return [word.lower() for word in VERB_PATTERN.findall(text)]


def _guess_verb(words: List[str]) -> str:
    for word in words:
        if word.endswith("e") or word.endswith("y"):
            return word
    return words[0] if words else "process"


def _guess_object(words: List[str]) -> str:
    return "_".join(words[:2]) if len(words) >= 2 else (words[0] if words else "data")


def extract_capabilities(tool: ToolSpec) -> List[Capability]:
    """Extracts primitive capabilities from the tool description and schema."""

    words = _find_candidate_words(tool.description)
    verb = _guess_verb(words)
    obj = _guess_object(words)
    constraints = ", ".join(field.description for field in tool.schema if field.description)
    inputs = [field.name for field in tool.schema]
    outputs = list(tool.example_output.keys()) if tool.example_output else ["result"]

    capabilities = [
        Capability(
            verb=verb,
            obj=obj,
            constraint=constraints or "",
            inputs=inputs,
            outputs=outputs,
        )
    ]

    # Treat each schema field as a potential atomic capability as well.
    for field in tool.schema:
        capabilities.append(
            Capability(
                verb=f"handle_{field.name}",
                obj=field.type,
                constraint="required" if field.required else "optional",
                inputs=[field.name],
                outputs=[field.name],
            )
        )
    return capabilities


def summarize_capabilities(tools: Iterable[ToolSpec]) -> str:
    lines = ["Capability Summary"]
    for tool in tools:
        caps = extract_capabilities(tool)
        lines.append(f"- {tool.name}: {len(caps)} capabilities")
    return "\n".join(lines)

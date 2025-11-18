# MCP Redundancy Optimizer

This repository contains a runnable Python prototype that automates the workflow described in the prompt: extracting MCP tool capabilities, finding redundant or overlapping tools, testing them, and producing merge decisions.

## Features

1. **Capability Extraction** – `mro.extract` atomizes each tool specification into capabilities based on its description and schema.
2. **Candidate Generation** – `mro.similarity` calculates semantic (bag-of-words cosine) and schema (Jaccard) similarity to locate redundancy candidates.
3. **Relation Classification** – `mro.relation` mimics a box-embedding discriminator to understand whether tools are identical, subsets, supersets, intersecting, or disjoint.
4. **Differential Testing** – `mro.testing` creates boundary-value test cases and simulates MCP executions to evaluate coverage, similarity, and failure distributions.
5. **Merge Decisions** – `mro.merger` applies the rules to drop duplicates, union intersecting tools, or keep distinct tools while generating wrapper schemas.
6. **Pipeline + Reporting** – `mro.pipeline` orchestrates the pipeline and emits a regression report with merge artifacts and replacement statistics.

## Project Layout

```
main.py                 # CLI entry
mro/                    # Package containing pipeline modules
sample_tools.json       # Example tool catalog for demo runs
```

## Usage

1. (Optional) Create a virtual environment with Python 3.11+.
2. Run the demo using the provided sample file:

```bash
python main.py sample_tools.json
```

3. Customize `sample_tools.json` (or provide your own file) with MCP tool specs. Each tool entry must include:

```json
{
  "name": "tool_name",
  "description": "textual description",
  "schema": [{"name": "field", "type": "string", "required": true, "description": "..."}],
  "example_output": {"key": "value"}
}
```

4. Tune thresholds if needed:

```bash
python main.py sample_tools.json --theta-s 0.5 --theta-p 0.6
```

The CLI will print a regression report summarizing candidate merges, replacements, and coverage stats.

## Extending the Prototype

- Replace the simple bag-of-words model with FAISS/Milvus embeddings.
- Plug actual MCP invocations inside `mro.testing._simulate_tool_output`.
- Train a real box embedding classifier and update `mro.relation`.
- Export the regression report as JSON or HTML for downstream review.
## Repository Status

All modules described above (CLI entry point, `mro` package, and sample catalog) are now committed to this repository so that the project can be cloned or forked directly without any additional setup.

"""CLI entry point for the MCP redundancy optimizer demo project."""

from __future__ import annotations

import argparse
from pathlib import Path

from mro import pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the MCP redundancy optimization pipeline")
    parser.add_argument(
        "config",
        type=Path,
        help="Path to a JSON file containing the tool catalog specification.",
    )
    parser.add_argument("--theta-s", type=float, default=0.1, help="Semantic similarity threshold")
    parser.add_argument("--theta-p", type=float, default=0.1, help="Schema similarity threshold")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = pipeline.run_pipeline(args.config, theta_s=args.theta_s, theta_p=args.theta_p)
    print(pipeline.pipeline_summary(report))


if __name__ == "__main__":
    main()

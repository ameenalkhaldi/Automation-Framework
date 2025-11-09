"""Entry point for running the multi-agent automation framework."""

from __future__ import annotations

import argparse
import ast
import operator
import os
import sys
from pathlib import Path
from typing import Iterable, List

from Agents import CoordinatorAgent, ExecutorAgent, PlannerAgent, ReviewerAgent
from skills import SkillRegistry
from utils import initialise_log_file
from workflow import AutomationWorkflow, Task


def load_tasks(task_file: Path) -> List[Task]:
    if not task_file.exists():
        raise FileNotFoundError(f"Task file '{task_file}' does not exist.")

    import json

    raw_tasks = json.loads(task_file.read_text())

    tasks: List[Task] = []
    for item in raw_tasks:
        tasks.append(
            Task(
                name=item["name"],
                objective=item["objective"],
                context=item.get("context"),
                deliverable=item.get("deliverable"),
                constraints=item.get("constraints"),
            )
        )
    return tasks


def build_skill_registry() -> SkillRegistry:
    registry = SkillRegistry()

    # A safe arithmetic evaluator inspired by AutoGen's calculator tools.
    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
    }

    def evaluate_math(expression: str) -> str:
        """Safely evaluate a simple arithmetic expression."""

        def _eval(node: ast.AST) -> float:
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            if isinstance(node, ast.BinOp) and type(node.op) in allowed_operators:
                return allowed_operators[type(node.op)](_eval(node.left), _eval(node.right))
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                value = _eval(node.operand)
                return value if isinstance(node.op, ast.UAdd) else -value
            if isinstance(node, ast.Num):  # pragma: no cover - Python <3.8 compat
                return float(node.n)
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return float(node.value)
            raise ValueError("Unsupported expression")

        tree = ast.parse(expression, mode="eval")
        result = _eval(tree)
        return str(result)

    registry.register(
        "evaluate_math",
        evaluate_math,
        "Safely evaluate arithmetic expressions containing +, -, *, /, %, and **.",
    )

    return registry


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the automation workflow.")
    parser.add_argument(
        "--tasks",
        type=Path,
        default=Path("tasks/example_tasks.json"),
        help="Path to a JSON file describing the tasks to execute.",
    )
    parser.add_argument(
        "--run-name",
        default="automation-run",
        help="Name used when creating log files and reports.",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=Path("reports"),
        help="Directory where Markdown reports will be stored.",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv or sys.argv[1:])

    tasks = load_tasks(args.tasks)
    if not tasks:
        print("No tasks defined in the provided task file.")
        return

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Provide a valid key to run the automation workflow."
        )

    log_file_path = initialise_log_file(args.run_name)
    skill_registry = build_skill_registry()

    planner = PlannerAgent(api_key=api_key)
    reviewer = ReviewerAgent(api_key=api_key)
    coordinator = CoordinatorAgent(api_key=api_key)
    executor = ExecutorAgent(skill_registry, api_key=api_key)

    workflow = AutomationWorkflow(
        planner,
        executor,
        reviewer,
        coordinator=coordinator,
        log_file_path=log_file_path,
        reports_dir=args.reports_dir,
    )

    workflow.run_all(tasks)
    print(f"Completed automation run. Reports saved to {args.reports_dir.resolve()}")


if __name__ == "__main__":
    main()

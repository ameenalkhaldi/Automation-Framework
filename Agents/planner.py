"""Planner agent responsible for decomposing tasks into executable steps."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, TYPE_CHECKING

from agent import Agent

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from workflow import Task


class PlannerAgent(Agent):
    """Creates high-level strategies for automation tasks."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini") -> None:
        system_prompt = (
            "You are the Planner, an expert workflow designer that specialises in "
            "breaking down complex objectives into concrete, automation-friendly "
            "steps. Your plans must be explicit, justified, and resilient to "
            "ambiguity. Output valid JSON with a top-level object containing the "
            "keys: 'plan_overview', 'assumptions', and 'steps'. Each item in the "
            "'steps' array must include 'id', 'description', 'rationale', and "
            "'success_criteria'. Prefer short identifiers such as 'step-1'."
        )
        super().__init__(
            name="Planner",
            role="Workflow strategist",
            system_prompt=system_prompt,
            api_key=api_key,
            model=model,
        )

    def propose_plan(
        self,
        task: "Task",
        *,
        feedback: Optional[str] = None,
        previous_plan: Optional[Dict[str, Any]] = None,
        log_file_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a plan for ``task`` incorporating ``feedback`` if provided."""

        conversation_id = f"plan::{task.name}"
        user_message = (
            f"Task name: {task.name}\n"
            f"Objective: {task.objective}\n"
            f"Context: {task.context or 'N/A'}\n"
        )
        if task.constraints:
            user_message += "Constraints:\n" + "\n".join(f"- {item}" for item in task.constraints) + "\n"
        if task.deliverable:
            user_message += f"Deliverable expectation: {task.deliverable}\n"
        if previous_plan:
            user_message += (
                "\nHere is the previous plan attempt that requires revision:\n"
                f"{json.dumps(previous_plan, indent=2)}\n"
            )
        if feedback:
            user_message += f"\nReviewer feedback to address:\n{feedback}\n"

        user_message += (
            "\nRespond strictly in JSON. Ensure the steps are ordered and ready for "
            "automation without manual glue code."
        )

        response = self.generate_response(
            conversation_id,
            user_message,
            response_format={"type": "json_object"},
        )
        self.log(response, log_file_path)
        return json.loads(response)

"""Reviewer agent that validates plans and execution outputs."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Optional, TYPE_CHECKING

from agent import Agent

if TYPE_CHECKING:  # pragma: no cover - import for typing only
    from workflow import StepResult, Task


class ReviewerAgent(Agent):
    """Ensures quality control throughout the automation workflow."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini") -> None:
        system_prompt = (
            "You are the Reviewer, a meticulous QA specialist. Your job is to "
            "stress test plans and execution artefacts. Return JSON objects with "
            "clear approvals, actionable feedback, and a confidence rating."
        )
        super().__init__(
            name="Reviewer",
            role="Quality assurance lead",
            system_prompt=system_prompt,
            api_key=api_key,
            model=model,
        )

    def review_plan(
        self,
        task: "Task",
        plan: Dict[str, Any],
        *,
        iteration: int,
        log_file_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        conversation_id = f"plan-review::{task.name}"
        user_message = (
            f"Task objective: {task.objective}\n"
            f"Review iteration: {iteration}\n"
            f"Proposed plan:\n{json.dumps(plan, indent=2)}\n"
            "\nRespond in JSON with keys 'approved' (boolean), 'feedback', and "
            "'confidence'. Be candid but constructive."
        )
        response = self.generate_response(
            conversation_id,
            user_message,
            response_format={"type": "json_object"},
        )
        self.log(response, log_file_path)
        return json.loads(response)

    def review_step(
        self,
        task: "Task",
        step: Dict[str, Any],
        result: Dict[str, Any],
        *,
        attempt: int,
        log_file_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        conversation_id = f"step-review::{task.name}::{step.get('id', 'unknown')}"
        user_message = (
            f"Task objective: {task.objective}\n"
            f"Step metadata: {json.dumps(step, indent=2)}\n"
            f"Attempt: {attempt}\n"
            f"Execution result: {json.dumps(result, indent=2)}\n"
            "\nProvide a JSON object with keys 'approved' (boolean), 'feedback', "
            "'requires_replan' (boolean), and 'quality' (one of ['high','medium','low'])."
        )
        response = self.generate_response(
            conversation_id,
            user_message,
            response_format={"type": "json_object"},
        )
        self.log(response, log_file_path)
        return json.loads(response)

    def final_review(
        self,
        task: "Task",
        plan: Dict[str, Any],
        results: Iterable["StepResult"],
        *,
        log_file_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        conversation_id = f"final-review::{task.name}"
        serialised_results = [result.to_dict() for result in results]
        user_message = (
            f"Task objective: {task.objective}\n"
            f"Approved plan summary:\n{json.dumps(plan, indent=2)}\n"
            f"Execution timeline: {json.dumps(serialised_results, indent=2)}\n"
            "\nReturn JSON with keys 'approved', 'feedback', 'highlights', and 'risks'."
        )
        response = self.generate_response(
            conversation_id,
            user_message,
            response_format={"type": "json_object"},
        )
        self.log(response, log_file_path)
        return json.loads(response)

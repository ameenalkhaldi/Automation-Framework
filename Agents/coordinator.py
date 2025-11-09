"""Coordinator agent that keeps the conversation on track."""

from __future__ import annotations

from typing import Iterable, Optional, TYPE_CHECKING

from agent import Agent

if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from workflow import StepResult, Task


class CoordinatorAgent(Agent):
    """Provides high-level guidance and synthesises outcomes."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini") -> None:
        system_prompt = (
            "You are the Coordinator, responsible for facilitating collaboration "
            "between specialist agents. Provide concise briefings and syntheses in "
            "clear Markdown."
        )
        super().__init__(
            name="Coordinator",
            role="Orchestration lead",
            system_prompt=system_prompt,
            api_key=api_key,
            model=model,
        )

    def kickoff_task(self, task: "Task", *, log_file_path: Optional[str] = None) -> str:
        conversation_id = f"coord::{task.name}"
        message = (
            f"Provide a short kickoff note for the task '{task.name}'.\n"
            f"Objective: {task.objective}\n"
            f"Context: {task.context or 'N/A'}\n"
            "State the initial focus areas in Markdown bullet points."
        )
        response = self.generate_response(conversation_id, message)
        self.log(response, log_file_path)
        return response

    def synthesise_outcome(
        self,
        task: "Task",
        plan: dict,
        results: Iterable["StepResult"],
        reviewer_summary: dict,
        *,
        log_file_path: Optional[str] = None,
    ) -> str:
        conversation_id = f"coord-summary::{task.name}"
        timeline = "\n".join(
            f"- {result.step_id}: {result.output.get('summary', 'No summary available')}"
            for result in results
        ) or "No executed steps recorded."
        message = (
            f"Craft a concise Markdown summary for the task '{task.name}'.\n"
            f"Objective: {task.objective}\n"
            f"Approved plan overview: {plan.get('plan_overview', 'N/A')}\n"
            f"Execution timeline:\n{timeline}\n"
            f"Reviewer verdict: {reviewer_summary.get('feedback', 'N/A')}\n"
            "Highlight completed deliverables and recommended next actions."
        )
        response = self.generate_response(conversation_id, message)
        self.log(response, log_file_path)
        return response

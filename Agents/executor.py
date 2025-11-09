"""Executor agent that carries out plan steps and can trigger skills."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional, TYPE_CHECKING

from agent import Agent
from skills import SkillRegistry

if TYPE_CHECKING:  # pragma: no cover - import for typing only
    from workflow import StepResult, Task


class ExecutorAgent(Agent):
    """Executes the planner's steps while leveraging registered skills."""

    def __init__(
        self,
        skill_registry: SkillRegistry,
        *,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        max_skill_invocations: int = 3,
    ) -> None:
        system_prompt = (
            "You are the Executor, a doer who converts plans into tangible results. "
            "You may call external skills to speed up execution. When responding, "
            "use JSON with keys: 'summary', 'artifacts' (array of strings), "
            "'action' (optional object with 'skill' and 'arguments'), and "
            "'notes'. If you no longer need to call a skill, omit the 'action' key."
        )
        super().__init__(
            name="Executor",
            role="Implementation specialist",
            system_prompt=system_prompt,
            api_key=api_key,
            model=model,
        )
        self.skill_registry = skill_registry
        self.max_skill_invocations = max_skill_invocations

    def _summarise_previous_results(self, results: Iterable["StepResult"]) -> str:
        summaries: List[str] = []
        for result in results:
            summaries.append(
                f"- {result.step_id}: {result.output.get('summary', 'No summary provided')}"
            )
        return "\n".join(summaries) if summaries else "None yet."

    def execute_step(
        self,
        task: "Task",
        step: Dict[str, Any],
        *,
        prior_results: Iterable["StepResult"],
        feedback: Optional[str] = None,
        log_file_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        conversation_id = f"execute::{task.name}::{step.get('id', 'unknown')}"
        base_message = (
            f"Task objective: {task.objective}\n"
            f"Current step: {json.dumps(step, indent=2)}\n"
            f"Progress so far:\n{self._summarise_previous_results(prior_results)}\n"
            f"Available skills:\n{self.skill_registry.to_prompt_fragment()}\n"
            "Respond in JSON as documented."
        )
        if task.deliverable:
            base_message += f"\nTarget deliverable: {task.deliverable}"
        if feedback:
            base_message += f"\nIncorporate reviewer feedback: {feedback}"

        pending_message = base_message
        invocations = 0
        while True:
            response = self.generate_response(
                conversation_id,
                pending_message,
                response_format={"type": "json_object"},
            )
            self.log(response, log_file_path)
            parsed_response = json.loads(response)

            action = parsed_response.get("action") or {}
            skill_name = action.get("skill") if isinstance(action, dict) else None
            if skill_name and invocations < self.max_skill_invocations:
                arguments = action.get("arguments", {}) if isinstance(action, dict) else {}
                try:
                    skill_output = self.skill_registry.execute(skill_name, **arguments)
                    feedback_message = (
                        f"Skill `{skill_name}` executed successfully with arguments {arguments}.\n"
                        f"Result:\n{skill_output}\n"
                        "Provide an updated JSON response. If further tooling is required, "
                        "specify another action; otherwise omit the action field."
                    )
                except Exception as exc:  # pragma: no cover - defensive logging
                    feedback_message = (
                        f"Skill `{skill_name}` raised an exception: {exc}.\n"
                        "Re-evaluate and either fix the request or continue without the skill."
                    )
                invocations += 1
                pending_message = feedback_message
                continue

            return parsed_response

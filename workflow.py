"""Workflow orchestration utilities for the automation framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from Agents import CoordinatorAgent, ExecutorAgent, PlannerAgent, ReviewerAgent


@dataclass
class Task:
    """Represents a user-defined automation task."""

    name: str
    objective: str
    context: Optional[str] = None
    deliverable: Optional[str] = None
    constraints: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "objective": self.objective,
            "context": self.context,
            "deliverable": self.deliverable,
            "constraints": self.constraints or [],
        }


@dataclass
class StepResult:
    """Captures the outcome of a single execution attempt."""

    step_id: str
    step: Dict[str, Any]
    output: Dict[str, Any]
    review: Dict[str, Any]
    attempt: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "attempt": self.attempt,
            "step": self.step,
            "output": self.output,
            "review": self.review,
        }


@dataclass
class TaskRunResult:
    """Aggregated information for a completed task run."""

    task: Task
    plan: Dict[str, Any]
    step_results: List[StepResult] = field(default_factory=list)
    reviewer_summary: Dict[str, Any] = field(default_factory=dict)
    coordinator_summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task.to_dict(),
            "plan": self.plan,
            "step_results": [result.to_dict() for result in self.step_results],
            "reviewer_summary": self.reviewer_summary,
            "coordinator_summary": self.coordinator_summary,
        }

    def to_markdown(self) -> str:
        lines = [
            f"# Task Report: {self.task.name}",
            "",
            f"**Objective:** {self.task.objective}",
        ]
        if self.task.context:
            lines.append(f"**Context:** {self.task.context}")
        if self.task.deliverable:
            lines.append(f"**Expected Deliverable:** {self.task.deliverable}")
        lines.extend(["", "## Plan Overview", self.plan.get("plan_overview", "No overview provided."), ""])

        lines.append("## Execution Timeline")
        if not self.step_results:
            lines.append("No steps were executed.")
        else:
            for result in self.step_results:
                status = "Approved" if result.review.get("approved") else "Pending"
                lines.append(f"- **{result.step_id}** (attempt {result.attempt}, {status}): {result.output.get('summary', 'No summary available')}")
        lines.append("")

        lines.append("## Reviewer Verdict")
        lines.append(self.reviewer_summary.get("feedback", "No reviewer feedback recorded."))
        lines.append("")

        if self.coordinator_summary:
            lines.append("## Coordinator Summary")
            lines.append(self.coordinator_summary)
            lines.append("")

        return "\n".join(lines)


class AutomationWorkflow:
    """Coordinates planner, executor, reviewer, and coordinator agents."""

    def __init__(
        self,
        planner: PlannerAgent,
        executor: ExecutorAgent,
        reviewer: ReviewerAgent,
        *,
        coordinator: Optional[CoordinatorAgent] = None,
        log_file_path: Optional[str] = None,
        reports_dir: Path = Path("reports"),
        max_plan_iterations: int = 3,
        max_step_iterations: int = 3,
        max_replan_attempts: int = 2,
    ) -> None:
        self.planner = planner
        self.executor = executor
        self.reviewer = reviewer
        self.coordinator = coordinator
        self.log_file_path = log_file_path
        self.max_plan_iterations = max_plan_iterations
        self.max_step_iterations = max_step_iterations
        self.max_replan_attempts = max_replan_attempts
        self.reports_dir = reports_dir
        self.reports_dir.mkdir(exist_ok=True)

    def run_all(self, tasks: Iterable[Task]) -> List[TaskRunResult]:
        results: List[TaskRunResult] = []
        for task in tasks:
            result = self.run_task(task)
            results.append(result)
        return results

    def run_task(self, task: Task) -> TaskRunResult:
        if self.coordinator:
            self.coordinator.kickoff_task(task, log_file_path=self.log_file_path)

        previous_plan: Optional[Dict[str, Any]] = None
        feedback: Optional[str] = None
        plan_attempt = 0

        while plan_attempt < self.max_plan_iterations:
            plan_attempt += 1
            plan = self.planner.propose_plan(
                task,
                feedback=feedback,
                previous_plan=previous_plan,
                log_file_path=self.log_file_path,
            )
            plan_review = self.reviewer.review_plan(
                task,
                plan,
                iteration=plan_attempt,
                log_file_path=self.log_file_path,
            )
            if not plan_review.get("approved"):
                feedback = plan_review.get("feedback")
                previous_plan = plan
                continue

            replan_attempts = 0
            while True:
                run_result, execution_feedback = self._execute_plan(task, plan)
                if run_result is not None:
                    return run_result

                replan_attempts += 1
                if replan_attempts > self.max_replan_attempts:
                    raise RuntimeError(
                        f"Exceeded maximum execution replans for task '{task.name}'."
                    )

                feedback = execution_feedback or "Reviewer requested a re-plan during execution."
                previous_plan = plan
                break

        raise RuntimeError(f"Exceeded maximum plan attempts for task '{task.name}'.")

    # ------------------------------------------------------------------
    def _execute_plan(self, task: Task, plan: Dict[str, Any]) -> Tuple[Optional[TaskRunResult], Optional[str]]:
        steps = plan.get("steps") or []
        if not isinstance(steps, list):
            raise ValueError("Planner response must contain a 'steps' array.")

        all_results: List[StepResult] = []
        approved_results: List[StepResult] = []

        for index, raw_step in enumerate(steps, start=1):
            step = dict(raw_step)
            step.setdefault("id", f"step-{index}")
            require_replan = False
            attempt_feedback: Optional[str] = None
            step_attempts: List[StepResult] = []

            for attempt in range(1, self.max_step_iterations + 1):
                execution_output = self.executor.execute_step(
                    task,
                    step,
                    prior_results=approved_results,
                    feedback=attempt_feedback,
                    log_file_path=self.log_file_path,
                )
                step_review = self.reviewer.review_step(
                    task,
                    step,
                    execution_output,
                    attempt=attempt,
                    log_file_path=self.log_file_path,
                )
                step_result = StepResult(
                    step_id=step["id"],
                    step=step,
                    output=execution_output,
                    review=step_review,
                    attempt=attempt,
                )
                step_attempts.append(step_result)

                if step_review.get("approved"):
                    approved_results.append(step_result)
                    break

                if step_review.get("requires_replan"):
                    require_replan = True
                    break

                attempt_feedback = step_review.get("feedback")

            all_results.extend(step_attempts)

            if require_replan:
                feedback = step_attempts[-1].review.get("feedback") if step_attempts else None
                return None, feedback

            if not step_attempts or not step_attempts[-1].review.get("approved"):
                raise RuntimeError(
                    f"Step '{step['id']}' was not approved after {self.max_step_iterations} attempts."
                )

        reviewer_summary = self.reviewer.final_review(
            task,
            plan,
            all_results,
            log_file_path=self.log_file_path,
        )

        coordinator_summary: Optional[str] = None
        if self.coordinator:
            coordinator_summary = self.coordinator.synthesise_outcome(
                task,
                plan,
                all_results,
                reviewer_summary,
                log_file_path=self.log_file_path,
            )

        result = TaskRunResult(
            task=task,
            plan=plan,
            step_results=all_results,
            reviewer_summary=reviewer_summary,
            coordinator_summary=coordinator_summary,
        )
        self._write_report(result)
        return result, None

    def _write_report(self, result: TaskRunResult) -> None:
        safe_name = "".join(
            char.lower() if char.isalnum() or char in {"-", "_"} else "-"
            for char in result.task.name
        ).strip("-")
        if not safe_name:
            safe_name = "task"
        report_path = self.reports_dir / f"{safe_name}.md"
        report_path.write_text(result.to_markdown())


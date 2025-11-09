# Multi-Agent Automation Framework

This project transforms the original penetration-testing prototype into a **general-purpose, multi-agent automation framework**. Specialists powered by large language models collaborate to plan, execute, review, and report on arbitrary tasks ranging from marketing research to internal process optimisation. The orchestration pattern draws inspiration from systems such as [Microsoft AutoGen](https://github.com/microsoft/autogen) while remaining lightweight and easy to customise.

> **Important:** Running the framework requires an OpenAI API key. All examples below assume the key is available through the `OPENAI_API_KEY` environment variable.

## Key Capabilities

- **Task-centric workflows** – supply one or many tasks via JSON. Each task specifies objectives, optional context, constraints, and desired deliverables.
- **Conversational planning loop** – a Planner agent decomposes the objective, a Reviewer critiques each proposal, and replanning occurs automatically until approval.
- **Iterative execution** – an Executor agent follows the approved plan step-by-step. After every attempt the Reviewer can accept the result, request revisions, or trigger a full replanning cycle.
- **Skill registry** – inspired by AutoGen tool-calling, the Executor can invoke registered Python “skills” (e.g., a safe math evaluator) to accelerate work. Custom skills are simple functions annotated with descriptions and automatically surfaced to the model.
- **Coordinator synthesis** – a Coordinator agent introduces tasks and compiles Markdown summaries for stakeholders.
- **Structured logging and reporting** – every run creates a JSON log under `logs/` and an artefact report for each task under `reports/`.

## Architecture Overview

| Component | Responsibility |
| --- | --- |
| `PlannerAgent` | Breaks an objective into automation-ready steps with rationale and success criteria. |
| `ExecutorAgent` | Executes steps, optionally calling skills, and produces artefacts for review. |
| `ReviewerAgent` | Performs quality control on plans, step results, and the final output. |
| `CoordinatorAgent` | Provides kickoff notes and synthesises the overall outcome in Markdown. |
| `SkillRegistry` | Registers callable tools that agents can request, similar to AutoGen skills. |
| `AutomationWorkflow` | Coordinates task progression, replanning, and report generation. |

The agents maintain individual conversation histories so they can reference prior context without external state management. Replanning and re-execution loops are bounded to avoid infinite conversations, yet flexible enough to incorporate Reviewer feedback at any stage.

## Comparison with Microsoft AutoGen

| AutoGen Concept | This Framework |
| --- | --- |
| **Conversational agents** | Planner, Executor, Reviewer, and Coordinator maintain independent dialogues with persistent memory. |
| **Tool/skill invocation** | `SkillRegistry` exposes Python callables to the Executor, mirroring AutoGen’s tool-calling pattern. |
| **Group chat orchestration** | `AutomationWorkflow` sequences plan → review → execute loops, automatically requesting replans when the Reviewer rejects a step. |
| **Human-readable summaries** | The Coordinator produces Markdown reports akin to AutoGen’s conversation summaries. |
| **Extensibility** | Add new agents or skills by subclassing `Agent` or registering additional tools—no core refactor required. |

While AutoGen offers a vast ecosystem, this repository focuses on an approachable core that you can extend or embed inside larger automation stacks.

## Getting Started

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *(Provide your own dependency list—at minimum `openai` and `colorama` are required.)*

2. **Configure credentials**
   ```bash
   export OPENAI_API_KEY="sk-your-key"
   ```

3. **Review or edit tasks** – Tasks live under `tasks/` and follow this structure:
   ```json
   {
     "name": "Marketing blog outline",
     "objective": "Draft a blog post outline...",
     "context": "Target operations teams...",
     "deliverable": "A Markdown outline...",
     "constraints": ["No more than seven sections", "Compare with single-agent approaches"]
   }
   ```

4. **Run the workflow**
   ```bash
   python main.py --tasks tasks/example_tasks.json --run-name demo-run
   ```

   The script prints progress, stores a JSON trace in `logs/`, and generates Markdown reports inside `reports/`.

## Logs and Reports

- **Logs** (`logs/<run-name>-<timestamp>.json`) capture every agent message for auditing or analysis.
- **Reports** (`reports/<task-name>.md`) consolidate the approved plan, execution timeline, reviewer verdict, and coordinator summary for each task.

## Extending the Framework

- **Add custom skills** by registering new functions in `build_skill_registry()` within `main.py`, or expose a registry in your own entry point. Provide descriptive docstrings and type-safe signatures so the Executor knows how to call them.
- **Create specialised agents** by subclassing `Agent` in `agent.py` and crafting role-specific prompts. Plug them into `AutomationWorkflow` to experiment with new collaboration styles (e.g., researcher agents, data critics, domain experts).
- **Integrate with other systems** by modifying `ExecutorAgent.execute_step` to call external APIs, trigger CI pipelines, or run local tooling before returning results to the Reviewer.

## Sample Output

A condensed example illustrating the interplay between agents can be found in [`SampleRun.md`](SampleRun.md). It showcases:

- JSON planning output from the Planner
- Reviewer critique followed by an approved revision
- An Executor step that invokes the math skill
- The final Markdown summary crafted by the Coordinator

## Roadmap Ideas

- Support for non-OpenAI model providers via a pluggable client layer
- Additional built-in skills (file system access, HTTP requests, knowledge-base retrieval)
- Conversational dashboards to monitor agent discussions in real time

## License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for details.

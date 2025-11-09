# Sample Workflow Walkthrough

This illustrative run demonstrates how the redesigned framework coordinates agents to complete a generic automation task. The interaction is abridged for clarity—the actual JSON logs in `logs/` capture the full transcripts.

## 1. Task Definition

```json
{
  "name": "Marketing blog outline",
  "objective": "Draft a blog post outline explaining how multi-agent automation accelerates business workflows.",
  "context": "Target operations teams at fast-growing startups and emphasise collaboration between planner, executor, and reviewer personas.",
  "deliverable": "A Markdown outline with sections and bullet points ready for content writers.",
  "constraints": [
    "Limit the outline to no more than seven major sections.",
    "Highlight at least one comparison with traditional single-agent approaches."
  ]
}
```

## 2. Planning Loop

**Planner**
```json
{
  "plan_overview": "Develop a concise outline that introduces multi-agent automation, compares it with single-agent workflows, and closes with actionable guidance for operations teams.",
  "assumptions": ["Readers have baseline familiarity with automation", "No proprietary metrics are required"],
  "steps": [
    {
      "id": "step-1",
      "description": "Research key benefits and challenges of multi-agent automation for operations teams.",
      "rationale": "Ground the outline in credible talking points before drafting.",
      "success_criteria": "List at least three benefits and two risks relevant to operations teams."
    },
    {
      "id": "step-2",
      "description": "Draft a Markdown outline with introduction, comparison, use-cases, and closing call-to-action.",
      "rationale": "Translate the research into a structured outline matching the deliverable requirements.",
      "success_criteria": "No more than seven top-level sections and at least one explicit comparison with single-agent flows."
    }
  ]
}
```

**Reviewer (iteration 1)**
```json
{
  "approved": false,
  "feedback": "Clarify that the comparison section should include measurable advantages (speed or quality).",
  "confidence": "medium"
}
```

**Planner Revision**
```json
{
  "plan_overview": "Augment the outline with quantified advantages of multi-agent automation and ensure stakeholder-ready framing.",
  "assumptions": ["Readers value measurable outcomes", "LLM agents can access internal skills"],
  "steps": [
    {
      "id": "step-1",
      "description": "Collect measurable benefits (e.g., cycle time reductions) and typical pitfalls of multi-agent automation in operations settings.",
      "rationale": "Provide quantified talking points for the comparison section.",
      "success_criteria": "At least three metrics or qualitative proxies with brief sources."
    },
    {
      "id": "step-2",
      "description": "Produce the final Markdown outline incorporating the metrics and highlighting collaboration patterns.",
      "rationale": "Deliver the requested asset in publication-ready form.",
      "success_criteria": "≤7 headings, explicit comparison paragraph, actionable closing section."
    }
  ]
}
```

**Reviewer (iteration 2)** – approved with confidence "high".

## 3. Execution & Skill Usage

**Executor – Step 1**
```json
{
  "summary": "Compiled metrics showing that multi-agent orchestration cuts analysis time by 30–45% and reduces review iterations by ~25%.",
  "artifacts": [
    "Benefit table referencing recent industry reports",
    "Risk list covering governance and data-quality considerations"
  ],
  "action": {
    "skill": "evaluate_math",
    "arguments": {"expression": "0.45 - 0.25"}
  },
  "notes": "Invoking calculator skill to quantify improvement delta for the comparison section."
}
```

**Skill execution feedback**
```
Skill `evaluate_math` executed successfully with arguments {'expression': '0.45 - 0.25'}.
Result:
0.2
```

**Executor follow-up**
```json
{
  "summary": "Updated comparison metrics to emphasise a 20% improvement gap between collaboration styles.",
  "artifacts": [
    "Refined metric table",
    "Context paragraph ready for inclusion in the outline"
  ],
  "notes": "Ready for reviewer validation.",
  "action": null
}
```

**Reviewer feedback**
```json
{
  "approved": true,
  "feedback": "Metrics are credible and align with the outlined success criteria.",
  "requires_replan": false,
  "quality": "high"
}
```

Step 2 proceeds similarly, culminating in an approved Markdown outline.

## 4. Coordinator Summary

```markdown
## Automation Campaign Outline
- Objective: Educate operations leaders on multi-agent automation
- Highlights: 20% faster iteration cycles, governance guardrails, rapid experimentation playbooks
- Next Steps: Package outline for the content team and schedule stakeholder review
```

Reports resembling the above are saved under `reports/` for every completed task.

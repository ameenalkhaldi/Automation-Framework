"""Skill registry inspired by Microsoft AutoGen's tool calling pattern."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List


@dataclass
class Skill:
    """Represents a callable tool that agents can invoke."""

    name: str
    description: str
    function: Callable[..., Any]
    signature: str

    def execute(self, **kwargs: Any) -> str:
        result = self.function(**kwargs)
        return result if isinstance(result, str) else repr(result)


class SkillRegistry:
    """Stores and executes skills that agents can call during workflows."""

    def __init__(self) -> None:
        self._skills: Dict[str, Skill] = {}

    def register(self, name: str, function: Callable[..., Any], description: str) -> None:
        if name in self._skills:
            raise ValueError(f"A skill named '{name}' is already registered.")
        signature = str(inspect.signature(function))
        self._skills[name] = Skill(
            name=name,
            description=description,
            function=function,
            signature=signature,
        )

    def execute(self, name: str, **kwargs: Any) -> str:
        if name not in self._skills:
            raise KeyError(f"No skill registered with name '{name}'.")
        skill = self._skills[name]
        return skill.execute(**kwargs)

    def list_skills(self) -> Iterable[Skill]:
        return self._skills.values()

    def to_prompt_fragment(self) -> str:
        if not self._skills:
            return "No custom skills are registered."
        lines: List[str] = []
        for skill in self._skills.values():
            lines.append(
                f"- {skill.name}{skill.signature}: {skill.description}"
            )
        return "\n".join(lines)

    def __len__(self) -> int:  # pragma: no cover - trivial helper
        return len(self._skills)

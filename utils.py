"""Utility helpers for the automation framework."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from colorama import Fore, Style, init

init(autoreset=True)

# Rotating color palette for agents so new personas automatically get
# deterministic but distinct colours in the terminal output.
_AGENT_PALETTE = [
    Fore.CYAN,
    Fore.GREEN,
    Fore.MAGENTA,
    Fore.YELLOW,
    Fore.BLUE,
    Fore.LIGHTCYAN_EX,
    Fore.LIGHTGREEN_EX,
    Fore.LIGHTMAGENTA_EX,
]
_AGENT_COLOR_CACHE: Dict[str, str] = {}


def _colour_for_agent(agent_name: str) -> str:
    if agent_name not in _AGENT_COLOR_CACHE:
        index = len(_AGENT_COLOR_CACHE) % len(_AGENT_PALETTE)
        _AGENT_COLOR_CACHE[agent_name] = _AGENT_PALETTE[index]
    return _AGENT_COLOR_CACHE[agent_name]


def print_agent_output(agent_name: str, text: Optional[str], log_file_path: Optional[str]) -> None:
    """Pretty print ``text`` for ``agent_name`` and persist it to the log."""

    colour = _colour_for_agent(agent_name)
    print(f"{colour}{agent_name}:{Style.RESET_ALL}")

    if text:
        parsed_text: Any
        try:
            parsed_text = json.loads(text)
        except json.JSONDecodeError:
            parsed_text = None

        if isinstance(parsed_text, dict):
            for key, value in parsed_text.items():
                formatted_value = value
                if isinstance(value, bool):
                    formatted_value = "Yes" if value else "No"
                elif isinstance(value, list):
                    formatted_value = ", ".join(str(item) for item in value)
                print(f"{colour}{key}: {formatted_value}{Style.RESET_ALL}")
        else:
            print(f"{colour}{text}{Style.RESET_ALL}")

    print()

    if not log_file_path:
        return

    log_path = Path(log_file_path)
    log_data: Dict[str, Any]

    if log_path.exists():
        log_data = json.loads(log_path.read_text())
    else:
        log_data = {"created_at": datetime.utcnow().isoformat(), "output": []}

    log_data.setdefault("output", []).append({"agent_name": agent_name, "text": text})
    log_path.write_text(json.dumps(log_data, indent=2))


def initialise_log_file(run_name: str) -> str:
    """Create a new log file for ``run_name`` and return its path."""

    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    log_file = logs_dir / f"{run_name}-{timestamp}.json"
    log_file.write_text(json.dumps({"run_name": run_name, "output": []}, indent=2))
    return str(log_file)

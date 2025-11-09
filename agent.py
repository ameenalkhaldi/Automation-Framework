"""Core abstractions for language model driven agents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from openai import OpenAI

from utils import print_agent_output


@dataclass
class Message:
    """Represents a single message exchanged during a conversation."""

    role: str
    content: str


class Agent:
    """Base class for building conversational LLM agents.

    The class wraps the OpenAI client and manages lightweight conversational
    state so derived agents can focus on task-specific prompts. Each agent can
    maintain multiple concurrent conversations that are keyed by a
    ``conversation_id``. Conversations automatically include the agent's system
    prompt as the leading message to keep interactions consistent.
    """

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ) -> None:
        self.name = name
        self.role = role
        self.system_prompt = system_prompt.strip()
        self.model = model
        self.client: Optional[OpenAI] = OpenAI(api_key=api_key) if api_key else None
        self.chat_histories: Dict[str, List[Message]] = {}

    # ------------------------------------------------------------------
    # Conversation management helpers
    # ------------------------------------------------------------------
    def _ensure_client(self) -> OpenAI:
        if not self.client:
            raise RuntimeError(
                "OpenAI client is not configured. Set the OPENAI_API_KEY environment "
                "variable or provide an explicit api_key when instantiating the agent."
            )
        return self.client

    def get_chat_history(self, conversation_id: str) -> List[Message]:
        """Return the chat history for ``conversation_id``.

        A new conversation is automatically seeded with the system prompt so the
        LLM always receives the full behavioural context.
        """

        if conversation_id not in self.chat_histories:
            self.chat_histories[conversation_id] = [
                Message(role="system", content=self.system_prompt)
            ]
        return self.chat_histories[conversation_id]

    def append_to_history(
        self,
        conversation_id: str,
        role: str,
        content: str,
    ) -> None:
        history = self.get_chat_history(conversation_id)
        history.append(Message(role=role, content=content))

    def reset_conversation(self, conversation_id: Optional[str] = None) -> None:
        """Reset one conversation or all stored conversations."""

        if conversation_id is None:
            self.chat_histories.clear()
            return

        self.chat_histories.pop(conversation_id, None)

    # ------------------------------------------------------------------
    # LLM interaction helpers
    # ------------------------------------------------------------------
    def _serialize_history(self, history: Iterable[Message]) -> List[Dict[str, str]]:
        return [{"role": message.role, "content": message.content} for message in history]

    def generate_response(
        self,
        conversation_id: str,
        user_message: str,
        *,
        response_format: Optional[Dict[str, Any]] = None,
        temperature: float = 0.2,
        max_output_tokens: Optional[int] = None,
    ) -> str:
        """Send ``user_message`` to the configured model and return the response."""

        client = self._ensure_client()
        history = self.get_chat_history(conversation_id)
        self.append_to_history(conversation_id, "user", user_message)

        request_payload: Dict[str, Any] = {
            "model": self.model,
            "messages": self._serialize_history(history),
            "temperature": temperature,
        }

        if response_format:
            request_payload["response_format"] = response_format
        if max_output_tokens is not None:
            request_payload["max_output_tokens"] = max_output_tokens

        completion = client.chat.completions.create(**request_payload)
        assistant_response = completion.choices[0].message.content
        self.append_to_history(conversation_id, "assistant", assistant_response)
        return assistant_response

    # ------------------------------------------------------------------
    # Presentation helpers
    # ------------------------------------------------------------------
    def log(self, text: Optional[str], log_file_path: Optional[str]) -> None:
        """Pretty-print and optionally persist the agent output."""

        print_agent_output(self.name, text=text, log_file_path=log_file_path)


__all__ = ["Agent", "Message"]

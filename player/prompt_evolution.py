"""Prompt evolution module for post-game self-improvement.

After a game session, uses the LLM to analyze what worked and what didn't,
then generates an improved system prompt for the next session.
"""

import json
import os
from datetime import datetime, timezone

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from config import MAX_SYSTEM_PROMPT_LENGTH


# File to store prompt evolution history
PROMPT_HISTORY_FILE = "prompt_history.json"


EVOLUTION_SYSTEM_PROMPT = """You are an AI coach analyzing a soccer agent's performance.
You will receive:
1. The agent's current strategy prompt
2. A session summary with statistics (goals, rewards, outcomes)

Your job is to REWRITE the strategy prompt to improve performance based on what worked and what didn't.

RULES:
- Keep the output under 1800 characters (leave room for formatting)
- Maintain the same OUTPUT FORMAT requirement (dx, dy, kick)
- Keep SHOOTING RULES intact (only kick when behind ball + in range)
- Focus on tactical improvements based on the data
- If goals were scored, reinforce what led to them
- If the agent kept moving away from the ball, emphasize chase behavior
- If kicks failed, emphasize positioning before kicking
- Be specific and actionable, not vague
- Return ONLY the new prompt text, no explanation or commentary
"""


def evolve_prompt(current_prompt: str, session_summary: dict, model: str = "meta/llama-3.1-8b-instruct") -> str:
    """Use the LLM to generate an improved system prompt based on session performance.

    Args:
        current_prompt: The system prompt used during the session.
        session_summary: Stats dict from AgentMemory.get_session_summary().
        model: The NVIDIA NIM model to use for evolution.

    Returns:
        An improved system prompt string.
    """
    summary_text = json.dumps(session_summary, indent=2)

    user_message = f"""CURRENT STRATEGY PROMPT:
---
{current_prompt}
---

SESSION PERFORMANCE SUMMARY:
---
{summary_text}
---

Based on this performance data, write an improved strategy prompt that addresses weaknesses and reinforces strengths. Return ONLY the new prompt text."""

    messages = [
        SystemMessage(content=EVOLUTION_SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]

    try:
        llm = ChatNVIDIA(model=model)
        response = llm.invoke(messages)
        new_prompt = response.content.strip()

        # Safety: ensure it doesn't exceed max length
        if len(new_prompt) > MAX_SYSTEM_PROMPT_LENGTH:
            new_prompt = new_prompt[:MAX_SYSTEM_PROMPT_LENGTH]

        # Safety: if the response is too short or nonsensical, keep the original
        if len(new_prompt) < 50:
            return current_prompt

        return new_prompt

    except Exception:
        # If evolution fails, return the original prompt unchanged
        return current_prompt


def save_prompt_history(
    old_prompt: str,
    new_prompt: str,
    session_summary: dict,
    filepath: str = PROMPT_HISTORY_FILE,
) -> None:
    """Save the prompt evolution to a history file for tracking improvements.

    Args:
        old_prompt: The previous system prompt.
        new_prompt: The evolved system prompt.
        session_summary: The performance stats that drove the evolution.
        filepath: Path to the history JSON file.
    """
    history = []

    # Load existing history
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                history = json.load(f)
        except (json.JSONDecodeError, IOError):
            history = []

    # Append new entry
    entry = {
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
        "old_prompt": old_prompt,
        "new_prompt": new_prompt,
        "session_summary": session_summary,
    }
    history.append(entry)

    # Keep last 20 evolutions
    if len(history) > 20:
        history = history[-20:]

    with open(filepath, "w") as f:
        json.dump(history, f, indent=2)


def load_latest_evolved_prompt(filepath: str = PROMPT_HISTORY_FILE) -> str | None:
    """Load the most recently evolved prompt from history.

    Returns:
        The latest evolved prompt string, or None if no history exists.
    """
    if not os.path.exists(filepath):
        return None

    try:
        with open(filepath, "r") as f:
            history = json.load(f)
        if history:
            return history[-1]["new_prompt"]
    except (json.JSONDecodeError, IOError, KeyError):
        pass

    return None

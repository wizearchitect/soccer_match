"""In-context memory module for the agent.

Maintains a rolling buffer of recent iterations (state -> action -> outcome)
that gets injected into the LLM prompt, giving the agent short-term memory
of what it did and what happened as a result.
"""

import json
import os
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional

from config import ActionModel


# How many past iterations to keep in the rolling buffer
MEMORY_BUFFER_SIZE = 8

# File for persisting memory across sessions
MEMORY_FILE = "memory_log.json"


@dataclass
class MemoryEntry:
    """One remembered iteration: what I saw, what I did, what happened."""

    # Compact state snapshot
    ball_distance: float
    ball_direction_dx: float
    ball_direction_dy: float
    in_kick_range: bool
    is_behind_ball: bool
    my_x: float
    my_y: float

    # What the agent decided
    action_dx: float
    action_dy: float
    action_kick: bool

    # Outcome (computed next iteration by comparing states)
    outcome: str = ""  # e.g., "ball moved toward goal", "ball moved away", "scored", "lost possession"
    reward: float = 0.0

    timestamp: str = ""


class AgentMemory:
    """Rolling memory buffer with outcome evaluation and persistence.

    Tracks the last N iterations and computes simple reward signals
    by comparing consecutive game states.
    """

    def __init__(self, team: str, position: str, buffer_size: int = MEMORY_BUFFER_SIZE):
        self.team = team
        self.position = position
        self.buffer: deque[MemoryEntry] = deque(maxlen=buffer_size)
        self.prev_game_state: Optional[dict] = None
        self.total_reward: float = 0.0
        self.iteration_count: int = 0
        self.goals_scored: int = 0

    def record(self, spatial_data: dict, action: ActionModel, game_state: dict) -> None:
        """Record the current iteration and evaluate the previous one's outcome.

        Args:
            spatial_data: The spatial analysis dict from spatial.py
            action: The action the agent chose
            game_state: The raw game state from the server
        """
        # Evaluate outcome of the PREVIOUS action by comparing states
        if self.prev_game_state is not None and len(self.buffer) > 0:
            outcome, reward = self._evaluate_outcome(self.prev_game_state, game_state)
            self.buffer[-1].outcome = outcome
            self.buffer[-1].reward = reward
            self.total_reward += reward

        # Record current iteration
        entry = MemoryEntry(
            ball_distance=spatial_data.get("ball_distance", 0),
            ball_direction_dx=spatial_data.get("ball_direction", {}).get("dx", 0),
            ball_direction_dy=spatial_data.get("ball_direction", {}).get("dy", 0),
            in_kick_range=spatial_data.get("in_kick_range", False),
            is_behind_ball=spatial_data.get("is_behind_ball", False),
            my_x=spatial_data.get("player_position", {}).get("x", 0),
            my_y=spatial_data.get("player_position", {}).get("y", 0),
            action_dx=action.dx,
            action_dy=action.dy,
            action_kick=action.kick,
            timestamp=datetime.now(timezone.utc).astimezone().strftime("%H:%M:%S"),
        )
        self.buffer.append(entry)
        self.prev_game_state = game_state
        self.iteration_count += 1

    def _evaluate_outcome(self, prev_state: dict, curr_state: dict) -> tuple[str, float]:
        """Compare two consecutive game states to determine what happened.

        Returns:
            A tuple of (outcome_description, reward_value)
        """
        prev_ball = prev_state.get("ball", {"x": 600, "y": 400})
        curr_ball = curr_state.get("ball", {"x": 600, "y": 400})

        prev_score = prev_state.get("score", {"red": 0, "blue": 0})
        curr_score = curr_state.get("score", {"red": 0, "blue": 0})

        # Check if we scored
        my_score_key = self.team.lower()
        if curr_score.get(my_score_key, 0) > prev_score.get(my_score_key, 0):
            self.goals_scored += 1
            return "GOAL SCORED!", 10.0

        # Check if opponent scored
        opp_key = "blue" if self.team == "Red" else "red"
        if curr_score.get(opp_key, 0) > prev_score.get(opp_key, 0):
            return "Opponent scored", -5.0

        # Check ball movement relative to opponent's goal
        if self.team == "Red":
            # Red attacks right (x=1200)
            target_x = 1200.0
        else:
            # Blue attacks left (x=0)
            target_x = 0.0

        prev_dist_to_goal = abs(prev_ball["x"] - target_x)
        curr_dist_to_goal = abs(curr_ball["x"] - target_x)

        if curr_dist_to_goal < prev_dist_to_goal - 20:
            return "Ball moved toward opponent goal", 2.0
        elif curr_dist_to_goal > prev_dist_to_goal + 20:
            return "Ball moved away from opponent goal", -1.0

        # Check if we got closer to ball
        player_key = f"{self.team}_{self.position}"
        prev_players = prev_state.get("players", {})
        curr_players = curr_state.get("players", {})

        if player_key in prev_players and player_key in curr_players:
            prev_px = prev_players[player_key]["x"]
            prev_py = prev_players[player_key]["y"]
            curr_px = curr_players[player_key]["x"]
            curr_py = curr_players[player_key]["y"]

            import math
            prev_ball_dist = math.sqrt((prev_px - prev_ball["x"])**2 + (prev_py - prev_ball["y"])**2)
            curr_ball_dist = math.sqrt((curr_px - curr_ball["x"])**2 + (curr_py - curr_ball["y"])**2)

            if curr_ball_dist < prev_ball_dist - 10:
                return "Got closer to ball", 0.5
            elif curr_ball_dist > prev_ball_dist + 10:
                return "Moved away from ball", -0.5

        return "Neutral movement", 0.0

    def format_for_prompt(self) -> str:
        """Format the memory buffer as text to inject into the LLM prompt.

        Returns a concise summary of recent actions and their outcomes.
        """
        if not self.buffer:
            return ""

        lines = [
            "--- RECENT MEMORY (last actions & outcomes) ---",
            f"Total iterations: {self.iteration_count} | Cumulative reward: {self.total_reward:.1f} | Goals: {self.goals_scored}",
            "",
        ]

        for i, entry in enumerate(self.buffer):
            kick_str = "KICK" if entry.action_kick else "move"
            outcome_str = f" → {entry.outcome}" if entry.outcome else " → (pending)"
            reward_str = f" [{'+' if entry.reward >= 0 else ''}{entry.reward:.1f}]" if entry.outcome else ""
            lines.append(
                f"  [{entry.timestamp}] dx={entry.action_dx:+.2f} dy={entry.action_dy:+.2f} {kick_str}"
                f" | ball@{entry.ball_distance:.0f}px behind={entry.is_behind_ball}"
                f"{outcome_str}{reward_str}"
            )

        # Add a learning hint based on recent performance
        recent_rewards = [e.reward for e in self.buffer if e.outcome]
        if recent_rewards:
            avg = sum(recent_rewards) / len(recent_rewards)
            if avg > 1.0:
                lines.append("\nPATTERN: Recent actions are working well. Continue current strategy.")
            elif avg < -1.0:
                lines.append("\nPATTERN: Recent actions are not effective. Try a different approach.")
            else:
                lines.append("\nPATTERN: Mixed results. Look for opportunities to get behind the ball.")

        return "\n".join(lines)

    def get_session_summary(self) -> dict:
        """Get a summary of the entire session for prompt evolution.

        Returns:
            A dict with session statistics and action patterns.
        """
        if not self.buffer:
            return {"iterations": 0, "reward": 0, "goals": 0, "summary": "No data"}

        outcomes = [e.outcome for e in self.buffer if e.outcome]
        kicks = [e for e in self.buffer if e.action_kick]
        successful_kicks = [e for e in kicks if "goal" in e.outcome.lower() or "toward" in e.outcome.lower()]

        return {
            "iterations": self.iteration_count,
            "total_reward": self.total_reward,
            "goals_scored": self.goals_scored,
            "kick_attempts": len(kicks),
            "successful_kicks": len(successful_kicks),
            "common_outcomes": self._count_outcomes(outcomes),
            "avg_reward": self.total_reward / max(self.iteration_count, 1),
        }

    def _count_outcomes(self, outcomes: list[str]) -> dict[str, int]:
        """Count occurrences of each outcome type."""
        counts: dict[str, int] = {}
        for o in outcomes:
            counts[o] = counts.get(o, 0) + 1
        return counts

    def save_to_file(self, filepath: str = MEMORY_FILE) -> None:
        """Persist the memory buffer to a JSON file for post-game analysis."""
        data = {
            "team": self.team,
            "position": self.position,
            "iteration_count": self.iteration_count,
            "total_reward": self.total_reward,
            "goals_scored": self.goals_scored,
            "entries": [asdict(e) for e in self.buffer],
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, filepath: str = MEMORY_FILE) -> bool:
        """Load previous session memory if available. Returns True if loaded."""
        if not os.path.exists(filepath):
            return False
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            # Restore stats
            self.iteration_count = data.get("iteration_count", 0)
            self.total_reward = data.get("total_reward", 0.0)
            self.goals_scored = data.get("goals_scored", 0)
            return True
        except (json.JSONDecodeError, KeyError):
            return False
